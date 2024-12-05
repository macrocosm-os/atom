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
    def __init__(self, config=None):
        config = create_config(self)
        config.mock = True

        super().__init__(config)

    def spec_version(self):
        return spec_version

    def forward(self, synapse: bt.Synapse) -> bt.Synapse:
        return None

    def blacklist(self, synapse: bt.Synapse) -> Tuple[bool, str]:
        return False, ""

    def priority(self, synapse: bt.Synapse) -> float:
        return 0.0


class MockValidator(BaseValidatorNeuron):
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
        return None

    def spec_version(self):
        return spec_version

    def forward(self, synapse: bt.Synapse) -> bt.Synapse:
        return None

    def blacklist(self, synapse: bt.Synapse) -> Tuple[bool, str]:
        return False, ""

    def priority(self, synapse: bt.Synapse) -> float:
        return 0.0

    # The following methods are not implemented in the mock classes, so they should return False.
    def should_set_weights(self):
        return False

    def should_sync_metagraph(self):
        return False
    
    def set_weights(self):
        return False
    
    def update_scores(self):
        return False


class MockOrganicValidator(OrganicScoringBase):
    """Validator class to handle organic entries."""

    def __init__(
        self,
        axon: bt.axon,
        trigger_frequency: Union[float, int],
        trigger: Literal["seconds", "steps"],
        trigger_frequency_min: Union[float, int] = 5,
        trigger_scaling_factor: Union[float, int] = 5,
        synth_dataset=None,
    ):
        super().__init__(
            axon=axon,
            synth_dataset=synth_dataset,
            trigger_frequency=trigger_frequency,
            trigger=trigger,
            trigger_frequency_min=trigger_frequency_min,
            trigger_scaling_factor=trigger_scaling_factor,
        )

    async def _on_organic_entry(self, synapse: bt.Synapse) -> bt.Synapse:
        return synapse

    async def start_loop(self):
        """
        The main loop for running the organic scoring task, either based on a time interval or steps.
        Calls the `sample` method to establish the sampling logic for the organic scoring task.
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
        """Sample data from the organic queue or the synthetic dataset.

        Returns:
            dict[str, Any]: dict that contains all the attributes for creating a simulation object.
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
        """The forward method is responsible for sampling data from the organic queue,
        and adding it to the local database of the validator.
        """
        sample: dict[str, Any] = await self.sample()
        return sample

    def _blacklist_fn(self, synapse: bt.Synapse) -> Tuple[bool, str]:
        return False, ""
