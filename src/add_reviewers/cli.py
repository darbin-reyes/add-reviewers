"""CLI implementation for add-reviewers."""

import click
from yaspin import yaspin
from yaspin.spinners import Spinners
from add_reviewers.x import (
    fire, red, yellow, green, gh_installed, jq_installed, run, random_verb,
    validate_pr_number, parse_repo_url, query_github_graphql
)
from add_reviewers._version import __version__


# accept -h and --help as help options, not just --help.
CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])

@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(version=__version__, prog_name="add-reviewers",message="%(prog)s version %(version)s")
def main():
    """CLI that automatically adds pull request reviewers based on past approvals."""
    pass

def _diff(remote: str, pr: int) -> list[str]:
    """See diff()."""

    gh_installed()

    # Build the gh pr diff command
    cmd: list[str] = ["gh", "pr", "diff", str(pr), "--name-only", "--repo", remote]


    stdout: str = run(cmd)

    pr_url = f"{remote}/pull/{pr}"
    m = green(f"\n\nFILES MODIFIED BY PR: {pr_url}")
    click.echo(m)
    click.echo(stdout)

    files: list[str] = stdout.strip().split("\n")

    click.echo(f"{len(files)} files touched.")

    return files



@main.command()
@click.option('--remote', type=str, required=True, help='URL of repository remote.')
@click.option('--pr', type=int, required=True, callback=validate_pr_number, help='Pull request number.')
def diff(remote: str, pr: int):
    """List files modified by a given pull request."""

    with yaspin(Spinners.dots2, text=random_verb()) as spinner:
        _diff(remote, pr)
        spinner.ok("✓")

def __list(remote: str, count: int) -> list[dict[str, any]]:
    """See _list()."""
    if count <= 0:
        raise click.ClickException(red(f"{count} is invalid. Count must be positive."))

    owner, repo = parse_repo_url(remote)

    # GraphQL query to fetch merged PRs with files and reviews using pagination
    # direction: DESC sorts the pull requests in descending order (newest first) based on the UPDATED_AT field.
    # The 100 in files(first: 100) and reviews(first: 100) limits how many files and reviews are fetched for each pull request.
    query = """
    query($owner: String!, $repo: String!, $limit: Int!, $after: String) {
        repository(owner: $owner, name: $repo) {
        pullRequests(first: $limit, states: MERGED, orderBy: {field: UPDATED_AT, direction: DESC}, after: $after) {
            pageInfo {
            hasNextPage
            endCursor
            }
            nodes {
            number
            files(first: 100) {
                nodes {
                path
                }
            }
            reviews(first: 100, states: APPROVED) {
                nodes {
                author {
                    login
                }
                }
            }
            }
        }
        }
    }
    """

    # Fetch up to 200 PRs using pagination (100 per query)
    all_pull_requests = []
    cursor = None
    target_count = (count // 100 + 1) * 100 # min(count, 200)  # Cap at 200 for this implementation
    np = target_count // 100

    for page in range(np):  # Maximum 2 pages to get 200 PRs
        remaining = target_count - len(all_pull_requests)
        if remaining <= 0:
            break

        page_size = min(100, remaining)

        variables = {
            'owner': owner,
            'repo': repo,
            'limit': page_size,
            'after': cursor
        }

        data = query_github_graphql(query, variables)

        pr_data = data.get('data', {}).get('repository', {}).get('pullRequests', {})
        page_prs = pr_data.get('nodes', [])
        page_info = pr_data.get('pageInfo', {})

        all_pull_requests.extend(page_prs)

        # Check if there are more pages and update cursor
        if not page_info.get('hasNextPage', False):
            break
        cursor = page_info.get('endCursor')

    # Extract and display PRs
    pull_requests = all_pull_requests

    if not pull_requests:
        click.echo(yellow("No merged pull requests found."))
        return []

    click.echo(green(f"\n{len(pull_requests)} most recent merged pull requests in {remote}:\n"))

    ret = []
    for pr in pull_requests:
        number = pr['number']
        files = [f['path'] for f in pr.get('files', {}).get('nodes', [])]
        reviews = [r['author']['login'] for r in pr.get('reviews', {}).get('nodes', []) if r.get('author')]

        click.echo(f"PR #{number}")
        click.echo(f"  Files ({len(files)}): {', '.join(files) if files else 'None'}")
        click.echo(f"  Approved by ({len(reviews)}): {', '.join(reviews) if reviews else 'None'}")
        click.echo()
        ret.append({"number": number, "files" : files, "approvers": reviews})

    return ret

@main.command("list-merged")
@click.option('--remote', type=str, required=True, help='URL of repository remote.')
@click.option('--count', type=int, default=100, help='Number of pull requests to list.')
def _list(remote: str, count: int):
    """List the most recent merged pull requests in repository specified by remote."""

    with yaspin(Spinners.dots2, text=random_verb()) as spinner:
        __list(remote, count)
        spinner.ok("✓")

@main.command()
@click.option('--remote', type=str, required=True, help='URL of repository remote.')
@click.option('--pr', type=int, required=True, callback=validate_pr_number, help='Open pull request number.')
def test(remote: str, pr: int):

    with yaspin(Spinners.dots2, text=random_verb()) as spinner:
        open_pr_files: list[str] = _diff(remote, pr)
        spinner.ok("✓")

    with yaspin(Spinners.dots2, text=random_verb()) as spinner:
        merged_prs = __list(remote, 1000)
        spinner.ok("✓")

    auto_reviewers = set()
    for mpr in merged_prs:
        # Add approvers if merged PR touched any file that the open PR touches
        if any(f in mpr["files"] for f in open_pr_files):
            auto_reviewers.update(mpr["approvers"])

    click.echo(f"{len(auto_reviewers)} approvers found. They will be added as reviewers to PR # {pr}.")
    click.echo(green(f"{auto_reviewers}"))