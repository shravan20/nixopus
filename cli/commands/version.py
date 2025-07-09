import typer
from core.version import display_version


def version_command():
    """Show version information"""
    display_version()


def version_callback(value: bool):
    """Callback for version options (-v, --version)"""
    if value:
        version_command()
        raise typer.Exit() 