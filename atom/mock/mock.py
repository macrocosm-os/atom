"""Mock module for Bittensor testing environment.

This module provides mock implementations of core Bittensor components for testing purposes.
It includes mock versions of wallet, subtensor, metagraph, and dendrite classes that simulate
the behavior of their real counterparts without actual blockchain interaction.

Key Features:
    - Mock wallet creation and management
    - Simulated subtensor environment
    - Mock metagraph for network topology testing
    - Mock dendrite for testing network requests
"""

import bittensor as bt


def create_wallet():
    """Creates a mock wallet for testing purposes.

    Creates a new wallet with predefined test keys for consistent testing environment.

    Returns:
        bt.wallet: A mock wallet instance with test coldkey and hotkey.
    """
    wallet = bt.wallet(name="test_coldkey", hotkey="test_hotkey")
    wallet.create_if_non_existent()
    return wallet


class MockSubtensor(bt.MockSubtensor):
    """Mock implementation of the Subtensor network.

    Simulates basic blockchain functionality for testing purposes.

    Args:
        netuid (int): Network UID to operate on
        n (int, optional): Number of nodes in the network. Defaults to 16
        wallet (bt.wallet, optional): Wallet to use for operations
        network (str, optional): Network name. Defaults to "mock"
    """

    def __init__(self, netuid, n=16, wallet=None, network="mock"):
        """Initialize the mock subtensor instance.

        Creates a new subnet if it doesn't exist for the given netuid.
        """
        super().__init__(network=network)

        if not self.subnet_exists(netuid):
            self.create_subnet(netuid)


class MockMetagraph(bt.metagraph):
    """Mock implementation of the Bittensor metagraph.

    Provides a simulated network topology for testing validator and miner interactions.

    Args:
        netuid (int, optional): Network UID to operate on. Defaults to 1
        network (str, optional): Network name. Defaults to "mock"
        subtensor (MockSubtensor, optional): Subtensor instance to use
    """

    def __init__(self, netuid=1, network="mock", subtensor=None):
        """Initialize the mock metagraph instance.

        Sets up a basic network topology with mock axons using localhost addresses.
        """
        super().__init__(netuid=netuid, network=network, sync=False)

        if subtensor is not None:
            self.subtensor = subtensor
        self.sync(subtensor=subtensor)

        for axon in self.axons:
            axon.ip = "127.0.0.0"
            axon.port = 8091

        bt.logging.info(f"Metagraph: {self}")
        bt.logging.info(f"Axons: {self.axons}")


class MockDendrite(bt.dendrite):
    """Mock implementation of the Bittensor dendrite.

    Simulates network requests for testing purposes without actual network communication.

    Args:
        wallet (bt.wallet): Wallet to use for operations
    """

    def __init__(self, wallet):
        """Initialize the mock dendrite instance."""
        super().__init__(wallet)

    def __str__(self) -> str:
        """Get string representation of the mock dendrite.

        Returns:
            str: String representation in format "MockDendrite(<wallet_address>)".
        """
        return "MockDendrite({})".format(self.keypair.ss58_address)

    async def forward(self):
        """Simulate a forward pass through the network.

        Returns:
            None: Currently returns None as placeholder.

        Todo:
            Implement mock forward functionality.
        """
        # TODO: Implement this function
        return None
