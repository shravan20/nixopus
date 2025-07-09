import typer
from core.version.version import display_version
from utils.message import application_version_help

version_app = typer.Typer(
    help=application_version_help,
    invoke_without_command=True
)

@version_app.callback()
def version_callback(ctx: typer.Context):
    """Show version information (default)"""
    if ctx.invoked_subcommand is None:
        display_version()

def main_version_callback(value: bool):
    if value:
        display_version()
        raise typer.Exit()