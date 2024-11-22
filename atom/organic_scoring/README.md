# Generic Implementation of Organic Scoring for Bittensor Subnets

This implementation provides a generic solution for integrating organic scoring into a Bittensor subnets. 

By *organic*, we mean that the validator is able to accept a query from an outside source, and distribute this query as a task to the network. In the case of something like a chat interface, this means a user provides an *organic* question to be sent to the network. 

## Functionality Overview
Generally, designing your subnet around the ability to accept organic queries should happen early in its life-cycle. Incorporating the infrastructure early will help you avoid unnecessary refactoring later. 

This section of the repo provides an `OrganicScoringBase` class that handles key abstractions:

- **Organic Query Handling**: Manages organic queries through the axon while storing samples in a queue.
- **Trigger Checks**: How often should the queue be looked at. This can be triggered based on a specified number of `steps` or `seconds`,
as defined by the `trigger` and `trigger_frequency` parameters. If `trigger` is set to `steps`,
steps must be incremented using the `increment_step` or `set_step` methods.

## Integration
To use the tools provided here effectively, the subnet validator must: 
1. Create an `OrganicValidator` that inherits from the `OrganicScoringBase`
2. Override the `_on_organic_query` and `forward` methods for your specific logic 
3. Open the axon to the outside world 

```python 
from atom.base.validator import BaseValidatorNeuron
from atom.organic_scoring import OrganicScoringBase

class OrganicValidator(OrganicScoringBase):
    """Validator class to handle organic entries."""

    def __init__(
        self,
        axon: bt.axon,
        trigger_frequency: Union[float, int],
        trigger: Literal["seconds", "steps"],
        validator: BaseNeuron,
        trigger_frequency_min: Union[float, int] = 5,
        trigger_scaling_factor: Union[float, int] = 5,
        synth_dataset=None,
    ):
        super().__init__(
            axon=axon,
            synth_dataset=synth_dataset,
            trigger_frequency=trigger_frequency,
            trigger=trigger,
            trigger_frequency_min=trigger_frequency_min,
            trigger_scaling_factor=trigger_scaling_factor,
        )

        # Self reference the validator object to have access to validator methods.
        self._validator: BaseNeuron = validator

        
    @override
    def _on_organic_query(self, synapse) -> synapse: ...
        """ This is the entry point of the organic query """ 
        ... 
        return synapse 

    @override
    def forward(): ... 

class Validator(BaseValidatorNeuron):
    """ Example implementatino of a Validator constructor """

    def __init__(self, ... ):
        
        self.axon = bt.axon(wallet=self.wallet, config=self.config)
        self._serve_axon()

        self.loop = asyncio.get_event_loop()

        self._organic_scoring: Optional[OrganicValidator] = None
        if not self.config.neuron.axon_off and not self.config.neuron.organic_disabled:
            self._organic_scoring = OrganicValidator(
                axon=self.axon,
                validator=self,
                synth_dataset=None,
                trigger=self.config.neuron.organic_trigger,
                trigger_frequency=self.config.neuron.organic_trigger_frequency,
                trigger_frequency_min=self.config.neuron.organic_trigger_frequency_min,
            )

            self.loop.create_task(self._organic_scoring.start_loop())
        else:
            bt.logging.warning(
                "Organic scoring is not enabled. To enable, remove '--neuron.axon_off' and '--neuron.organic_disabled'"
            )

    def _serve_axon(self):
        """Serve axon to enable external connections"""
        validator_uid = self.metagraph.hotkeys.index(self.wallet.hotkey.ss58_address)
        bt.logging.info(f"Serving validator IP of UID {validator_uid} to chain...")
        self.axon.serve(netuid=self.config.netuid, subtensor=self.subtensor).start()
```

## Setup

Add to requirements to your project:
```shell
git+https://github.com/macrocosm-os/organic-scoring.git@main
```

Or install manually by:
```shell
pip install git+https://github.com/macrocosm-os/organic-scoring.git@main
```

## Implementation

### Example Usage
1. Create a subclass of OrganicScoringBase.
2. Implement the required methods.
3. Create an instance of the subclass.
4. Call the `start` method to start the organic scoring task.
5. Call the `stop` method to stop the organic scoring task.
6. Call the `increment_step` method to increment the step counter if the trigger is set to "steps".
