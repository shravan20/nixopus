import typer
from app.utils.logger import Logger
from app.utils.timeout import TimeoutWrapper
from .dev import DevSetup, DevSetupConfig

setup_app = typer.Typer(help="Setup development and production environments")

@setup_app.command()
def dev(
    # Port configurations from config.dev.yaml defaults
    api_port: int = typer.Option(8080, "--api-port", help="API server port"),
    view_port: int = typer.Option(7443, "--view-port", help="Frontend server port"),
    db_port: int = typer.Option(5432, "--db-port", help="Database port"),
    redis_port: int = typer.Option(6379, "--redis-port", help="Redis port"),
    
    # Repository and branch configuration
    branch: str = typer.Option("feat/develop", "--branch", "-b", help="Git branch to clone"),
    repo: str = typer.Option(None, "--repo", "-r", help="Custom repository URL"),
    workspace: str = typer.Option("./nixopus-dev", "--workspace", "-w", help="Target workspace directory"),
    
    # SSH configuration
    ssh_key_path: str = typer.Option("~/.ssh/id_ed25519_nixopus", "--ssh-key-path", help="SSH key location"),
    ssh_key_type: str = typer.Option("ed25519", "--ssh-key-type", help="SSH key type"),
    
    # Setup options
    skip_preflight: bool = typer.Option(False, "--skip-preflight", help="Skip preflight validation checks"),
    skip_conflict: bool = typer.Option(False, "--skip-conflict", help="Skip conflict detection"),
    skip_deps: bool = typer.Option(False, "--skip-deps", help="Skip dependency installation"),
    skip_docker: bool = typer.Option(False, "--skip-docker", help="Skip Docker-based database setup"),
    skip_ssh: bool = typer.Option(False, "--skip-ssh", help="Skip SSH key generation"),
    skip_admin: bool = typer.Option(False, "--skip-admin", help="Skip admin account creation"),
    
    # Admin credentials
    admin_email: str = typer.Option(None, "--admin-email", help="Admin email (defaults to $USER@example.com)"),
    admin_password: str = typer.Option("Nixopus123!", "--admin-password", help="Admin password"),
    
    # Control options
    force: bool = typer.Option(False, "--force", "-f", help="Force overwrite existing files"),
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="Show what would be done"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Detailed output"),
    timeout: int = typer.Option(300, "--timeout", "-t", help="Operation timeout in seconds"),
    
    # Output configuration
    output: str = typer.Option("text", "--output", "-o", help="Output format (text/json)"),
    
    # Configuration override
    config_file: str = typer.Option("../helpers/config.dev.yaml", "--config-file", "-c", help="Configuration file path"),
):
    """Setup complete development environment for Nixopus"""
    try:
        logger = Logger(verbose=verbose)
        
        # Create configuration object
        config = DevSetupConfig(
            api_port=api_port,
            view_port=view_port,
            db_port=db_port,
            redis_port=redis_port,
            branch=branch,
            repo=repo,
            workspace=workspace,
            ssh_key_path=ssh_key_path,
            ssh_key_type=ssh_key_type,
            skip_preflight=skip_preflight,
            skip_conflict=skip_conflict,
            skip_deps=skip_deps,
            skip_docker=skip_docker,
            skip_ssh=skip_ssh,
            skip_admin=skip_admin,
            admin_email=admin_email,
            admin_password=admin_password,
            force=force,
            dry_run=dry_run,
            verbose=verbose,
            timeout=timeout,
            output=output,
            config_file=config_file,
        )
        
        # Initialize development setup orchestrator
        dev_setup = DevSetup(config=config, logger=logger)
        
        # Execute setup with timeout
        with TimeoutWrapper(timeout):
            dev_setup.run()
            
        logger.success("Development environment setup completed successfully!")
        
    except TimeoutError as e:
        logger.error(f"Setup timed out after {timeout} seconds: {e}")
        raise typer.Exit(1)
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        if verbose:
            import traceback
            logger.error(traceback.format_exc())
        raise typer.Exit(1)