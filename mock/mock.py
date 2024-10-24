import bittensor as bt


class MockSubtensor(bt.MockSubtensor):
    def __init__(self, netuid, n=16, wallet=None, network="mock"):
        super().__init__(network=network)

        if not self.subnet_exists(netuid):
            self.create_subnet(netuid)

        # Register ourself (the validator) as a neuron at uid=0
        if wallet is not None:
            self.force_register_neuron(
                netuid=netuid,
                hotkey=wallet.hotkey.ss58_address,
                coldkey=wallet.coldkey.ss58_address,
                balance=100000,
                stake=100000,
            )

        # Register n mock neurons who will be miners
        for i in range(1, n + 1):
            self.force_register_neuron(
                netuid=netuid,
                hotkey=f"miner-hotkey-{i}",
                coldkey="mock-coldkey",
                balance=100000,
                stake=100000,
            )


class MockMetagraph(bt.metagraph):
    def __init__(self, netuid=1, network="mock", subtensor=None):
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
    """
    Replaces a real bittensor network request with a mock request that just returns some static completion for all axons that are passed and adds some random delay.
    """

    def __init__(self, wallet):
        super().__init__(wallet)

    def __str__(self) -> str:
        """
        Returns a string representation of the Dendrite object.

        Returns:
            str: The string representation of the Dendrite object in the format "dendrite(<user_wallet_address>)".
        """
        return "MockDendrite({})".format(self.keypair.ss58_address)

    async def forward(self):
        # TODO: Implement this function
        return None
