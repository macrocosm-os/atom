import os
import json

import subprocess
import bittensor as bt
from typing import List, Dict, Any

def is_validator(uid: int, metagraph: bt.metagraph, stake_needed = 10_000) -> bool:
    """Checks if a UID on the subnet is a validator."""
    return metagraph.validator_permit[uid] and metagraph.S[uid] >= stake_needed

def get_validator_data(metagraph: bt.metagraph) -> Dict[str, Dict[str, Any]]:
    """Retrieve validator data (hotkey, percent stake) from metagraph."""

    total_stake = sum(
        stake
        for uid, stake in enumerate(metagraph.S)
        if is_validator(uid, metagraph)
    )

    validator_data = {
        hotkey: {
            'percent_stake': float(stake / total_stake),
            'hash': None,
            'data': None
        }
        for uid, (hotkey, stake) in enumerate(zip(metagraph.hotkeys, metagraph.S))
        if is_validator(uid, metagraph)
    }

    return validator_data

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
