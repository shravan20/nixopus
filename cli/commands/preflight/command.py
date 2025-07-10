import typer
from .messages import running_preflight_checks
from .port import PortConfig, PortCheckResult    
from utils.logger import Logger

preflight_app = typer.Typer(no_args_is_help=False)

@preflight_app.callback(invoke_without_command=True)
def preflight_callback(ctx: typer.Context):
    """Preflight checks for system compatibility"""
    if ctx.invoked_subcommand is None:
        ctx.invoke(check)

@preflight_app.command()
def check(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    output: str = typer.Option("text", "--output", "-o", help="Output format, text,json"),
):
    """Run all preflight checks"""
    logger = Logger(verbose=verbose)
    logger.info(PortConfig.format(running_preflight_checks, output))

@preflight_app.command()
def ports(
    ports: list[int] = typer.Argument(..., help="The list of ports to check"),
    host: str = typer.Option("localhost", "--host", "-h", help="The host to check"),
    timeout: int = typer.Option(1, "--timeout", "-t", help="The timeout in seconds for each port check"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    output: str = typer.Option("text", "--output", "-o", help="Output format, text, json"),
) -> list[PortCheckResult]:
    """Check if list of ports are available on a host"""
    try:
        logger = Logger(verbose=verbose)
        logger.debug(f"Checking ports: {ports}")
        config = PortConfig(ports=ports, host=host, timeout=timeout, verbose=verbose)
        results = PortConfig.check_ports(config)
        logger.success(PortConfig.format(results, output))
        return results
    except Exception as e:
        logger.error(f"Error checking ports: {e}")
        raise typer.Exit(1)
