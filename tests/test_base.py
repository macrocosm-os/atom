import pytest
from atom.mock.mock_identities import MockMiner, MockValidator


def test_base_miner_neuron():
    miner = MockMiner()
    validator = MockValidator()
