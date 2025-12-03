# Design

Given a PR, inspect the list of modified files (use gh command for this), for each modified file, use the file audit gh command to get a list of all users who have approved changes to that file, aggregate the list of users, add those users as reviewers. Skip adding reviewers who are already listed in the PR. Also, Automatically add CoPilot as a reviewer.

# list files touched by PR

gh pr view 11 --json files --jq ".files[].path"


gh pr diff 11 --name-only

# list PRs numbers that touched a given file

gh pr list --state merged --limit 100 --json number,files | jq --arg filepath 'src/pysvtools/irecipe/commands/rgit.py' '.[] | select(.files[]? | select(.path == $filepath)) | .number'

In powershell, single quotes is required because of $.

gh pr list --state merged --limit 100 --json number,files | jq --arg filepath "BoardPkgBuild.py" '.[] | select(.files[]? | select(.path == $filepath)) | .number'

Paths are returned relative to the repo root even if command is run elsewhere down the tree.

# Get PRs that touched a specific file and show approvers

gh pr list --state merged --limit 100 --json number,files,reviews | jq --arg filepath "src/pysvtools/irecipe/commands/rgit.py" ' .[] | select(.files[]? | select(.path == $filepath)) | { pr: .number,approvers: [.review []? | select(.state == \"APPROVED\") | .author.login] | unique } | select(.approvers | length > 0)'


# list users who approved PR 9

gh pr view 9 --json reviews | jq '.reviews[] | select(.state == \"APPROVED\") | .author.login '

# 12/2/2025

- Problem: Given an open pull request and the list of modified files, using graphql github API we can iterate over all merged pull requests that modified the same files.
    - (Optionally: Open pull requests as well, but excluding this pull request).
    - Given this list of merged pull requests, we can output the github username and email of the approvers.
    - Finally, we use the github API to add those usernames as reviewers.
    - Why this doesn't work: the API is too slow (hours, possibly more than 24hrs) to be run in real time either as a directly run script, as git hook, or github workflow.
    - Failed solution: give up on using the merged github API pull requests as a data source, use git blame instead, its a single git command per modified file that is fast and does not involve network requests.
    - Problem: git blame provides emails but  does not provide github username information and adding reviewers is only supported by username.
    - New solution: Download the pull request information upfront and save it as a JSON file. This needs to be implemented, if supported, in a way that can resume download progress if the API connection fails because these failures are very frequent with large data transfers. Once that is downloaded, we can map blame emails to usernames and use both blame and past pull request approvers as reviewers to an open pull request.


        - Concern: implementing this as a git hook might require that users carry this data base as a very large file. In this case a GitHub workflow may be preferable.