# The MIT License (MIT)
# Copyright © 2024 Macrocosmos AI

import copy
import torch
import asyncio
import argparse
import threading
import bittensor as bt
from typing import List
from abc import abstractmethod

from atom.mock.mock import MockDendrite
from atom.base.neuron import BaseNeuron
from atom.base.config import add_validator_args


class BaseValidatorNeuron(BaseNeuron):
    """
    Base class for Bittensor validators.

    This class provides the fundamental structure and functionality for validators in the Bittensor network.
    It handles network synchronization, weight setting, and score management for miners in the network.

    Attributes:
        hotkeys (List[str]): Copy of metagraph hotkeys for local reference
        dendrite (bt.dendrite): Interface for sending messages to other nodes
        scores (torch.FloatTensor): Scoring weights for validation
        should_exit (bool): Flag indicating if validator should stop
        is_running (bool): Flag indicating if validator is currently running
        thread (threading.Thread): Background thread for validator operations
        lock (asyncio.Lock): Lock for thread-safe operations
    """

    @classmethod
    def add_args(cls, parser: argparse.ArgumentParser):
        """
        Adds validator-specific arguments to the command line parser.

        Args:
            parser (argparse.ArgumentParser): The argument parser to add arguments to.
        """
        super().add_args(parser)
        add_validator_args(cls, parser)

    def __init__(self, config=None):
        """
        Initializes the BaseValidatorNeuron.

        Args:
            config: Configuration object containing validator settings. Defaults to None.
        """
        super().__init__(config=config)

        # Save a copy of the hotkeys to local memory.
        self.hotkeys = copy.deepcopy(self.metagraph.hotkeys)

        # Dendrite lets us send messages to other nodes (axons) in the network.
        if self.config.mock:
            self.dendrite = MockDendrite(wallet=self.wallet)
        else:
            self.dendrite = bt.dendrite(wallet=self.wallet)
        bt.logging.info(f"Dendrite: {self.dendrite}")

        # Set up initial scoring weights for validation
        bt.logging.info("Building validation weights.")
        self.scores = torch.zeros(
            self.metagraph.n, dtype=torch.float32, device=self.device
        )

        # Initial sync with the network. Updates the metagraph.
        self.sync()

        # Serve axon to enable external connections. axon attachments need to be configured.
        if not self.config.neuron.axon_off:
            self.axon = bt.axon(wallet=self.wallet, config=self.config)
            self.serve_axon()
        else:
            bt.logging.warning("axon off, not serving ip to chain.")

        # Create asyncio event loop to manage async tasks.
        self.loop = asyncio.get_event_loop()

        # Instantiate runners
        self.should_exit: bool = False
        self.is_running: bool = False
        self.thread: threading.Thread = None
        self.lock = asyncio.Lock()

    async def async_updater(self):
        """
        Asynchronous update loop for the validator.

        This method runs continuously in the background, performing the following tasks:
        1. Synchronizes the metagraph with the network
        2. Sets validator weights
        3. Saves the validator state
        4. Waits for the configured epoch length before the next update
        """
        bt.logging.info("starting the sync_loop")
        while True:
            self.sync()
            SECONDS_PER_BLOCK = 12
            await asyncio.sleep(self.config.neuron.epoch_length * SECONDS_PER_BLOCK)

    def serve_axon(self):
        """
        Serves the validator's axon to enable external connections.

        Attempts to start the axon service on the specified network UID.
        Logs an error if the axon fails to start.
        """
        try:
            self.axon.serve(netuid=self.config.netuid, subtensor=self.subtensor).start()
        except Exception as e:
            bt.logging.error(f"Failed to serve axon: {e}")

    def run(self):
        """
        Starts the validator's operations.

        Returns:
            BaseValidatorNeuron: The validator instance.
        """
        return self

    def __enter__(self):
        self.run()
        return self

    async def __aenter__(self):
        """
        Asynchronous context manager entry point.

        Creates and starts the background update task for the validator.

        Returns:
            BaseValidatorNeuron: The validator instance.
        """
        bt.logging.debug("Starting validator in background thread.")
        self.loop.create_task(self.async_updater())
        self.is_running = True
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Stops the validator's background operations upon exiting the context.

        Args:
            exc_type: The type of the exception that caused the context to be exited.
            exc_value: The instance of the exception that caused the context to be exited.
            traceback: A traceback object encoding the stack trace.
        """
        if self.is_running:
            bt.logging.debug("Stopping validator in background thread.")
            self.should_exit = True
            self.thread.join(5)
            self.is_running = False
            bt.logging.debug("Stopped")

    def resync_metagraph(self):
        """
        Resyncs the metagraph and updates the hotkeys and scores.

        This method:
        1. Creates a copy of the current metagraph state
        2. Syncs with the network to get the latest state
        3. Updates scores for any replaced hotkeys
        4. Adjusts the size of scoring tensors if the network has grown
        5. Updates the local hotkey cache
        """
        bt.logging.info("resync_metagraph()")

        # Copies state of metagraph before syncing.
        previous_metagraph = copy.deepcopy(self.metagraph)

        # Sync the metagraph.
        self.metagraph.sync(subtensor=self.subtensor)

        # Check if the metagraph axon info has changed.
        if previous_metagraph.axons == self.metagraph.axons:
            return

        bt.logging.info(
            "Metagraph updated, re-syncing hotkeys, dendrite pool and moving averages"
        )
        # Zero out all hotkeys that have been replaced.
        for uid, hotkey in enumerate(self.hotkeys):
            if hotkey != self.metagraph.hotkeys[uid]:
                self.scores[uid] = 0  # hotkey has been replaced

        # Check to see if the metagraph has changed size.
        # If so, we need to add new hotkeys and moving averages.
        if len(self.hotkeys) < len(self.metagraph.hotkeys):
            # Update the size of the moving average scores.
            new_moving_average = torch.zeros((self.metagraph.n)).to(self.device)
            min_len = min(len(self.hotkeys), len(self.scores))
            new_moving_average[:min_len] = self.scores[:min_len]
            self.scores = new_moving_average

        # Update the hotkeys.
        self.hotkeys = copy.deepcopy(self.metagraph.hotkeys)

    def save_state(self):
        """
        Saves the validator's state to a file.

        Saves the following information:
        - Current step
        - Validation scores
        - Hotkey list
        """
        bt.logging.info("Saving validator state.")

        # Save the state of the validator to file.
        torch.save(
            {
                "step": self.step,
                "scores": self.scores,
                "hotkeys": self.hotkeys,
            },
            self.config.neuron.full_path + "/state.pt",
        )

    def load_state(self):
        """
        Loads the validator's state from a file.

        Attempts to load:
        - Step count
        - Validation scores
        - Hotkey list

        If no state file exists, starts with fresh state.
        """
        try:
            state = torch.load(self.config.neuron.full_path + "/state.pt")
            self.step = state["step"]
            self.scores = state["scores"]
            self.hotkeys = state["hotkeys"]
            bt.logging.info("Loaded previously saved validator state information.")
        except:
            bt.logging.info(
                "Previous validator state not found... Starting from scratch"
            )

    @abstractmethod
    def set_weights(self):
        """
        Sets the validator weights for the network.

        This abstract method must be implemented by subclasses to define how
        the validator assigns trust and incentive weights to miners based on
        their performance scores.
        """
        raise NotImplementedError

    @abstractmethod
    def update_scores(self, rewards: torch.FloatTensor, uids: List[int]):
        """
        Updates the scores for miners using exponential moving average.

        Args:
            rewards (torch.FloatTensor): The rewards tensor for miners
            uids (List[int]): List of miner UIDs corresponding to the rewards

        This abstract method must be implemented by subclasses to define how
        the validator updates its scoring mechanism based on miner performance.
        """
        raise NotImplementedError
