import os

from env_loader import load_app_env

load_app_env()

for key, value in os.environ.items():
    if "DATABASE" in key:
        print(f"{key}: {value}")
