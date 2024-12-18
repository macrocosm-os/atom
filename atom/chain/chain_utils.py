"""Various utility functions to be used for chain-related tasks."""


import json
from typing import Union

def json_reader(filepath: str, encoding: str = "utf-8") -> Union[dict, list]:
    """Reads and parses a JSON file into a Python object.

    Args:
        filepath (str): Path to the JSON file to be read
        encoding (str, optional): Character encoding to use when reading the file. Defaults to "utf-8"

    Returns:
        Union[dict, list]: The parsed JSON content as a Python object - either a dictionary or list 
                    depending on the JSON structure
    """
    with open(filepath, "r", encoding=encoding) as file:
        content = json.load(file)
    return content
