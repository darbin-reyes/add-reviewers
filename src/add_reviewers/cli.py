"""CLI implementation for add-reviewers."""

import subprocess
import click
from yaspin import yaspin
from yaspin.spinners import Spinners
from add_reviewers.x import fire, red, yellow, green
from add_reviewers._version import __version__



# accept -h and --help as help options, not just --help.
CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])

@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(version=__version__, prog_name="add-reviewers",message="%(prog)s version %(version)s")
def main():
    """CLI that automatically adds pull request reviewers based on past approvals."""
    pass


@main.command()
@click.option('--remote', type=str, help='URL of repository remote. Inferred from CWD if not specified.')
@click.option('--pr', type=int, required=True, help='Pull request number.')
@yaspin(Spinners.dots2, text="Fooing ")
def diff(remote, pr):
    """List files modified by a given pull request."""

    # Build the gh pr diff command
    cmd = ["gh", "pr", "diff", str(pr), "--name-only"]

    if remote:
        cmd.extend(["--repo", remote])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        m = green("\n" + result.stdout)
        click.echo(m)
    except subprocess.CalledProcessError as e:
        m = red(f"Error running gh command: {e.stderr}")
        raise click.ClickException(m) from e
    except FileNotFoundError as e:
        m = red("Error: 'gh' command not found. Please install GitHub CLI.")
        raise click.ClickException(m) from e
    except Exception as e:
        m = red(f"Exception: {e}.")
        raise click.ClickException(m) from e


if __name__ == "__main__":
    main()
