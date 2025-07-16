import os
import shutil
import tempfile
from typing import Dict, Generic, Optional, Protocol, TypeVar

from pydantic import BaseModel, Field, field_validator

from app.utils.logger import Logger
from app.utils.protocols import LoggerProtocol
from app.utils.config import Config, API_ENV_FILE, VIEW_ENV_FILE

from .messages import (
    atomic_complete,
    atomic_failed,
    atomic_write,
    atomic_write_failed,
    backup_created,
    backup_created_at,
    backup_created_success,
    backup_creation_failed,
    backup_exists,
    backup_failed,
    backup_file_not_found,
    backup_not_found,
    backup_remove_failed,
    backup_removed,
    backup_restore_attempt,
    backup_restore_failed,
    backup_restore_success,
    backup_restored,
    cleanup_failed,
    cleanup_temp,
    config_entries,
    creating_backup,
    directory_ensured,
    file_not_exists,
    file_not_found,
    file_read_failed,
    file_write_failed,
    getting_service,
    invalid_line_warning,
    invalid_service,
    no_backup_needed,
    parsed_config,
    read_error,
    read_success,
    reading_env_file,
    replacing_file,
    restore_failed,
    restoring_backup,
    skipping_line,
    sync_not_critical,
    synced_temp,
    temp_file_created,
    unexpected_error,
    using_default_api,
    using_default_view,
    using_provided_env,
    write_complete,
    writing_entries,
    writing_env_file,
    wrote_to_temp,
)

TConfig = TypeVar("TConfig", bound=BaseModel)
TResult = TypeVar("TResult", bound=BaseModel)


class EnvironmentServiceProtocol(Protocol):
    def list_config(self, service: str, env_file: str = None) -> tuple[bool, Dict[str, str], str]: ...

    def set_config(self, service: str, key: str, value: str, env_file: str = None) -> tuple[bool, str]: ...

    def delete_config(self, service: str, key: str, env_file: str = None) -> tuple[bool, str]: ...


class BaseEnvironmentManager:
    def __init__(self, logger: LoggerProtocol):
        self.logger = logger

    def read_env_file(self, file_path: str) -> tuple[bool, Dict[str, str], Optional[str]]:
        self.logger.debug(reading_env_file.format(file_path=file_path))
        try:
            if not os.path.exists(file_path):
                self.logger.debug(file_not_exists.format(file_path=file_path))
                return False, {}, file_not_found.format(path=file_path)

            config = {}
            with open(file_path, "r") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith("#"):
                        self.logger.debug(skipping_line.format(line_num=line_num))
                        continue

                    if "=" not in line:
                        self.logger.warning(invalid_line_warning.format(line_num=line_num, file_path=file_path, line=line))
                        continue

                    key, value = line.split("=", 1)
                    config[key.strip()] = value.strip()
                    self.logger.debug(parsed_config.format(key=key.strip(), value=value.strip()))

            self.logger.debug(read_success.format(count=len(config), file_path=file_path))
            return True, config, None
        except Exception as e:
            self.logger.debug(read_error.format(file_path=file_path, error=e))
            return False, {}, file_read_failed.format(error=e)

    def _create_backup(self, file_path: str) -> tuple[bool, Optional[str], Optional[str]]:
        self.logger.debug(creating_backup.format(file_path=file_path))
        if not os.path.exists(file_path):
            self.logger.debug(no_backup_needed.format(file_path=file_path))
            return True, None, None

        try:
            backup_path = f"{file_path}.backup"
            self.logger.debug(backup_created_at.format(backup_path=backup_path))
            shutil.copy2(file_path, backup_path)
            self.logger.debug(backup_created_success.format(backup_path=backup_path))
            return True, backup_path, None
        except Exception as e:
            self.logger.debug(backup_failed.format(error=e))
            return False, None, backup_creation_failed.format(error=e)

    def _restore_backup(self, backup_path: str, file_path: str) -> tuple[bool, Optional[str]]:
        self.logger.debug(restoring_backup.format(backup_path=backup_path, file_path=file_path))
        try:
            if os.path.exists(backup_path):
                self.logger.debug(backup_exists)
                shutil.copy2(backup_path, file_path)
                os.remove(backup_path)
                self.logger.debug(backup_restored)
                return True, None
            self.logger.debug(backup_not_found.format(backup_path=backup_path))
            return False, backup_file_not_found.format(path=backup_path)
        except Exception as e:
            self.logger.debug(restore_failed.format(error=e))
            return False, backup_restore_failed.format(error=e)

    def _atomic_write(self, file_path: str, config: Dict[str, str]) -> tuple[bool, Optional[str]]:
        self.logger.debug(atomic_write.format(file_path=file_path))
        self.logger.debug(writing_entries.format(count=len(config)))
        temp_path = None
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            self.logger.debug(directory_ensured.format(directory=os.path.dirname(file_path)))

            with tempfile.NamedTemporaryFile(mode="w", delete=False, dir=os.path.dirname(file_path)) as temp_file:
                self.logger.debug(temp_file_created.format(temp_path=temp_file.name))
                for key, value in sorted(config.items()):
                    temp_file.write(f"{key}={value}\n")
                    self.logger.debug(wrote_to_temp.format(key=key, value=value))
                temp_file.flush()
                try:
                    os.fsync(temp_file.fileno())
                    self.logger.debug(synced_temp)
                except (OSError, AttributeError):
                    self.logger.debug(sync_not_critical)
                    pass
                temp_path = temp_file.name

            self.logger.debug(replacing_file.format(file_path=file_path))
            os.replace(temp_path, file_path)
            self.logger.debug(atomic_complete)
            return True, None
        except Exception as e:
            self.logger.debug(atomic_failed.format(error=e))
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                    self.logger.debug(cleanup_temp.format(temp_path=temp_path))
                except:
                    self.logger.debug(cleanup_failed.format(temp_path=temp_path))
                    pass
            return False, file_write_failed.format(error=e)

    def write_env_file(self, file_path: str, config: Dict[str, str]) -> tuple[bool, Optional[str]]:
        self.logger.debug(writing_env_file.format(file_path=file_path))
        self.logger.debug(config_entries.format(count=len(config)))
        backup_created_flag = False
        backup_path = None

        try:
            success, backup_path, error = self._create_backup(file_path)
            if not success:
                self.logger.debug(backup_creation_failed.format(error=error))
                return False, error

            backup_created_flag = True
            self.logger.info(backup_created.format(backup_path=backup_path))

            success, error = self._atomic_write(file_path, config)
            if not success:
                self.logger.debug(atomic_write_failed)
                if backup_created_flag and backup_path:
                    self.logger.warning(backup_restore_attempt)
                    restore_success, restore_error = self._restore_backup(backup_path, file_path)
                    if restore_success:
                        self.logger.info(backup_restore_success)
                    else:
                        self.logger.error(backup_restore_failed.format(error=restore_error))
                return False, error

            if backup_created_flag and backup_path and os.path.exists(backup_path):
                try:
                    os.remove(backup_path)
                    self.logger.info(backup_removed)
                    self.logger.debug(backup_removed.format(backup_path=backup_path))
                except Exception as e:
                    self.logger.warning(backup_remove_failed.format(error=e))
                    self.logger.debug(backup_remove_failed.format(error=e))

            self.logger.debug(write_complete)
            return True, None

        except Exception as e:
            self.logger.debug(unexpected_error.format(error=e))
            return False, file_write_failed.format(error=e)

    def get_service_env_file(self, service: str, env_file: Optional[str] = None) -> str:
        self.logger.debug(getting_service.format(service=service))
        if env_file:
            self.logger.debug(using_provided_env.format(env_file=env_file))
            return env_file

        config = Config()
        if service == "api":
            default_path = config.get_yaml_value(API_ENV_FILE)
            self.logger.debug(using_default_api.format(path=default_path))
            return default_path
        elif service == "view":
            default_path = config.get_yaml_value(VIEW_ENV_FILE)
            self.logger.debug(using_default_view.format(path=default_path))
            return default_path
        else:
            self.logger.debug(invalid_service.format(service=service))
            raise ValueError(invalid_service.format(service=service))


