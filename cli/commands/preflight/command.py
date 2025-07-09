import typer
from .messages import running_preflight_checks

preflight_app = typer.Typer()

@preflight_app.command()
def check():    
    """Run all preflight checks"""
    typer.echo(running_preflight_checks)
