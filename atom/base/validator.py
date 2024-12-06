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
    Base class for Bittensor validators. Your validator should inherit from this class.
    """

    @classmethod
    def add_args(cls, parser: argparse.ArgumentParser):
        super().add_args(parser)
        add_validator_args(cls, parser)

    def __init__(self, config=None):
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
        """Intended to be run as an async entrypoint for the validator to:
        1. Sync the metagraph.
        2. Set the weights.
        3. Save the state of the validator.
        """
        bt.logging.info("starting the sync_loop")
        while True:
            self.sync()
            SECONDS_PER_BLOCK = 12
            await asyncio.sleep(self.config.neuron.epoch_length * SECONDS_PER_BLOCK)

    def serve_axon(self):
        """Serve axon to enable external connections"""
        try:
            self.axon.serve(netuid=self.config.netuid, subtensor=self.subtensor).start()
        except Exception as e:
            bt.logging.error(f"Failed to serve axon: {e}")

    def run(self):
        return self 

    def __enter__(self):
        self.run()
        return self

    async def __aenter__(self):
        """
        Entry point for the validator to start running in the background.
        Indended to be overwritten by the user, as this is an example.
        """
        bt.logging.debug("Starting validator in background thread.")
        self.loop.create_task(self.async_updater())
        self.is_running = True
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Stops the validator's background operations upon exiting the context.
        This method facilitates the use of the validator in a 'with' statement.

        Args:
            exc_type: The type of the exception that caused the context to be exited.
                      None if the context was exited without an exception.
            exc_value: The instance of the exception that caused the context to be exited.
                       None if the context was exited without an exception.
            traceback: A traceback object encoding the stack trace.
                       None if the context was exited without an exception.
        """
        if self.is_running:
            bt.logging.debug("Stopping validator in background thread.")
            self.should_exit = True
            self.thread.join(5)
            self.is_running = False
            bt.logging.debug("Stopped")

    def resync_metagraph(self):
        """Resyncs the metagraph and updates the hotkeys and moving averages based on the new metagraph."""
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
        """Saves the state of the validator to a file."""
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
        """Loads the state of the validator from a file."""
        try:
            state = torch.load(self.config.neuron.full_path + "/state.pt")
            self.step = state["step"]
            self.scores = state["scores"]
            self.hotkeys = state["hotkeys"]
            bt.logging.info("Loaded previously saved validator state information.")
        except:
            bt.logging.info("Previous validator state not found... Starting from scratch")

    @abstractmethod
    def set_weights(self):
        """Sets the validator weights to the metagraph hotkeys based on the scores it has received from the miners. 
        The weights determine the trust and incentive level the validator assigns to miner nodes on the network."""
        raise NotImplementedError

    @abstractmethod
    def update_scores(self, rewards: torch.FloatTensor, uids: List[int]):
        """Performs exponential moving average on the scores based on the rewards received from the miners."""
        raise NotImplementedError