class BaseConfig(BaseModel):
    service: str = Field("api", description="The name of the service to manage configuration for")
    key: Optional[str] = Field(None, description="The configuration key")
    value: Optional[str] = Field(None, description="The configuration value")
    verbose: bool = Field(False, description="Verbose output")
    output: str = Field("text", description="Output format: text, json")
    dry_run: bool = Field(False, description="Dry run mode")
    env_file: Optional[str] = Field(None, description="Path to the environment file")

    @field_validator("env_file")
    @classmethod
    def validate_env_file(cls, env_file: str) -> Optional[str]:
        if not env_file:
            return None
        stripped_env_file = env_file.strip()
        if not stripped_env_file:
            return None
        if not os.path.exists(stripped_env_file):
            raise ValueError(file_not_found.format(path=stripped_env_file))
        return stripped_env_file


class BaseResult(BaseModel):
    service: str
    key: Optional[str] = None
    value: Optional[str] = None
    config: Dict[str, str] = Field(default_factory=dict)
    verbose: bool
    output: str
    success: bool = False
    error: Optional[str] = None


class BaseService(Generic[TConfig, TResult]):
    def __init__(self, config: TConfig, logger: LoggerProtocol = None, environment_service: EnvironmentServiceProtocol = None):
        self.config = config
        self.logger = logger or Logger(verbose=config.verbose)
        self.environment_service = environment_service
        self.formatter = None

    def _create_result(self, success: bool, error: str = None, config_dict: Dict[str, str] = None) -> TResult:
        raise NotImplementedError

    def execute(self) -> TResult:
        raise NotImplementedError

    def execute_and_format(self) -> str:
        raise NotImplementedError


class BaseAction(Generic[TConfig, TResult]):
    def __init__(self, logger: LoggerProtocol = None):
        self.logger = logger
        self.formatter = None

    def execute(self, config: TConfig) -> TResult:
        raise NotImplementedError

    def format_output(self, result: TResult, output: str) -> str:
        raise NotImplementedError
