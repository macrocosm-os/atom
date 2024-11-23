import json


def json_reader(filepath: str):
    with open(filepath, "r") as file:
        content = json.load(file)
    return content
