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


# Prompt

* Initialize repository for a python CLI which uses click to implement the CLI,
use src layout, with __main__.py, cli.py. Include pyproject.toml such that the
CLI can be invoked as "add-reviewers", hatch as the build backend, dynamically
determined version via _version.py, author name Darbin Reyes, email
darbin.reyes@intel.com, description "CLI that automatically adds pull request
reviewers based on past approvals.", dependencies click, yaspin, coloroma,
emoji.
