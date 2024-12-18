import asyncio
from abc import ABC, abstractmethod
from typing import Any, Literal, Optional, Sequence, Union, Tuple

import bittensor as bt

from atom.organic_scoring.organic_queue import OrganicQueue, OrganicQueueBase
from atom.organic_scoring.synth_dataset import SynthDatasetBase
from atom.organic_scoring.utils import is_overridden


"""
Base module for organic scoring mechanisms in the Atom framework.

This module provides the foundation for implementing organic scoring systems,
which combine both synthetic and organic data processing for reward calculation
and weight adjustment in the network.
"""


class OrganicScoringBase(ABC):
    """
    Abstract base class for organic scoring implementations.

    This class provides the framework for processing both organic and synthetic data,
    managing scoring frequencies, and handling weight updates in the network. It runs
    asynchronously and can be triggered either by time intervals or step counts.

    Args:
        axon (bt.axon): The axon instance for network communication.
        synth_dataset (Optional[Union[SynthDatasetBase, Sequence[SynthDatasetBase]]]): 
            Synthetic dataset(s) for training. If None, only organic data will be used.
        trigger_frequency (Union[float, int]): Frequency of organic scoring reward steps.
        trigger (Literal["seconds", "steps"]): Trigger type for scoring:
            - "seconds": Wait specified number of seconds between steps
            - "steps": Wait specified number of steps between updates
        trigger_frequency_min (Union[float, int], optional): Minimum frequency value.
            Defaults to 2.
        trigger_scaling_factor (Union[float, int], optional): Scaling factor for
            adjusting trigger frequency based on queue size. Higher values mean slower
            adjustment. Must be > 0. Defaults to 5.
        organic_queue (Optional[OrganicQueueBase], optional): Queue for storing organic
            samples. Defaults to OrganicQueue.

    Attributes:
        _axon: The axon instance used for network communication.
        _should_exit: Flag indicating if the scoring loop should terminate.
        _is_running: Flag indicating if the scoring loop is active.
        _synth_dataset: Collection of synthetic datasets.
        _trigger_frequency: Base frequency for triggering scoring steps.
        _trigger: Type of trigger mechanism used.
        _trigger_min: Minimum allowed trigger frequency.
        _trigger_scaling_factor: Factor for dynamic frequency adjustment.
        _organic_queue: Queue storing organic samples.
        _step_counter: Counter for step-based triggering.
        _step_lock: Lock for thread-safe step counter operations.
    """

    def __init__(
        self,
        axon: bt.axon,
        synth_dataset: Optional[Union[SynthDatasetBase, Sequence[SynthDatasetBase]]],
        trigger_frequency: Union[float, int],
        trigger: Literal["seconds", "steps"],
        trigger_frequency_min: Union[float, int] = 2,
        trigger_scaling_factor: Union[float, int] = 5,
        organic_queue: Optional[OrganicQueueBase] = None,
    ):
        """Runs the organic weight setter task in separate threads.

        Args:
            axon: The axon to use, must be started and served.
            synth_dataset: The synthetic dataset(s) to use, must be inherited from `synth_dataset.SynthDatasetBase`.
                If None, only organic data will be used, when available.
            trigger_frequency: The frequency to trigger the organic scoring reward step.
            trigger: The trigger type, available values: "seconds", "steps".
                In case of "seconds" the `trigger_frequency` is the number of seconds to wait between each step.
                In case of "steps" the `trigger_frequency` is the number of steps to wait between each step. The
                `increment_step` method should be called to increment the step counter.
            organic_queue: The organic queue to use, must be inherited from `organic_queue.OrganicQueueBase`.
                Defaults to `organic_queue.OrganicQueue`.
            trigger_frequency_min: The minimum frequency value to trigger the organic scoring reward step.
                Defaults to 1.
            trigger_scaling_factor: The scaling factor to adjust the trigger frequency based on the size
                of the organic queue. A higher value means that the trigger frequency adjusts more slowly to changes
                in the organic queue size. This value must be greater than 0.

        Override the following methods:
            - `forward`: Method to establish the sampling logic for the organic scoring task.
            - `_on_organic_entry`: Handle an organic entry, append required values to `_organic_queue`.
                Important: this method must add the required values to the `_organic_queue`.
            - `_query_miners`: Query the miners with a given organic sample.
            - `_set_weights`: Set the weights based on generated rewards for the miners.
            - (Optional) `_priority_fn`: Function with priority value for organic handles.
            - (Optional) `_blacklist_fn`: Function with blacklist for organic handles.
            - (Optional) `_verify_fn`: Function to verify requests for organic handles.

        Usage:
            1. Create a subclass of OrganicScoringBase.
            2. Implement the required methods.
            3. Create an instance of the subclass.
            4. Call the `start` method to start the organic scoring task.
            5. Call the `stop` method to stop the organic scoring task.
            6. Call the `increment_step` method to increment the step counter if the trigger is set to "steps".
        """
        self._axon = axon
        self._should_exit = False
        self._is_running = False
        self._synth_dataset = synth_dataset

        if isinstance(self._synth_dataset, SynthDatasetBase):
            self._synth_dataset = (synth_dataset,)

        self._trigger_frequency = trigger_frequency
        self._trigger = trigger
        self._trigger_min = trigger_frequency_min
        self._trigger_scaling_factor = trigger_scaling_factor

        assert (
            self._trigger_scaling_factor > 0
        ), "The scaling factor must be higher than 0."

        self._organic_queue = organic_queue

        if self._organic_queue is None:
            self._organic_queue = OrganicQueue()

        self._step_counter = 0
        self._step_lock = asyncio.Lock()

        # Bittensor's internal checks require synapse to be a subclass of bt.Synapse.
        # If the methods are not overridden in the derived class, None is passed.
        self._axon.attach(
            forward_fn=self._on_organic_entry,
            blacklist_fn=(
                self._blacklist_fn if is_overridden(self._blacklist_fn) else None
            ),
            priority_fn=self._priority_fn if is_overridden(self._priority_fn) else None,
            verify_fn=self._verify_fn if is_overridden(self._verify_fn) else None,
        )

    def increment_step(self):
        """Increment the step counter if the trigger is set to `steps`."""
        with self._step_lock:
            if self._trigger == "steps":
                self._step_counter += 1

    def set_step(self, step: int):
        """Set the step counter to a specific value.

        Args:
            step: The step value to set.
        """
        with self._step_lock:
            if self._trigger == "steps":
                self._step_counter = step

    @abstractmethod
    async def _on_organic_entry(self, synapse: bt.Synapse) -> bt.Synapse:
        """
        Process an incoming organic sample.

        This abstract method must be implemented by subclasses to handle incoming
        organic samples and add them to the organic queue.

        Args:
            synapse (bt.Synapse): The incoming synapse containing the organic sample.

        Returns:
            bt.Synapse: The processed synapse.

        Note:
            Implementations MUST add required values to self._organic_queue.
        """
        raise NotImplementedError

    async def _priority_fn(self, synapse: bt.Synapse) -> float:
        """
        Calculate priority for organic sample processing.

        Args:
            synapse (bt.Synapse): The synapse to evaluate.

        Returns:
            float: Priority value, higher values indicate higher priority.
                Defaults to 0.0.
        """
        return 0.0

    async def _blacklist_fn(self, synapse: bt.Synapse) -> Tuple[bool, str]:
        """
        Determine if a synapse should be blacklisted.

        Args:
            synapse (bt.Synapse): The synapse to evaluate.

        Returns:
            Tuple[bool, str]: A tuple containing:
                - bool: True if blacklisted, False otherwise
                - str: Reason for blacklisting (empty if not blacklisted)
        """
        return False, ""

    async def _verify_fn(self, synapse: bt.Synapse) -> bool:
        """
        Verify if a synapse request is valid.

        Args:
            synapse (bt.Synapse): The synapse to verify.

        Returns:
            bool: True if the request is valid, False otherwise.
        """
        return True

    async def start_loop(self):
        """
        Main execution loop for the organic scoring task.

        This asynchronous loop runs continuously until _should_exit is set to True.
        It handles both time-based and step-based triggering mechanisms, executing
        the forward pass and managing the waiting period between iterations.

        The loop:
        1. Checks trigger conditions (time or steps)
        2. Executes the forward pass
        3. Calculates the next waiting period
        4. Handles any exceptions during execution

        Raises:
            Logs errors that occur during execution but doesn't terminate the loop.
        """
        while not self._should_exit:
            if self._trigger == "steps":
                while self._step_counter < self._trigger_frequency:
                    await asyncio.sleep(0.1)

            try:
                logs = await self.forward()

                total_elapsed_time = logs.get("total_elapsed_time", 0)
                await self.wait_until_next(timer_elapsed=total_elapsed_time)

            except Exception as e:
                bt.logging.error(
                    f"Error occured during organic scoring iteration:\n{e}"
                )
                await asyncio.sleep(1)

    @abstractmethod
    async def forward(self) -> dict[str, Any]:
        """
        Method to establish the sampling logic for the organic scoring task.
        Sample data from the organic queue or the synthetic dataset (if available).

        Expected to return a dictionary with information from the sampling method.
        If the trigger is based on seconds, the dictionary should contain the key "total_elapsed_time".
        """
        ...

    async def wait_until_next(self, timer_elapsed: float = 0):
        """
        Dynamically adjust and wait for the next iteration based on queue size.

        Implements an adaptive waiting mechanism that adjusts the sampling rate
        based on the current size of the organic queue. This ensures efficient
        processing as the queue size changes.

        Args:
            timer_elapsed (float, optional): Time spent in the current processing
                iteration. Used for time-based triggers. Defaults to 0.

        Dynamic Adjustment Formula:
            - For time-based triggers: 
              wait_time = max(base_frequency - (queue_size / scaling_factor), min_frequency)
            - For step-based triggers:
              steps = int(max(base_steps - (queue_size / scaling_factor), min_steps))
        """
        # Annealing sampling rate logic.
        dynamic_unit = self.sample_rate_dynamic()
        if self._trigger == "seconds":
            # Adjust the sleep duration based on the queue size.
            sleep_duration = max(dynamic_unit - timer_elapsed, 0)
            await asyncio.sleep(sleep_duration)
        elif self._trigger == "steps":
            # Adjust the steps based on the queue size.
            while True:
                if self._step_counter >= dynamic_unit:
                    self._step_counter -= dynamic_unit
                else:
                    await asyncio.sleep(1)

    def sample_rate_dynamic(self) -> float:
        """
        Calculate the dynamic sampling rate based on organic queue size.

        Returns:
            float: The adjusted sampling rate. For time-based triggers, returns
                seconds to wait. For step-based triggers, returns the number of
                steps (as an integer).

        Formula:
            rate = max(trigger_frequency - (queue_size / scaling_factor), trigger_min)
        """
        size = self._organic_queue.size
        delay = max(
            self._trigger_frequency - (size / self._trigger_scaling_factor),
            self._trigger_min,
        )
        return delay if self._trigger == "seconds" else int(delay)
