# The MIT License (MIT)
# Copyright © 2024 Macrocosmos AI.

import copy
import threading
from abc import ABC, abstractmethod

import bittensor as bt

from atom.base.ttl import ttl_get_block
from atom.base.config import check_config, add_args
from atom.base.config import config as bittensor_config

from atom.mock.mock import MockSubtensor, MockMetagraph, create_wallet


class BaseNeuron(ABC):
    """
    Base class for Bittensor miners and validators.

    This class provides the core functionality for all neurons in the Bittensor network.
    It handles wallet management, network synchronization, and state management through
    a basic checkpointing mechanism based on epoch length.

    Attributes:
        subtensor (bt.subtensor): Interface to the Bittensor blockchain
        wallet (bt.wallet): Wallet containing cryptographic keys
        metagraph (bt.metagraph): Network state information
    """

    @classmethod
    def check_config(cls, config: "bt.Config"):
        """
        Validates the configuration for the neuron.

        Args:
            config (bt.Config): Configuration object to validate
        """
        check_config(cls, config)

    @classmethod
    def add_args(cls, parser):
        """
        Adds neuron-specific arguments to the command line parser.

        Args:
            parser: The argument parser to add arguments to
        """
        add_args(cls, parser)

    @classmethod
    def get_config(cls):
        """
        Returns the default configuration for the neuron.

        Returns:
            bt.Config: Default configuration object
        """
        return bittensor_config(cls)

    subtensor: "bt.subtensor"
    wallet: "bt.wallet"
    metagraph: "bt.metagraph"

    @property
    @abstractmethod
    def spec_version(self):
        """
        Abstract property for the neuron's specification version.

        Returns:
            Version information for the neuron implementation
        """
        ...

    @property
    def block(self):
        """
        Gets the current block number from the Bittensor network.

        Returns:
            int: Current block number
        """
        return ttl_get_block(self)

    def __init__(self, config=None):
        base_config = copy.deepcopy(config or BaseNeuron.get_config())
        self.config = self.get_config()
        self.config.merge(base_config)
        self.check_config(self.config)

        # Set up logging with the provided configuration and directory.
        bt.logging(config=self.config, logging_dir=self.config.full_path)

        # If a gpu is required, set the device to cuda:N (e.g. cuda:0)
        self.device = self.config.neuron.device

        # Log the configuration for reference.
        bt.logging.info(self.config)

        # Build Bittensor objects
        # These are core Bittensor classes to interact with the network.
        bt.logging.info("Setting up bittensor objects.")

        # The wallet holds the cryptographic key pairs for the miner.
        if self.config.mock:
            self.wallet = create_wallet()
            self.subtensor = MockSubtensor(self.config.netuid, wallet=self.wallet)
            self.metagraph = MockMetagraph(self.config.netuid, subtensor=self.subtensor)
        else:
            self.wallet = bt.wallet(config=self.config)
            self.subtensor = bt.subtensor(config=self.config)
            self.metagraph = self.subtensor.metagraph(self.config.netuid)

            # Each key has a unique identity (UID) in the network for differentiation.
            self.uid = self.metagraph.hotkeys.index(self.wallet.hotkey.ss58_address)
            bt.logging.info(
                f"Running neuron on subnet: {self.config.netuid} with uid {self.uid} using network: {self.subtensor.chain_endpoint}"
            )

        bt.logging.info(f"Wallet: {self.wallet}")
        bt.logging.info(f"Subtensor: {self.subtensor}")
        bt.logging.info(f"Metagraph: {self.metagraph}")

        # Check if the miner is registered on the Bittensor network before proceeding further.
        self.check_registered()

        self.step = 0

    @abstractmethod
    async def forward(self, synapse: bt.Synapse) -> bt.Synapse:
        ...

    @abstractmethod
    def run(self):
        ...

    def sync(self):
        """
        Synchronizes the neuron's state with the network.

        Performs the following tasks:
        1. Verifies registration status
        2. Syncs metagraph if necessary
        3. Sets weights if conditions are met
        4. Saves current state
        """
        # Ensure miner or validator hotkey is still registered on the network.
        self.check_registered()

        if self.should_sync_metagraph():
            self.resync_metagraph()

        if self.should_set_weights():
            self.set_weights()

        # Always save state.
        self.save_state()

    def check_registered(self):
        """
        Verifies that the neuron's hotkey is registered on the network.

        Raises:
            SystemExit: If the hotkey is not registered on the specified subnet
        """
        # --- Check for registration.
        if self.config.mock:
            return

        if not self.subtensor.is_hotkey_registered(
            netuid=self.config.netuid,
            hotkey_ss58=self.wallet.hotkey.ss58_address,
        ):
            bt.logging.error(
                f"Wallet: {self.wallet} is not registered on netuid {self.config.netuid}."
                f" Please register the hotkey using `btcli subnets register` before trying again"
            )
            exit()

    def should_sync_metagraph(self):
        """
        Determines if the metagraph should be synchronized.

        Returns:
            bool: True if enough blocks have elapsed since last sync, False otherwise
        """
        return (
            self.block - self.metagraph.last_update[self.uid]
        ) > self.config.neuron.metagraph_resync_length

    def should_set_weights(self) -> bool:
        """
        Determines if the neuron should set weights on the network.

        Returns:
            bool: True if weights should be set, False otherwise
        """
        # Don't set weights on initialization.
        if self.step == 0:
            return False

        # Check if enough epoch blocks have elapsed since the last epoch.
        if self.config.neuron.disable_set_weights:
            return False

        # Do not allow weight setting if the neuron is not a validator.
        if not self.metagraph.validator_permit[self.uid]:
            return False

        # Define appropriate logic for when set weights.
        return (
            self.block - self.metagraph.last_update[self.uid]
        ) > self.config.neuron.epoch_length

    def run_in_background_thread(self):
        """
        Starts the neuron's operations in a background thread.

        The thread runs as a daemon, allowing the program to exit when the main thread ends.
        """
        if not self.is_running:
            bt.logging.debug("Starting in background thread.")
            self.should_exit = False
            self.thread = threading.Thread(target=self.run, daemon=True)
            self.thread.start()
            self.is_running = True
            bt.logging.debug("Started")

    def stop_run_thread(self):
        """
        Stops the neuron's background operations.

        Attempts to gracefully stop the background thread with a 5-second timeout.
        """
        if self.is_running:
            bt.logging.debug("Stopping in background thread.")
            self.should_exit = True
            self.thread.join(5)
            self.is_running = False
            bt.logging.debug("Stopped")

    def __enter__(self):
        """
        Context manager entry point.

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError

    async def __aenter__(self):
        """
        Asynchronous context manager entry point.

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Context manager exit point.

        Args:
            exc_type: Type of the exception that caused the context to be exited
            exc_value: Instance of the exception that caused the context to be exited
            traceback: Traceback if an exception occurred

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError

    async def __aexit__(self, exc_type, exc_value, traceback):
        """
        Asynchronous context manager exit point.

        Args:
            exc_type: Type of the exception that caused the context to be exited
            exc_value: Instance of the exception that caused the context to be exited
            traceback: Traceback if an exception occurred

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError

    def save_state(self):
        """
        Saves the current state of the neuron.

        This is an empty implementation that can be overridden by subclasses
        to save model checkpoints or other state information.
        """
        pass

    def load_state(self):
        """
        Loads the previously saved state of the neuron.

        This is a placeholder implementation that logs a warning. Subclasses
        should override this method to load their specific state information.
        """
        bt.logging.warning(
            "load_state() not implemented for this neuron. You can implement this function to load model checkpoints or other useful data."
        )
