"""
A module implementing a basic organic queue data structure for sample management.

The organic queue is a fixed-size queue that stores samples and provides a sequential sampler. 
"""

import random
from typing import Any

from atom.organic_scoring.organic_queue.organic_queue_base import OrganicQueueBase


class OrganicQueue(OrganicQueueBase):
    """
    A basic organic queue implementation using a list as the underlying data structure.

    The queue maintains a maximum size and implements FIFO behavior when the size limit
    is reached. Samples can be randomly retrieved from any position in the queue.

    Args:
        max_size (int): Maximum number of samples that can be stored in the queue.
            Defaults to 10000.

    Attributes:
        max_size (int): Maximum capacity of the queue.
        _queue (list): Internal list storing the samples.
    """

    def __init__(self, max_size: int = 10000):
        self._queue = []
        self.max_size = max_size

    def add(self, sample: Any):
        """
        Add a sample to the queue.

        If the queue is at maximum capacity, the oldest sample is removed before
        adding the new one (FIFO behavior).

        Args:
            sample (Any): The sample to be added to the queue.
        """
        if self.size >= self.max_size:
            self._queue.pop(0)
        self._queue.append(sample)

    def sample(self) -> Any:
        """
        Randomly sample and remove an item from the queue.

        Returns:
            Any: A randomly selected sample from the queue.
                Returns None if the queue is empty.
        """
        if self.is_empty():
            return None
        return self._queue.pop(random.randint(0, self.size - 1))

    @property
    def size(self) -> int:
        """
        Get the current number of samples in the queue.

        Returns:
            int: The current size of the queue.
        """
        return len(self._queue)
