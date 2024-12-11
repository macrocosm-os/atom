import pytest
from atom.mock.mock_identities import MockMiner, MockValidator


# Ensure that the miner and validator classes can be instantiated.
def test_base_miner_neuron():
    miner = MockMiner()
    validator = MockValidator()
