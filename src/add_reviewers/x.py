import subprocess
import click
from emoji import emojize
import shutil
import random
import requests
import os

########################### Terminal Sugar #####################################

fire = emojize(":fire:")

def color(m: str, fg: str) -> str:
    return click.style(m, fg=fg)


def green(m: str) -> str:
    return color(m, fg="green")


def yellow(m: str) -> str:
    return color(m, fg="yellow")


def red(m: str) -> str:
    return color(m, fg="red")

def random_verb():
    """Return a random verb for spinner text."""
    verbs = [
        "Thinking",
        "Pondering",
        "Processing",
        "Computing",
        "Analyzing",
        "Examining",
        "Investigating",
        "Exploring",
        "Considering",
        "Evaluating",
        "Fetching",
        "Retrieving",
        "Gathering",
        "Collecting",
        "Working",
    ]
    return random.choice(verbs)

############################ Dependency Checks #################################

def gh_installed():
    """Check if gh command is installed.

    Returns:
        bool: True if gh command is available.

    Raises:
        click.ClickException: If gh command is not installed.
    """
    if shutil.which("gh") is None:
        raise click.ClickException("To proceed, install gh command: https://cli.github.com/")
    return True

def jq_installed():
    """Check if jq command is installed.

    Returns:
        bool: True if jq command is available.

    Raises:
        click.ClickException: If jq command is not installed.
    """
    if shutil.which("jq") is None:
        raise click.ClickException("To proceed, install jq command: https://jqlang.org/")
    return True

################################################################################

def run(cmd: list[str]) -> str:
    """Run a command, returns stdout on success, otherwise raises ClickException to terminate."""

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            return result.stdout
        else:
            m = red(f"Command returned non-zero exit code: {result.returncode}\n\n")
            m += result.stdout
            m += red(result.stderr)
            raise click.ClickException(m)
    except Exception as e:
        m = red(f"Exception running command {cmd}: {e}.")
        raise click.ClickException(m) from e


########################### Argument and option validation #####################

def validate_pr_number(ctx, param, value):
    """Validate that PR number is greater than 0."""
    if value <= 0:
        raise click.BadParameter('PR number must be greater than 0')
    return value

################################################################################

def get_github_token() -> str:
    """Get GitHub token from environment or gh CLI.

    Returns:
        str: GitHub authentication token.

    Raises:
        click.ClickException: If token cannot be obtained.
    """
    # First try GH_TOKEN or GITHUB_TOKEN environment variables
    token = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')

    if token:
        return token

    # Fall back to gh CLI
    gh_installed()
    try:
        result = subprocess.run(['gh', 'auth', 'token'], capture_output=True, text=True, check=False)
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass

    raise click.ClickException(
        "GitHub token not found. Set GH_TOKEN environment variable or authenticate with 'gh auth login'."
    )


def parse_repo_url(remote: str) -> tuple[str, str]:
    """Parse GitHub repository URL to extract owner and repo name.

    Args:
        remote: GitHub repository URL (e.g., https://github.com/owner/repo or git@github.com:owner/repo.git)

    Returns:
        tuple: (owner, repo_name)

    Raises:
        click.ClickException: If URL format is invalid.
    """
    import re

    # Match HTTPS URLs: https://github.com/owner/repo or https://github.com/owner/repo.git
    https_pattern = r'https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$'
    # Match SSH URLs: git@github.com:owner/repo.git or git@github.com:owner/repo
    ssh_pattern = r'git@github\.com:([^/]+)/(.+?)(?:\.git)?$'

    match = re.match(https_pattern, remote) or re.match(ssh_pattern, remote)

    if not match:
        raise click.ClickException(f"Invalid GitHub repository URL: {remote}")

    owner, repo = match.groups()
    return owner, repo


def query_github_graphql(query: str, variables: dict) -> dict:
    """Execute a GraphQL query against GitHub API.

    Args:
        query: GraphQL query string.
        variables: Variables for the query.

    Returns:
        dict: JSON response from GitHub API.

    Raises:
        click.ClickException: If request fails.
    """
    token = get_github_token()

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }

    payload = {
        'query': query,
        'variables': variables
    }

    try:
        response = requests.post(
            'https://api.github.com/graphql',
            json=payload,
            headers=headers,
            timeout=30
        )
        response.raise_for_status()

        data = response.json()

        if 'errors' in data:
            error_messages = [error.get('message', str(error)) for error in data['errors']]
            raise click.ClickException(f"GraphQL errors: {'; '.join(error_messages)}")

        return data

    except requests.exceptions.RequestException as e:
        raise click.ClickException(f"GitHub API request failed: {e}")

################################################################################