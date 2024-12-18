"""Chain module for interacting with the Bittensor blockchain.

This module provides functionality for storing and retrieving information on the Bittensor
blockchain through the ChainStore class. It handles both reading and writing operations
with appropriate subprocess management and timeout controls.
"""

import functools
from typing import Optional
import bittensor as bt
from bittensor.extrinsics.serving import publish_metadata

from atom.chain.generic import run_in_subprocess

class ChainStore:
    """Chain based implementation for storing and retrieving information on chain.
    
    This class provides methods to read from and write to the Bittensor blockchain,
    handling all necessary subprocess management and timeout controls.

    Args:
        netuid (int): The network UID to interact with
        chain (str, optional): The chain to connect to. Defaults to "finney"
        wallet (bt.wallet, optional): The wallet used for chain operations. Required for writing. Defaults to None
    """

    def __init__(
        self,
        netuid: int,
        chain: str = "finney",
        wallet: Optional[bt.wallet] = None,
    ):
        """Initialize the ChainStore instance.

        Args:
            netuid (int): The network UID to interact with
            chain (str, optional): The chain to connect to. Defaults to "finney"
            wallet (bt.wallet, optional): The wallet used for chain operations. Required for writing. Defaults to None
        """
        if wallet is None:
            bt.logging.warning(
                "No wallet provided. You will not be able to write to the chain."
            )
        self.wallet = wallet

        self.netuid = netuid
        self.subtensor = bt.subtensor(network=chain)

    async def write(
        self,
        data: str,
        wait_for_inclusion: bool = True,
        wait_for_finalization: bool = True,
    ):
        """Write data to the subnet chain for a specific wallet.

        Args:
            data (str): The data to write to the chain
            wait_for_inclusion (bool, optional): Whether to wait for the transaction to be included. Defaults to True
            wait_for_finalization (bool, optional): Whether to wait for the transaction to be finalized. Defaults to True

        Raises:
            ValueError: If no wallet is available or if no data is provided
        """
        if self.wallet is None:
            raise ValueError("No wallet available to write to the chain.")
        if not data:
            raise ValueError("No data provided to store on the chain.")

        # Wrap calls to the subtensor in a subprocess with a timeout to handle potential hangs.
        partial = functools.partial(
            publish_metadata,
            self.subtensor,
            self.wallet,
            self.netuid,
            f"Raw{len(data)}",
            data.encode(),
            wait_for_inclusion,
            wait_for_finalization,
        )

        bt.logging.info("Writing to chain...")
        run_in_subprocess(partial, 60)

    async def read(self, hotkey: str) -> str:
        """Read the most recent data from the chain for the specified hotkey.

        Args:
            hotkey (str): The hotkey to read data from

        Returns:
            str: The decoded data from the chain, or None if no data is found
        """

        # Wrap calls to the subtensor in a subprocess with a timeout to handle potential hangs.
        partial = functools.partial(
            bt.extrinsics.serving.get_metadata, self.subtensor, self.netuid, hotkey
        )

        metadata = run_in_subprocess(partial, 60)

        if not metadata:
            return None

        commitment = metadata["info"]["fields"][0]
        hex_data = commitment[list(commitment.keys())[0]][2:]

        chain_str = bytes.fromhex(hex_data).decode()

        return chain_str
