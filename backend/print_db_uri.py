import os
from dotenv import load_dotenv

# Explicitly load the .env file from the project root
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../.env'))

for key, value in os.environ.items():
    if 'DATABASE' in key:
        print(f'{key}: {value}') 