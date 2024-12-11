from atom.organic_scoring.organic_queue import OrganicQueue
from atom.mock.mock_identities import MockValidator


# Ensure that the organic queue can be instantiated and used.
def test_organic_queue():
    queue = OrganicQueue()
    assert queue.size == 0

    queue.add({"a": 1})
    assert queue.size == 1

    sample = queue.sample()
    assert sample == {"a": 1}

    assert queue.size == 0


# Ensure that the organic validator class can be instantiated.
def test_organic_validator():
    organic_config = {"trigger_frequency": 1, "trigger": "steps"}
    organic_validator = MockValidator(organic_config=organic_config)
