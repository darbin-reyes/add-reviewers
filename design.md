# Design

Given a PR, inspect the list of modified files (use gh command for this), for each modified file, use the file audit gh command to get a list of all users who have approved changes to that file, aggregate the list of users, add those users as reviewers. Skip adding reviewers who are already listed in the PR. Also, Automatically add CoPilot as a reviewer.

# list files touched by PR
gh pr view 11 --json files --jq ".files[].path"


gh pr diff 11 --name-only

# list PRs numbers that touched a given file

gh pr list --state merged --limit 100 --json number,files | jq --arg filepath "src/pysvtools/irecipe/commands/rgit.py" ".[] | select(.files[]? | select(.path == $filepath)) | .number"

# Get PRs that touched a specific file and show approvers
gh pr list --state merged --limit 100 --json number,files,reviews | jq --arg filepath "src/pysvtools/irecipe/commands/rgit.py" ' .[] | select(.files[]? | select(.path == $filepath)) | { pr: .number,approvers: [.review []? | select(.state == \"APPROVED\") | .author.login] | unique } | select(.approvers | length > 0)'


# list users who approved PR 9
gh pr view 9 --json reviews | jq '.reviews[] | select(.state == \"APPROVED\") | .author.login '


