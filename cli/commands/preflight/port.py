import re, json
from typing import List, TypedDict, Union, Any
from pydantic import BaseModel, Field, field_validator
from .messages import available, not_available
from core.preflight.port import is_port_available
from utils.logger import Logger

class PortCheckResult(TypedDict):
    port: int
    status: str
    host: str | None
    error: str | None
    is_available: bool

class PortConfig(BaseModel):
    ports: List[int] = Field(..., min_length=1, max_length=65535, description="List of ports to check")
    host: str = Field("localhost", min_length=1, description="Host to check")
    timeout: int = Field(1, gt=0, le=60, description="Timeout in seconds")
    verbose: bool = Field(False, description="Verbose output")

    @field_validator('host')
    @classmethod
    def validate_host(cls, v: str) -> str:
        """Validate host is localhost, valid IP address, or domain name"""
        if v.lower() == "localhost":
            return v
        
        # IP address validation regex
        ip_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        if re.match(ip_pattern, v):
            return v
        
        # Domain name validation regex
        domain_pattern = r'^[a-zA-Z]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        if re.match(domain_pattern, v):
            return v
        
        raise ValueError("Host must be 'localhost', a valid IP address, or a valid domain name")

    @staticmethod
    def format(data: Union[str, List[PortCheckResult], Any], output_type: str) -> str:
        """Format output based on output type"""
        if output_type == "json":
            return json.dumps(data, indent=4)
        elif output_type == "text" and isinstance(data, list):
            return "\n".join([f"Port {item['port']}: {item['status']}" for item in data])
        else:
            return str(data)

    @staticmethod
    def check_ports(config: "PortConfig") -> List[PortCheckResult]:
        """Check if ports are available"""
        logger = Logger(verbose=config.verbose)
        results = []
        for port in config.ports:
            logger.debug(f"Checking port {port} on host {config.host}")
            status = available if is_port_available(config.host, port, config.timeout) else not_available
            result = {
                "port": port,
                "status": status,
                "host": config.host if config.verbose else None,
                "error": None,
                "is_available": status == available
            }
            results.append(result)
        return results
