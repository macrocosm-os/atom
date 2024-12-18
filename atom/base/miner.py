# The MIT License (MIT)
# Copyright © 2024 Macrocosmos AI.

import time
import asyncio
import threading
import argparse
import traceback

from typing import Tuple
from abc import abstractmethod

import bittensor as bt
from atom.base.neuron import BaseNeuron
from atom.base.config import add_miner_args


class BaseMinerNeuron(BaseNeuron):
    """
    Base class for Bittensor miners.

    This class provides the fundamental structure and functionality for miners in the Bittensor network.
    It handles network registration, request processing, and network synchronization.
    """

    @classmethod
    def add_args(cls, parser: argparse.ArgumentParser):
        """
        Adds miner-specific arguments to the command line parser.

        Args:
            parser (argparse.ArgumentParser): The argument parser to add arguments to.
        """
        super().add_args(parser)
        add_miner_args(cls, parser)

    def __init__(self, config=None):
        """
        Initializes the BaseMinerNeuron.

        Args:
            config: Configuration object containing miner settings. Defaults to None.
        """
        super().__init__(config=config)

        # Warn if allowing incoming requests from anyone.
        if not self.config.get("blacklist.force_validator_permit"):
            bt.logging.warning(
                "You are allowing non-validators to send requests to your miner. This is a security risk."
            )
        if self.config.get("blacklist.allow_non_registered"):
            bt.logging.warning(
                "You are allowing non-registered entities to send requests to your miner. This is a security risk."
            )

        # The axon handles request processing, allowing validators to send this miner requests.
        self.axon = bt.axon(wallet=self.wallet, config=self.config)

        # Attach determiners which functions are called when servicing a request.
        bt.logging.info(f"Attaching forward function to miner axon.")
        self.axon.attach(
            forward_fn=self.forward,
            blacklist_fn=self.blacklist,
            priority_fn=self.priority,
        )

        bt.logging.info(f"Axon created: {self.axon}")

        # Instantiate runners
        self.should_exit: bool = False
        self.is_running: bool = False
        self.thread: threading.Thread = None
        self.lock = asyncio.Lock()

    def run(self):
        """
        Initiates and manages the main loop for the miner on the Bittensor network. The main loop handles graceful shutdown on keyboard interrupts and logs unforeseen errors.

        This function performs the following primary tasks:
        
        1. Check for registration on the Bittensor network.
        2. Starts the miner's axon, making it active on the network.
        3. Periodically resynchronizes with the chain; updating the metagraph with the latest network state and setting weights.

        The miner continues its operations until `should_exit` is set to True or an external interruption occurs.
        During each epoch of its operation, the miner waits for new blocks on the Bittensor network, updates its
        knowledge of the network (metagraph), and sets its weights. This process ensures the miner remains active
        and up-to-date with the network's latest state.

        Note:
            - The function leverages the global configurations set during the initialization of the miner.
            - The miner's axon serves as its interface to the Bittensor network, handling incoming and outgoing requests.

        Raises:
            KeyboardInterrupt: If the miner is stopped by a manual interruption.
            Exception: For unforeseen errors during the miner's operation, which are logged for diagnosis.
        """

        # Check that miner is registered on the network.
        self.sync()

        # Serve passes the axon information to the network + netuid we are hosting on.
        # This will auto-update if the axon port of external ip have changed.
        bt.logging.info(
            "Serving miner axon %s on network: %s with netuid: %s",
            self.axon,
            self.config.subtensor.chain_endpoint,
            self.config.netuid
        )
        self.axon.serve(netuid=self.config.netuid, subtensor=self.subtensor)

        # Start  starts the miner's axon, making it active on the network.
        self.axon.start()

        bt.logging.info("Miner starting at block: %s", self.block)

        # This loop maintains the miner's operations until intentionally stopped.
        try:
            while not self.should_exit:
                time.sleep(10)
                self.sync()

        # If someone intentionally stops the miner, it'll safely terminate operations.
        except KeyboardInterrupt:
            self.axon.stop()
            bt.logging.success("Miner killed by keyboard interrupt.")
            exit()

        # In case of unforeseen errors, the miner will log the error and continue operations.
        except Exception as e:
            bt.logging.error("Error: %s\n%s", str(e), traceback.format_exc())

    def __enter__(self):
        """
        Starts the miner's operations in a background thread upon entering the context.
        This method facilitates the use of the miner in a 'with' statement.

        Returns:
            BaseMinerNeuron: The instance of the miner.
        """
        self.run_in_background_thread()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Stops the miner's background operations upon exiting the context.
        This method facilitates the use of the miner in a 'with' statement.

        Args:
            exc_type: The type of the exception that caused the context to be exited.
                     None if the context was exited without an exception.
            exc_value: The instance of the exception that caused the context to be exited.
                      None if the context was exited without an exception.
            traceback: A traceback object encoding the stack trace.
                      None if the context was exited without an exception.
        """
        self.stop_run_thread()

    def resync_metagraph(self):
        """
        Resyncs the metagraph and updates network state.

        Updates the local copy of the network's metagraph, including hotkeys and moving averages,
        by synchronizing with the latest state of the Bittensor network.
        """
        bt.logging.info("resync_metagraph()")

        # Sync the metagraph.
        self.metagraph.sync(subtensor=self.subtensor)

    def set_weights(self):
        """
        Empty implementation as miners do not set weights on the network.
        
        This method is inherited from BaseNeuron but is intentionally left empty as
        miners are not responsible for setting weights - this is a validator function.
        """
        pass

    @abstractmethod
    def blacklist(self, synapse: bt.Synapse) -> Tuple[bool, str]:
        """
        Determines whether to blacklist an incoming request.

        Args:
            synapse (bt.Synapse): The synapse object containing the request details.

        Returns:
            Tuple[bool, str]: A tuple containing:
                - bool: Whether to blacklist the request (True) or not (False)
                - str: A message explaining the blacklist decision
        """
        ...

    @abstractmethod
    def priority(self, synapse: bt.Synapse) -> float:
        """
        Determines the priority level of an incoming request.

        Args:
            synapse (bt.Synapse): The synapse object containing the request details.

        Returns:
            float: The priority value assigned to the request. Higher values indicate higher priority.
        """
        ...
