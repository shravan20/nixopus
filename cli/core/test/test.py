import typer
import subprocess
from core.config import is_development

def test_command(target: str = typer.Argument(None, help="Test target (e.g., version)")):
    if not is_development():
        typer.echo("Test command is only available in DEVELOPMENT environment.")
        raise typer.Exit(1)
    cmd = ["venv/bin/python", "-m", "pytest"]
    if target:
        cmd.append(f"tests/{target}.py")
    typer.echo(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    raise typer.Exit(result.returncode) 