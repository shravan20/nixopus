import os
import subprocess
import re
import yaml
from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel, Field
from packaging import version
from app.utils.logger import Logger
from app.utils.protocols import LoggerProtocol
from app.utils.output_formatter import OutputFormatter
from app.utils.lib import ParallelProcessor
from .messages import (
    error_checking_tool_version,
    error_parsing_version,
    timeout_checking_tool,
    tool_not_found,
    tool_version_mismatch,
    tool_version_compatible,
    conflict_config_not_found,
    conflict_invalid_config,
    conflict_loading_config,
    conflict_config_loaded
)

class ConflictCheckResult(BaseModel):
    tool: str
    expected: Optional[str] = None
    current: Optional[str] = None
    status: str
    conflict: bool
    error: Optional[str] = None

class ConflictConfig(BaseModel):
    config_file: str = Field("helpers/config.prod.yaml", description="Path to configuration file")
    environment: str = Field("production", description="Environment to check (production/staging)")
    timeout: int = Field(5, gt=0, le=60, description="Timeout for tool checks")
    verbose: bool = Field(False, description="Verbose output")
    output: str = Field("text", description="Output format (text/json)")

class ConfigLoader:
    def __init__(self, logger: LoggerProtocol):
        self.logger = logger
    
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        self.logger.debug(conflict_loading_config.format(path=config_path))
        
        if not os.path.exists(config_path):
            raise FileNotFoundError(conflict_config_not_found.format(path=config_path))
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            self.logger.debug(conflict_config_loaded)
            return config
        except yaml.YAMLError as e:
            raise ValueError(conflict_invalid_config.format(error=str(e)))
        except Exception as e:
            raise Exception(conflict_invalid_config.format(error=str(e)))

