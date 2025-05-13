#!/usr/bin/env python
# coding: utf-8

# In[19]:


import boto3
from datetime import datetime, timedelta
import time


client = boto3.client('ec2')

# In[20]:


instances = client.describe_instances()
instances['Reservations']

yesterday = (datetime.now() - timedelta(days=2)).timestamp()

reservations = instances['Reservations']

instances_over_48hours_old = list(
    filter(lambda instance: instance['Instances'][0]['LaunchTime'].timestamp() < yesterday, reservations)
)

# In[21]:


save_list = []
kill_list = []

for ins in instances_over_48hours_old:
    instance_name = None
    instance_venue = None
    instance_project = None

    for k in ins['Instances'][0]['Tags']:
        if k['Key'] == 'Name':
            instance_name = k['Value']
        if k['Key'] == 'Venue':
            instance_venue = k['Value']
        if k['Key'] == 'Proj':
            instance_project = k['Value']
    if instance_project in ['unity'] and instance_venue in ['venue-dev', 'dev']:
        save_list.append(ins['Instances'][0]['InstanceId'])
        print("SAVE {} - {} ({}|{})".format(ins['Instances'][0]['InstanceId'], instance_name, instance_project,
                                            instance_venue))
    elif "Management Console" in instance_name:
        save_list.append(ins['Instances'][0]['InstanceId'])
        print("SAVE {} - {} ({}|{})".format(ins['Instances'][0]['InstanceId'], instance_name, instance_project,
                                            instance_venue))
    else:
        kill_list.append(ins['Instances'][0]['InstanceId'])
        print("KILL {} - {} ({}|{})".format(ins['Instances'][0]['InstanceId'], instance_name, instance_project,
                                            instance_venue))

# In[22]:


kill_list

# In[23]:


save_list

# In[24]:


as_client = boto3.client('autoscaling')

# In[25]:


as_groups = as_client.describe_auto_scaling_instances(InstanceIds=kill_list)

# In[26]:


asgs_set = set()
asgs_instance_list = []
asgs_kill_follow_up_list = []
for as_instance in as_groups['AutoScalingInstances']:
    if "eks" in as_instance['AutoScalingGroupName']:
        asgs_set.add(as_instance['AutoScalingGroupName'])
        asgs_kill_follow_up_list.append(as_instance['InstanceId'])
    asgs_instance_list.append(as_instance['InstanceId'])

# In[27]:


asgs_set

# In[28]:


for asg_name in asgs_set:
    print("Scaling in " + asg_name)
    as_client.update_auto_scaling_group(
        AutoScalingGroupName=asg_name,
        MinSize=0,
        MaxSize=0
    )

    as_client.set_desired_capacity(
        AutoScalingGroupName=asg_name,
        DesiredCapacity=0,
        HonorCooldown=False
    )

# In[29]:


# Get the list of instances older than 48h but _not_ in the autoscaling groups
asgs_instance_list

# In[30]:


kill_instance_list_not_in_auto_scaling_group = list(set(kill_list) - set(asgs_instance_list))

# In[31]:


kill_instance_list_not_in_auto_scaling_group

# In[32]:


# Kill the autoscaling group nodes if they aren't killed yet
# This will kill any instances older than 48 hours but not in the asg_instance_lists
if len(kill_instance_list_not_in_auto_scaling_group) > 0:
    client.terminate_instances(
        InstanceIds=kill_instance_list_not_in_auto_scaling_group,
        DryRun=False
    )

# In[14]:


# Check for the existence of 'aws:eks:cluster-name' tag in the instance to see
# if this is a karpenter node managed through EKS. If so, what do we do there? 
# Could sleep a while for the karpenter nodes to die and then shut these down.
# Better steps would be to remove the airflow deployment from 

print("Sleeping 3 minutes.")
time.sleep(180)  # 3 minutes

# In[16]:


asgs_kill_follow_up_list

# In[17]:

if len(asgs_kill_follow_up_list) > 0:
    client.terminate_instances(
        InstanceIds=asgs_kill_follow_up_list,
        DryRun=False
    )

# In[ ]:
