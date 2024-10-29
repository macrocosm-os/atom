import os
import json

import subprocess
import bittensor as bt
from typing import List


def run_command(command: List[str], cwd: str = None) -> str:
    """Runs a subprocess command."""
    try:
        result = subprocess.run(
            command, check=True, text=True, capture_output=True, cwd=cwd
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        bt.logging.error(f"Error executing command: {' '.join(command)}")
        bt.logging.error(f"Error message: {e.stderr.strip()}")
        raise


def json_reader(filepath: str):
    with open(filepath, "r") as file:
        content = json.load(file)
    return content