class ToolVersionChecker:
    def __init__(self, timeout: int, logger: LoggerProtocol):
        self.timeout = timeout
        self.logger = logger
    
    def get_tool_version(self, tool: str) -> Optional[str]:
        """Get version of a tool"""
        try:
            # Common version commands for different tools
            version_commands = {
                'docker': ['docker', '--version'],
                'docker-compose': ['docker-compose', '--version'],
                'go': ['go', 'version'],
                'node': ['node', '--version'],
                'npm': ['npm', '--version'],
                'yarn': ['yarn', '--version'],
                'python': ['python', '--version'],
                'python3': ['python3', '--version'],
                'pip': ['pip', '--version'],
                'pip3': ['pip3', '--version'],
                'git': ['git', '--version'],
                'curl': ['curl', '--version'],
                'ssh': ['ssh', '-V'],
                'caddy': ['caddy', 'version'],
                'postgresql': ['psql', '--version'],
                'redis': ['redis-server', '--version'],
                'air': ['air', '-v']
            }
            
            cmd = version_commands.get(tool, [tool, '--version'])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            if result.returncode == 0:
                return self._parse_version_output(tool, result.stdout)
            else:
                # Try alternative version command
                alt_cmd = [tool, '-v']
                result = subprocess.run(
                    alt_cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )
                if result.returncode == 0:
                    return self._parse_version_output(tool, result.stdout)
                    
        except subprocess.TimeoutExpired:
            self.logger.error(timeout_checking_tool.format(tool=tool))
            return None
        except Exception as e:
            self.logger.error(error_checking_tool_version.format(tool=tool, error=str(e)))
            return None
        
        return None
    
    def _parse_version_output(self, tool: str, output: str) -> Optional[str]:
        """Parse version from tool output"""
        try:
            # Common version patterns
            patterns = [
                r'version\s+(\d+\.\d+\.\d+)',
                r'v(\d+\.\d+\.\d+)',
                r'(\d+\.\d+\.\d+)',
                r'Version\s+(\d+\.\d+\.\d+)',
                r'(\d+\.\d+)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, output, re.IGNORECASE)
                if match:
                    return match.group(1)
            
            # Tool-specific parsing
            if tool == 'go':
                match = re.search(r'go(\d+\.\d+\.\d+)', output)
                if match:
                    return match.group(1)
            
            return None
        except Exception as e:
            self.logger.error(error_parsing_version.format(tool=tool, error=str(e)))
            return None
    
    def compare_versions(self, current: str, expected: str) -> bool:
        """Compare version against requirement specification"""
        try:
            from packaging.specifiers import SpecifierSet
            from packaging.version import Version
            
            # Handle simple version comparisons (backwards compatibility)
            if not any(op in expected for op in ['>=', '<=', '>', '<', '==', '!=', '~', '^']):
                # Default to >= for simple version strings
                return version.parse(current) >= version.parse(expected)
            
            # Handle version ranges and specifiers
            spec_set = SpecifierSet(expected)
            return Version(current) in spec_set
            
        except Exception:
            # Fallback to string comparison
            return current == expected
    
    def parse_version_requirement(self, requirement: str) -> str:
        """Parse version requirement and return a normalized specifier"""
        if not requirement:
            return requirement
            
        # Handle common version range formats
        
        # Handle npm-style caret ranges: ^1.20.0 -> >=1.20.0, <2.0.0
        if requirement.startswith('^'):
            base_version = requirement[1:]
            try:
                parsed = version.parse(base_version)
                major = parsed.major
                return f">={base_version}, <{major + 1}.0.0"
            except Exception:
                return f">={base_version}"
        
        # Handle npm-style tilde ranges: ~1.20.0 -> >=1.20.0, <1.21.0
        if requirement.startswith('~'):
            base_version = requirement[1:]
            try:
                parsed = version.parse(base_version)
                major = parsed.major
                minor = parsed.minor
                return f">={base_version}, <{major}.{minor + 1}.0"
            except Exception:
                return f">={base_version}"
        
        # Handle ranges with commas: 1.20.0,2.0.0 -> >=1.20.0, <2.0.0
        if ',' in requirement and not any(op in requirement for op in ['>=', '<=', '>', '<', '==', '!=']):
            parts = [p.strip() for p in requirement.split(',')]
            if len(parts) == 2:
                return f">={parts[0]}, <{parts[1]}"
        
        # Handle x.x.x format ranges: 1.20.* -> >=1.20.0, <1.21.0
        if requirement.endswith('.*') or requirement.endswith('.x'):
            base_version = requirement.replace('.*', '.0').replace('.x', '.0')
            try:
                parsed = version.parse(base_version)
                major = parsed.major
                minor = parsed.minor
                return f">={base_version}, <{major}.{minor + 1}.0"
            except Exception:
                return f">={base_version}"
        
        # Return as-is if it already contains operators
        return requirement

class ConflictChecker:
    def __init__(self, config: ConflictConfig, logger: LoggerProtocol):
        self.config = config
        self.logger = logger
        self.config_loader = ConfigLoader(logger)
        self.version_checker = ToolVersionChecker(config.timeout, logger)
    
    def check_conflicts(self) -> List[ConflictCheckResult]:
        """Check for version conflicts"""
        results = []
        
        try:
            # Load configuration
            config_data = self.config_loader.load_config(self.config.config_file)
            
            # Extract version requirements from deps section
            deps = config_data.get('deps', {})
            
            if not deps:
                self.logger.warning("No dependencies found in configuration")
                return results
            
            # Check version conflicts
            results.extend(self._check_version_conflicts(deps))
            
        except Exception as e:
            self.logger.error(f"Error loading configuration: {str(e)}")
            results.append(ConflictCheckResult(
                tool="configuration",
                status="error",
                conflict=True,
                error=str(e)
            ))
        
        return results
    
    def _check_version_conflicts(self, deps: Dict[str, Any]) -> List[ConflictCheckResult]:
        """Check for tool version conflicts from deps configuration"""
        results = []
        
        # Extract version requirements from deps
        version_requirements = {}
        
        for tool, config in deps.items():
            if isinstance(config, dict):
                # Only check tools that have a version key (even if empty)
                if 'version' in config:
                    version_req = config.get('version', '')
                    version_requirements[tool] = version_req if version_req else None
        
        def check_version(tool_requirement: Tuple[str, Optional[str]]) -> ConflictCheckResult:
            tool, expected_version = tool_requirement
            
            # Map tool names to common command names
            tool_mapping = {
                'open-ssh': 'ssh',
                'open-sshserver': 'sshd',
                'python3-venv': 'python3'
            }
            
            command_name = tool_mapping.get(tool, tool)
            current_version = self.version_checker.get_tool_version(command_name)
            
            if current_version is None:
                return ConflictCheckResult(
                    tool=tool,
                    expected=expected_version,
                    current=None,
                    status=tool_not_found,
                    conflict=True
                )
            
            if expected_version is None or expected_version == "":
                # Just check existence
                return ConflictCheckResult(
                    tool=tool,
                    expected="present",
                    current=current_version,
                    status=tool_version_compatible,
                    conflict=False
                )
            
            # Parse version requirement to handle ranges
            normalized_expected = self.version_checker.parse_version_requirement(expected_version)
            
            # Check version compatibility
            is_compatible = self.version_checker.compare_versions(current_version, normalized_expected)
            
            return ConflictCheckResult(
                tool=tool,
                expected=normalized_expected,
                current=current_version,
                status=tool_version_compatible if is_compatible else tool_version_mismatch,
                conflict=not is_compatible
            )
        
        # Check versions in parallel
        def error_handler(tool_requirement: Tuple[str, Optional[str]], error: Exception) -> ConflictCheckResult:
            tool, expected_version = tool_requirement
            return ConflictCheckResult(
                tool=tool,
                expected=expected_version,
                current=None,
                status="error",
                conflict=True,
                error=str(error)
            )
        
        if version_requirements:
            results = ParallelProcessor.process_items(
                items=list(version_requirements.items()),
                processor_func=check_version,
                max_workers=min(len(version_requirements), 10),
                error_handler=error_handler
            )
        
        return results

class ConflictFormatter:
    def __init__(self):
        self.output_formatter = OutputFormatter()
    
    def format_output(self, results: List[ConflictCheckResult], output_type: str) -> str:
        """Format conflict check results"""
        if not results:
            return self.output_formatter.format_output(
                self.output_formatter.create_success_message("No version conflicts to check"),
                output_type
            )
        
        messages = []
        for result in results:
            data = result.model_dump()
            
            if result.conflict:
                if result.current is None:
                    message = f"{result.tool}: {result.status}"
                else:
                    message = f"{result.tool}: Expected {result.expected}, Found {result.current}"
                messages.append(self.output_formatter.create_error_message(message, data))
            else:
                message = f"{result.tool}: Version compatible ({result.current})"
                messages.append(self.output_formatter.create_success_message(message, data))
        
        return self.output_formatter.format_output(messages, output_type)

class ConflictService:
    def __init__(self, config: ConflictConfig, logger: Optional[LoggerProtocol] = None):
        self.config = config
        self.logger = logger or Logger(verbose=config.verbose)
        self.checker = ConflictChecker(config, self.logger)
        self.formatter = ConflictFormatter()
    
    def check_conflicts(self) -> List[ConflictCheckResult]:
        """Check for conflicts and return results"""
        self.logger.debug("Starting version conflict checks")
        return self.checker.check_conflicts()
    
    def check_and_format(self) -> str:
        """Check conflicts and return formatted output"""
        results = self.check_conflicts()
        return self.formatter.format_output(results, self.config.output)
