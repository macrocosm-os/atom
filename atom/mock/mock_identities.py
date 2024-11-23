import bittensor as bt 

from typing import Tuple
from atom.base.config import config as create_config 

from atom.base.miner import BaseMinerNeuron
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