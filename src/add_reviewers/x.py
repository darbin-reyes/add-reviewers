import click
from emoji import emojize

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

################################################################################