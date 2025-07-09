import typer
from commands.version import version_command, version_callback
from commands.test import test_command

app = typer.Typer(
    name="nixopus",
    help="NixOpus CLI - A powerful deployment and management tool",
    add_completion=False,
)

@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        help="Show version information"
    )
):
    pass

@app.command()
def version():
    """Show version information"""
    version_command()

@app.command()
def test(target: str = typer.Argument(None, help="Test target (e.g., version)")):
    """Run tests (only in DEVELOPMENT environment)"""
    test_command(target)

if __name__ == "__main__":
    app()
