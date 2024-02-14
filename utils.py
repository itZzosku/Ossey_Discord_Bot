import json
from dotenv import load_dotenv
import os

load_dotenv()


def get_discord_token():
    # Use os.getenv to provide a default value if necessary, e.g., None
    return os.getenv('DISCORD_TOKEN', None)


def get_influxdb2_token():
    return os.getenv('INFLUXDB2_TOKEN', None)


def get_warcraft_logs_token():
    return os.getenv('WARCRAFT_LOGS_TOKEN', None)


def read_json_file(filename):
    with open(filename, 'r') as file:
        return json.load(file)


def hex_to_int(hex_color: str) -> int:
    hex_color = hex_color.lstrip('#')  # Remove '#' if present
    return int(hex_color, 16)


def get_config():
    return read_json_file('config.json')
