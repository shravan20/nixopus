import typer
from .conflict import ConflictConfig, ConflictService
from .messages import conflict_check_help, error_checking_conflicts
from app.utils.logger import Logger

conflict_app = typer.Typer(help=conflict_check_help, no_args_is_help=False)


@conflict_app.callback(invoke_without_command=True)
def conflict_callback(
    ctx: typer.Context,
    config_file: str = typer.Option("helpers/config.prod.yaml", "--config-file", "-c", help="Path to configuration file"),
    environment: str = typer.Option("production", "--environment", "-e", help="Environment to check (production/staging)"),
    timeout: int = typer.Option(5, "--timeout", "-t", help="Timeout for tool checks in seconds"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    output: str = typer.Option("text", "--output", "-o", help="Output format (text/json)"),
) -> None:
    """Check for tool version conflicts"""
    if ctx.invoked_subcommand is None:
        try:
            logger = Logger(verbose=verbose)

            config = ConflictConfig(
                config_file=config_file,
                environment=environment,
                timeout=timeout,
                verbose=verbose,
                output=output,
            )

            service = ConflictService(config, logger=logger)
            result = service.check_and_format()

            # Print the formatted result
            print(result)

            # Check if there are any conflicts and exit with appropriate code
            results = service.check_conflicts()
            conflicts = [r for r in results if r.conflict]

            if conflicts:
                logger.warning(f"Found {len(conflicts)} version conflict(s)")
                raise typer.Exit(1)
            else:
                logger.success("No version conflicts found")

        except Exception as e:
            logger = Logger(verbose=verbose)
            logger.error(error_checking_conflicts.format(error=str(e)))
            raise typer.Exit(1)
