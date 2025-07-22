import typer
import os
import yaml
import json
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from app.utils.protocols import LoggerProtocol
from app.utils.config import Config, VIEW_ENV_FILE, API_ENV_FILE, DEFAULT_REPO, DEFAULT_BRANCH, DEFAULT_PATH, NIXOPUS_CONFIG_DIR, PORTS, DEFAULT_COMPOSE_FILE, PROXY_PORT, SSH_KEY_TYPE, SSH_KEY_SIZE, SSH_FILE_PATH, VIEW_PORT, API_PORT
from app.utils.timeout import TimeoutWrapper
from app.commands.preflight.port import PortConfig, PortService
from app.commands.clone.clone import Clone, CloneConfig
from app.utils.lib import HostInformation, FileManager
from app.commands.conf.base import BaseEnvironmentManager
from app.commands.service.up import Up, UpConfig
from app.commands.proxy.load import Load, LoadConfig
from .ssh import SSH, SSHConfig
from .messages import (
    installation_failed, ports_unavailable, installing_nixopus,
    dependency_installation_timeout,
    clone_failed, env_file_creation_failed, env_file_permissions_failed, 
    proxy_config_created, ssh_setup_failed, services_start_failed, proxy_load_failed,
    operation_timed_out, created_env_file, config_file_not_found, configuration_key_has_no_default_value
)
from .deps import install_all_deps

_config = Config()
_config_dir = _config.get_yaml_value(NIXOPUS_CONFIG_DIR)
_source_path = _config.get_yaml_value(DEFAULT_PATH)

DEFAULTS = {
    'proxy_port': _config.get_yaml_value(PROXY_PORT),
    'ssh_key_type': _config.get_yaml_value(SSH_KEY_TYPE),   
    'ssh_key_size': _config.get_yaml_value(SSH_KEY_SIZE),
    'ssh_passphrase': None,
    'service_name': 'all',
    'service_detach': True,
    'required_ports': [int(port) for port in _config.get_yaml_value(PORTS)],
    'repo_url': _config.get_yaml_value(DEFAULT_REPO),
    'branch_name': _config.get_yaml_value(DEFAULT_BRANCH),
    'source_path': _source_path,
    'config_dir': _config_dir,
    'api_env_file_path': _config.get_yaml_value(API_ENV_FILE),
    'view_env_file_path': _config.get_yaml_value(VIEW_ENV_FILE),
    'compose_file': _config.get_yaml_value(DEFAULT_COMPOSE_FILE),
    'full_source_path': os.path.join(_config_dir, _source_path),
    'ssh_key_path': _config_dir + "/" + _config.get_yaml_value(SSH_FILE_PATH),
    'compose_file_path': _config_dir + "/" + _config.get_yaml_value(DEFAULT_COMPOSE_FILE),
    'host_os': HostInformation.get_os_name(),
    'package_manager': HostInformation.get_package_manager(),
    'view_port': _config.get_yaml_value(VIEW_PORT),
    'api_port': _config.get_yaml_value(API_PORT),   
}

def get_config_value(key: str, provided_value=None):
    return provided_value if provided_value is not None else DEFAULTS.get(key)

