import json


def read_json_file(filename):
    with open(filename, 'r') as file:
        return json.load(file)


def hex_to_int(hex_color):
    return int(hex_color.lstrip('#'), 16)


def get_discord_token():
    tokens = read_json_file('token.json')
    return tokens.get('discord_token', None)  # Provide a default value if necessary

def get_influxdb2_token():
    tokens = read_json_file('token.json')
    return tokens.get('influxdb2_token', None)  # Provide a default value if necessary


def get_warcraft_logs_token():
    tokens = read_json_file('token.json')
    return tokens.get('warcraft_logs_token', None)  # Provide a default value if necessary


def get_config():
    return read_json_file('config.json')
