import os
import json

import subprocess
import bittensor as bt
from typing import List, Dict, Any


def check_uid_availability(
    metagraph,
    uid: int,
    vpermit_tao_limit: int = 10_000,
    coldkeys: set = None,
    ips: set = None,
) -> bool:
    """Check if uid is available. The UID should be available if it is serving and has less than vpermit_tao_limit stake
    Args:
        metagraph (:obj: bt.metagraph): Metagraph object
        uid (int): uid to be checked
        vpermit_tao_limit (int): Validator permit tao limit
        coldkeys (set): Set of coldkeys to exclude
        ips (set): Set of ips to exclude
    Returns:
        bool: True if uid is available, False otherwise
    """
    # Filter non serving axons.
    if not metagraph.axons[uid].is_serving:
        return False

    # Filter validator permit > 1024 stake.
    if metagraph.validator_permit[uid] and metagraph.S[uid] > vpermit_tao_limit:
        return False

    if coldkeys and metagraph.axons[uid].coldkey in coldkeys:
        return False

    if ips and metagraph.axons[uid].ip in ips:
        return False

    # Available otherwise.
    return True


def get_top_incentive_uids(
    metagraph, k: int, vpermit_tao_limit: int = 10_000
) -> List[int]:
    """get the top k uids with the highest incentives.

    Args:
        metagraph (bt.metagraph)
        k (int): Number of uids.
        vpermit_tao_limit (int, optional): Amount of stake that we decide determines if a hotkey is a validator. Defaults to 10_000.

    Returns:
        List[int]: sorted top-k miners.
    """

    miners_uids = list(
        map(
            int,
            filter(
                lambda uid: check_uid_availability(
                    metagraph=metagraph, uid=uid, vpermit_tao_limit=vpermit_tao_limit
                ),
                metagraph.uids,
            ),
        )
    )

    # Builds a dictionary of uids and their corresponding incentives.
    all_miners_incentives = {
        "miners_uids": miners_uids,
        "incentives": list(map(lambda uid: metagraph.I[uid], miners_uids)),
    }

    # Zip the uids and their corresponding incentives into a list of tuples.
    uid_incentive_pairs = list(
        zip(all_miners_incentives["miners_uids"], all_miners_incentives["incentives"])
    )

    # Sort the list of tuples by the incentive value in descending order.
    uid_incentive_pairs_sorted = sorted(
        uid_incentive_pairs, key=lambda x: x[1], reverse=True
    )

    # Extract the top uids.
    top_k_uids = [uid for uid, incentive in uid_incentive_pairs_sorted[:k]]
    return top_k_uids


def is_validator(uid: int, metagraph: bt.metagraph, stake_needed=10_000) -> bool:
    """Checks if a UID on the subnet is a validator."""
    return metagraph.validator_permit[uid] and metagraph.S[uid] >= stake_needed


def get_validator_data(metagraph: bt.metagraph) -> Dict[str, Dict[str, Any]]:
    """Retrieve validator data (hotkey, percent stake) from metagraph."""

    total_stake = sum(
        stake for uid, stake in enumerate(metagraph.S) if is_validator(uid, metagraph)
    )

    validator_data = {
        hotkey: {
            "percent_stake": float(stake / total_stake),
            "hash": None,
            "data": None,
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
