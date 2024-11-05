from abc import ABC, abstractmethod
from typing import Any


class SynthDatasetBase(ABC):
    @abstractmethod
    def sample(self) -> Any:
        raise NotImplementedError
