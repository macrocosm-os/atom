import functools
from typing import Optional

from atom.chain.generic import run_in_subprocess

import bittensor as bt
from bittensor.extrinsics.serving import publish_metadata


class ChainStore:
    """Chain based implementation for storing and retrieving information on chain."""

    def __init__(
        self,
        netuid: int,
        chain: str = "finney",
        # Wallet is only needed to write to the chain, not to read.
        wallet: Optional[bt.wallet] = None,
    ):
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
        """write to the subnet chain for a specific wallet."""
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
        """Reads the most recent data from the chain from the specified hotkey."""

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
