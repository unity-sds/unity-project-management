import requests
import time
import random
import logging
import base64
import re

logging.basicConfig(level=logging.INFO)

org_name = "unity-sds"
org_url = f"https://api.github.com/orgs/{org_name}/repos"
headers = {'Authorization': 'token TOKEN_GOES_HERE'}
org_repos = requests.get(org_url, headers=headers).json()

table_header = "| Project | Repository | [Issue Templates](https://nasa-ammos.github.io/slim/docs/guides/governance/contributions/issue-templates/) | [PR Templates](https://nasa-ammos.github.io/slim/docs/guides/governance/contributions/change-request-templates/) | [Code of Conduct](https://nasa-ammos.github.io/slim/docs/guides/governance/contributions/code-of-conduct/) | [Contributing Guide](https://nasa-ammos.github.io/slim/docs/guides/governance/contributions/contributing-guide/) | LICENSE | [README](https://nasa-ammos.github.io/slim/docs/guides/documentation/readme/) | [Change Log](https://nasa-ammos.github.io/slim/docs/guides/documentation/change-log/) | Dev/User Documentation |\n"
table_header += "|---|---|---|---|---|---|---|---|---|---|\n"

rows = []

for index, repo in enumerate(org_repos):
    repo_name = repo['name']
    repo_url = repo['html_url']

    issue_template_url = f"https://api.github.com/repos/{org_name}/{repo_name}/contents/.github/ISSUE_TEMPLATE"
    pr_template_url = f"https://api.github.com/repos/{org_name}/{repo_name}/contents/.github/PULL_REQUEST_TEMPLATE.md"
    contents_url = f"https://api.github.com/repos/{org_name}/{repo_name}/contents"
    readme_url = f"https://api.github.com/repos/{org_name}/{repo_name}/contents/README.md"

    jitter = random.uniform(0.5, 1.5)
    time.sleep(jitter)  # jittering

    issue_templates_response = requests.get(issue_template_url, headers=headers)
    pr_template_response = requests.get(pr_template_url, headers=headers)
    contents_response = requests.get(contents_url, headers=headers)
    readme_response = requests.get(readme_url, headers=headers)

    issue_templates = issue_templates_response.json() if issue_templates_response.status_code == 200 else []
    pr_templates = '✅' if pr_template_response.status_code == 200 else '❌'
    contents = contents_response.json() if contents_response.status_code == 200 else []
    readme = base64.b64decode(readme_response.json()['content']).decode() if readme_response.status_code == 200 else ""

    issue_template_files = [file['name'] for file in issue_templates]
    files = [file['name'] for file in contents]

    issue_templates = '✅' if 'bug_report.md' in issue_template_files and 'feature_request.md' in issue_template_files else '❌'
    code_of_conduct = '✅' if 'CODE_OF_CONDUCT.md' in files else '❌'
    contributing_guide = '✅' if 'CONTRIBUTING.md' in files else '❌'
    license = '✅' if 'LICENSE' in files else '❌'
    change_log = '✅' if 'CHANGELOG.md' in files else '❌'

    required_sections = ["Features", "Contents", "Quick Start", "Changelog", "Frequently Asked Questions (FAQ)", "Contributing", "License", "Support"]
    readme_sections = re.findall(r'^#+\s*(.*)$', readme, re.MULTILINE)
    readme = '✅' if all(section in readme_sections for section in required_sections) else '❌'

    docs_link = '✅' if re.search(r'\[Docs\w*\]\(.*\)', readme, re.IGNORECASE) else '❌'

    row = f"| [{org_name}](https://github.com/{org_name}) | [{repo_name}]({repo_url}) | {issue_templates} | {pr_templates} | {code_of_conduct} | {contributing_guide} | {license} | {readme} | {change_log} | {docs_link} |"
    rows.append((row.count('✅'), row))

    logging.info(row) # print the markdown rendering of the row

# Sort rows by the number of '✅' values and add them to the table
rows.sort(reverse=True)
table = table_header + '\n'.join(row for _, row in rows)

print("\n")
print(table)
