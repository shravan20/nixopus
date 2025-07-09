import os

def get_env(default="PRODUCTION"):
    return os.environ.get("ENV", default)

def is_development():
    return get_env().upper() == "DEVELOPMENT" 