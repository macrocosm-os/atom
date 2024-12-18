"""Mock implementation module for testing Bittensor neurons.

This module provides mock implementations of miner and validator neurons for testing purposes.
It includes basic implementations of required methods while maintaining minimal functionality.

Classes:
    MockMiner: A mock implementation of a miner neuron
    MockValidator: A mock implementation of a validator neuron
    MockOrganicValidator: A mock implementation of organic validation functionality
"""

import random
import asyncio
import bittensor as bt

from typing import Tuple, Any, Union, Literal, Dict
from atom.base.config import config as create_config

from atom.base.miner import BaseMinerNeuron
from atom.base.validator import BaseValidatorNeuron
from atom.organic_scoring.organic_scoring_base import OrganicScoringBase

from atom import __spec_version__ as spec_version


class MockMiner(BaseMinerNeuron):
    """Mock implementation of a miner neuron for testing.

    A simplified miner implementation that returns default values for all required methods.
    Useful for testing validator behavior without full miner functionality.

    Args:
        config: Configuration object for the miner. Defaults to None.
    """

    def __init__(self, config=None):
        config = create_config(self)
        config.mock = True

        super().__init__(config)

    def spec_version(self):
        """Get the specification version.

        Returns:
            str: The current specification version.
        """
        return spec_version

    def forward(self, synapse: bt.Synapse) -> bt.Synapse:
        """Mock forward pass implementation.

        Args:
            synapse: The input synapse object.

        Returns:
            bt.Synapse: Always returns None.
        """
        return None

    def blacklist(self, synapse: bt.Synapse) -> Tuple[bool, str]:
        """Mock blacklist check implementation.

        Args:
            synapse: The synapse to check.

        Returns:
            Tuple[bool, str]: Always returns (False, "").
        """
        return False, ""

    def priority(self, synapse: bt.Synapse) -> float:
        """Mock priority calculation implementation.

        Args:
            synapse: The synapse to evaluate.

        Returns:
            float: Always returns 0.0.
        """
        return 0.0


class MockValidator(BaseValidatorNeuron):
    """Mock implementation of a validator neuron for testing.

    A simplified validator implementation that returns default values for all required methods.
    Includes a mock organic validator component.

    Args:
        config: Configuration object for the validator. Defaults to None.
        organic_config (Dict[str, Any]): Configuration for the organic validator component.
    """

    def __init__(
        self,
        config=None,
        organic_config: Dict[str, Any] = {"trigger_frequency": 1, "trigger": "steps"},
    ):
        config = create_config(self)
        config.mock = True

        super().__init__(config)

        self.organic_validator = MockOrganicValidator(axon=self.axon, **organic_config)

    def run(self):
        """Mock run implementation.

        Returns:
            None: Always returns None.
        """
        return None

    def spec_version(self):
        """Get the specification version.

        Returns:
            str: The current specification version.
        """
        return spec_version

    def forward(self, synapse: bt.Synapse) -> bt.Synapse:
        """Mock forward pass implementation.

        Args:
            synapse: The input synapse object.

        Returns:
            bt.Synapse: Always returns None.
        """
        return None

    def blacklist(self, synapse: bt.Synapse) -> Tuple[bool, str]:
        """Mock blacklist check implementation.

        Args:
            synapse: The synapse to check.

        Returns:
            Tuple[bool, str]: Always returns (False, "").
        """
        return False, ""

    def priority(self, synapse: bt.Synapse) -> float:
        """Mock priority calculation implementation.

        Args:
            synapse: The synapse to evaluate.

        Returns:
            float: Always returns 0.0.
        """
        return 0.0

    def should_set_weights(self):
        """Mock weight setting check.

        Returns:
            bool: Always returns False.
        """
        return False

    def should_sync_metagraph(self):
        """Mock metagraph sync check.

        Returns:
            bool: Always returns False.
        """
        return False

    def set_weights(self):
        """Mock weight setting implementation.

        Returns:
            bool: Always returns False.
        """
        return False

    def update_scores(self):
        """Mock score update implementation.

        Returns:
            bool: Always returns False.
        """
        return False


class MockOrganicValidator(OrganicScoringBase):
    """Mock implementation of organic validation functionality.

    Provides a basic implementation of organic validation for testing purposes.

    Args:
        axon (bt.axon): The axon instance to use.
        trigger_frequency (Union[float, int]): Frequency of organic validation triggers.
        trigger (Literal["seconds", "steps"]): Type of trigger to use.
        trigger_frequency_min (Union[float, int]): Minimum trigger frequency.
        trigger_scaling_factor (Union[float, int]): Scaling factor for triggers.
        synth_dataset: Optional synthetic dataset for testing.
    """

    async def _on_organic_entry(self, synapse: bt.Synapse) -> bt.Synapse:
        """Mock organic entry handler.

        Args:
            synapse: The input synapse object.

        Returns:
            bt.Synapse: Returns the input synapse unchanged.
        """
        return synapse

    async def start_loop(self):
        """Main loop for organic scoring task.

        Implements a basic loop that handles organic scoring based on time or step triggers.
        """
        while not self._should_exit:
            if self._trigger == "steps":
                while self._step_counter < self._trigger_frequency:
                    await asyncio.sleep(0.1)

            try:
                await self.forward()

            except Exception as e:
                bt.logging.error(
                    f"Error occured during organic scoring iteration:\n{e}"
                )
                await asyncio.sleep(0.1)

    async def sample(self) -> dict[str, Any]:
        """Sample data from organic queue or synthetic dataset.

        Returns:
            dict[str, Any]: A sample containing attributes for simulation.
        """
        if not self._organic_queue.is_empty():
            # Choose organic sample based on the organic queue logic.
            sample = self._organic_queue.sample()
        elif self._synth_dataset is not None:
            # Choose if organic queue is empty, choose random sample from provided datasets.
            sample = random.choice(self._synth_dataset).sample()
        else:
            sample = None

        return sample

    async def forward(self) -> dict[str, Any]:
        """Process organic queue entries.

        Returns:
            dict[str, Any]: The sampled data.
        """
        sample: dict[str, Any] = await self.sample()
        return sample

    def _blacklist_fn(self, synapse: bt.Synapse) -> Tuple[bool, str]:
        """Mock blacklist function implementation.

        Args:
            synapse: The synapse to check.

        Returns:
            Tuple[bool, str]: Always returns (False, "").
        """
        return False, ""