class Install:
    def __init__(self, logger: LoggerProtocol = None, verbose: bool = False, timeout: int = 300, force: bool = False, dry_run: bool = False, config_file: str = None, api_domain: str = None, view_domain: str = None):
        self.logger = logger
        self.verbose = verbose
        self.timeout = timeout
        self.force = force
        self.dry_run = dry_run
        self.config_file = config_file
        self.api_domain = api_domain
        self.view_domain = view_domain
        self._config_cache = {}
        self._user_config = self._load_user_config()
        self.progress = None
        self.main_task = None
    
    def _load_user_config(self):
        if not self.config_file:
            return {}
        
        try:
            if not os.path.exists(self.config_file):
                raise FileNotFoundError(config_file_not_found.format(config_file=self.config_file))
            
            with open(self.config_file, 'r') as f:
                user_config = yaml.safe_load(f)
            
            flattened = {}
            self._flatten_config(user_config, flattened)
            return flattened
        except Exception as e:
            if self.logger:
                self.logger.error(f"{config_file_not_found}: {str(e)}")
            raise
    
    def _flatten_config(self, config, result, prefix=""):
        for key, value in config.items():
            new_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                self._flatten_config(value, result, new_key)
            else:
                result[new_key] = value
    
    def _get_config(self, key: str):
        if key not in self._config_cache:
            user_value = self._get_user_config_value(key)
            value = user_value if user_value is not None else DEFAULTS.get(key)
            
            if value is None:
                raise ValueError(configuration_key_has_no_default_value.format(key=key))
            self._config_cache[key] = value
        return self._config_cache[key]
    
    def _get_user_config_value(self, key: str):
        key_mappings = {
            'proxy_port': 'services.caddy.env.PROXY_PORT',
            'repo_url': 'clone.repo',
            'branch_name': 'clone.branch',
            'source_path': 'clone.source-path',
            'config_dir': 'nixopus-config-dir',
            'api_env_file_path': 'services.api.env.API_ENV_FILE',
            'view_env_file_path': 'services.view.env.VIEW_ENV_FILE',
            'compose_file': 'compose-file-path',
            'required_ports': 'ports'
        }
        
        config_path = key_mappings.get(key, key)
        return self._user_config.get(config_path)

    def run(self):
        steps = [
            ("Preflight checks", self._run_preflight_checks),
            ("Installing dependencies", self._install_dependencies),
            ("Setting up proxy config", self._setup_proxy_config),
            ("Cloning repository", self._setup_clone_and_config),
            ("Creating environment files", self._create_env_files),
            ("Generating SSH keys", self._setup_ssh),
            ("Starting services", self._start_services),
        ]
        
        # Only add proxy steps if both api_domain and view_domain are provided
        if self.api_domain and self.view_domain:
            steps.append(("Loading proxy configuration", self._load_proxy))
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                transient=True,
                refresh_per_second=2,
            ) as progress:
                self.progress = progress
                self.main_task = progress.add_task(installing_nixopus, total=len(steps))
                
                for i, (step_name, step_func) in enumerate(steps):
                    progress.update(self.main_task, description=f"{installing_nixopus} - {step_name} ({i+1}/{len(steps)})")
                    try:
                        step_func()
                        progress.advance(self.main_task, 1)
                    except Exception as e:
                        progress.update(self.main_task, description=f"Failed at {step_name}")
                        raise
                
                progress.update(self.main_task, completed=True, description="Installation completed")
            
            self._show_success_message()
            
        except Exception as e:
            self._handle_installation_error(e)
            self.logger.error(f"{installation_failed}: {str(e)}")
            raise typer.Exit(1)

    def _handle_installation_error(self, error, context=""):
        context_msg = f" during {context}" if context else ""
        if self.verbose:
            self.logger.error(f"{installation_failed}{context_msg}: {str(error)}")
        else:
            self.logger.error(f"{installation_failed}{context_msg}")

    def _run_preflight_checks(self):
        port_config = PortConfig(ports=self._get_config('required_ports'), host="localhost", verbose=self.verbose)
        port_service = PortService(port_config, logger=self.logger)
        port_results = port_service.check_ports()
        unavailable_ports = [result for result in port_results if not result.get('is_available', True)]
        if unavailable_ports:
            error_msg = f"{ports_unavailable}: {[p['port'] for p in unavailable_ports]}"
            raise Exception(error_msg)

    def _install_dependencies(self):
        try:
            with TimeoutWrapper(self.timeout):
                result = install_all_deps(verbose=self.verbose, output="json", dry_run=self.dry_run)
        except TimeoutError:
            raise Exception(dependency_installation_timeout)

    def _setup_clone_and_config(self):        
        clone_config = CloneConfig(
            repo=self._get_config('repo_url'),
            branch=self._get_config('branch_name'),
            path=self._get_config('full_source_path'),
            force=self.force,
            verbose=self.verbose,
            output="text",
            dry_run=self.dry_run
        )
        clone_service = Clone(logger=self.logger)
        try:
            with TimeoutWrapper(self.timeout):
                result = clone_service.clone(clone_config)
        except TimeoutError:
            raise Exception(f"{clone_failed}: {operation_timed_out}")
        if not result.success:
            raise Exception(f"{clone_failed}: {result.error}")

    def _create_env_files(self):        
        api_env_file = self._get_config('api_env_file_path')
        view_env_file = self._get_config('view_env_file_path')
        FileManager.create_directory(FileManager.get_directory_path(api_env_file), logger=self.logger)
        FileManager.create_directory(FileManager.get_directory_path(view_env_file), logger=self.logger)
        services = [
            ("api", "services.api.env", api_env_file),
            ("view", "services.view.env", view_env_file),
        ]
        env_manager = BaseEnvironmentManager(self.logger)
        
        for i, (service_name, service_key, env_file) in enumerate(services):            
            env_values = _config.get_service_env_values(service_key)
            success, error = env_manager.write_env_file(env_file, env_values)
            if not success:
                raise Exception(f"{env_file_creation_failed} {service_name}: {error}")            
            file_perm_success, file_perm_error = FileManager.set_permissions(env_file, 0o644)
            if not file_perm_success:
                raise Exception(f"{env_file_permissions_failed} {service_name}: {file_perm_error}")            
            self.logger.debug(created_env_file.format(service_name=service_name, env_file=env_file))

    def _setup_proxy_config(self):
        full_source_path = self._get_config('full_source_path')
        caddy_json_template = os.path.join(full_source_path, 'helpers', 'caddy.json')
        
        if not self.dry_run:
            with open(caddy_json_template, 'r') as f:
                config_str = f.read()
            
            config_str = config_str.replace('{env.APP_DOMAIN}', self.view_domain)
            config_str = config_str.replace('{env.API_DOMAIN}', self.api_domain)
            
            host_ip = HostInformation.get_public_ip()
            view_port = self._get_config('view_port')
            api_port = self._get_config('api_port')
            
            app_reverse_proxy_url = f"{host_ip}:{view_port}"
            api_reverse_proxy_url = f"{host_ip}:{api_port}"
            config_str = config_str.replace('{env.APP_REVERSE_PROXY_URL}', app_reverse_proxy_url)
            config_str = config_str.replace('{env.API_REVERSE_PROXY_URL}', api_reverse_proxy_url)
            
            caddy_config = json.loads(config_str)
            with open(caddy_json_template, 'w') as f:
                json.dump(caddy_config, f, indent=2)
        
        self.logger.debug(f"{proxy_config_created}: {caddy_json_template}")

    def _setup_ssh(self):
        config = SSHConfig(
            path=self._get_config('ssh_key_path'),
            key_type=self._get_config('ssh_key_type'),
            key_size=self._get_config('ssh_key_size'),
            passphrase=self._get_config('ssh_passphrase'),
            verbose=self.verbose,
            output="text",
            dry_run=self.dry_run,
            force=self.force,
            set_permissions=True,
            add_to_authorized_keys=True,
            create_ssh_directory=True,
        )
        ssh_operation = SSH(logger=self.logger)
        try:
            with TimeoutWrapper(self.timeout):
                result = ssh_operation.generate(config)
        except TimeoutError:
            raise Exception(f"{ssh_setup_failed}: {operation_timed_out}")
        if not result.success:
            raise Exception(ssh_setup_failed)

    def _start_services(self):
        config = UpConfig(
            name=self._get_config('service_name'),
            detach=self._get_config('service_detach'),
            env_file=None,
            verbose=self.verbose,
            output="text",
            dry_run=self.dry_run,
            compose_file=self._get_config('compose_file_path')
        )

        up_service = Up(logger=self.logger)
        try:
            with TimeoutWrapper(self.timeout):
                result = up_service.up(config)
        except TimeoutError:
            raise Exception(f"{services_start_failed}: {operation_timed_out}")
        if not result.success:
            raise Exception(services_start_failed)

    def _load_proxy(self):
        proxy_port = self._get_config('proxy_port')
        full_source_path = self._get_config('full_source_path')
        caddy_json_config = os.path.join(full_source_path, 'helpers', 'caddy.json')
        config = LoadConfig(proxy_port=proxy_port, verbose=self.verbose, output="text", dry_run=self.dry_run, config_file=caddy_json_config)

        load_service = Load(logger=self.logger)
        try:
            with TimeoutWrapper(self.timeout):
                result = load_service.load(config)
        except TimeoutError:
            raise Exception(f"{proxy_load_failed}: {operation_timed_out}")

        if result.success:
            if not self.dry_run:
                self.logger.success(load_service.format_output(result, "text"))
        else:
            self.logger.error(result.error)
            raise Exception(proxy_load_failed)

    def _show_success_message(self):
        """Display formatted success message with access information"""
        nixopus_accessible_at = self._get_access_url()
        
        self.logger.success("Installation Complete!")
        self.logger.info(f"Nixopus is accessible at: {nixopus_accessible_at}")
        self.logger.highlight("Thank you for installing Nixopus!")
        self.logger.info("Please visit the documentation at https://docs.nixopus.com for more information.")
        self.logger.info("If you have any questions, please visit the community forum at https://discord.gg/skdcq39Wpv")
        self.logger.highlight("See you in the community!")
    
    def _get_access_url(self):
        """Determine the access URL based on provided domains or fallback to host IP"""
        if self.view_domain:
            return f"https://{self.view_domain}"
        elif self.api_domain:
            return f"https://{self.api_domain}"
        else:
            view_port = self._get_config('view_port')
            host_ip = HostInformation.get_public_ip()
            return f"http://{host_ip}:{view_port}"
