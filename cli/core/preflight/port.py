import socket

def is_port_available(host: str, port: int, timeout: int = 1) -> bool:
    """Check if a port is available on the specified host"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            return result != 0
    except Exception:
        return False