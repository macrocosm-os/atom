from abc import ABC, abstractmethod
from typing import Any


class OrganicQueueBase(ABC):
    """Base organic queue.

    The following methods must be implemented:
        - add: Add the sample to the queue;
        - sample: Pop the sample from the queue;
        - size: Return the size of the queue.
    """

    @abstractmethod
    def add(self, sample: Any):
        """Add the sample to the queue."""
        raise NotImplementedError

    @abstractmethod
    def sample(self) -> Any:
        """Pop the sample from the queue."""
        raise NotImplementedError

    @property
    @abstractmethod
    def size(self) -> int:
        raise NotImplementedError

    def __len__(self) -> int:
        return self.size

    def is_empty(self) -> bool:
        return self.size == 0
