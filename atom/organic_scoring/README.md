# Generic Implementation of Organic Scoring for Bittensor Subnets

This implementation provides a generic solution for integrating organic scoring into a Bittensor subnets.


## Functionality Overview
- **Organic Query Handling**: Manages organic queries through the axon while storing samples in a queue.
- **Rewarding Process**: Can be triggered based on a specified number of `steps` or `seconds`,
as defined by the `trigger` and `trigger_frequency` parameters. If `trigger` is set to `steps`,
steps must be incremented using the `increment_step` or `set_step` methods.


## Process Workflow
1. **Trigger Check**: Upon triggering the rewarding process, the system checks if the organic queue is empty.
If the queue is empty, synthetic datasets (defined in `organic_scoring/synth_dataset_base.py`) are used to bootstrap
the organic scoring mechanism. Otherwise, samples from the organic queue are utilized.
2. **Data Processing**: The sampled data is concurrently passed to the `_query_miners` and `_generate_reference`
methods.
3. **Reward Generation**: After receiving responses from miners and any reference data, the information
is processed by the `_generate_rewards` method.
4. **Weight Setting**: The generated rewards are then applied through the `_set_weights` method.
5. **Logging**: Finally, the results can be logged using the `_log_results` method, along with all relevant data
provided as arguments, and default time elapsed on each step of rewarding process.


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

### Implement the following OrganicScoringBase methods
- `_on_organic_entry`: Handle an organic entry.
    Important: this method must add the required values to the `_organic_queue`.
- `_query_miners`: Query the miners with a given organic sample.
- `_generate_rewards`: Concurrently generate rewards based on the sample and responses.
- `_set_weights`: Set the weights based on generated rewards for the miners.
- (Optional) `_generate_reference`: Generate a reference based on the sample, if required.
    Used in `_generate_rewards`.
- (Optional) `_log_results`: Log the results.
- (Optional) `_priority_fn`: Function with priority value for organic handles.
- (Optional) `_blacklist_fn`: Function with blacklist for organic handles.
- (Optional) `_verify_fn`: Function to verify requests for organic handles.

```python
from organic_scoring import OrganicScoringBase
from organic_scoring.organic_queue import OrganicQueueBase
from organic_scoring.synth_dataset import SynthDatasetBase


class YourOrganicScoring(OrganicScoringBase):
    # Implement the required methods.
    ...

class YourOrganicQueue(OrganicQueueBase):
    # Implement the required methods.
    def add(self, sample: Any):
        ...
    
    def sample(self) -> Any:
        ...

    @property
    def size(self) -> int:
        ...

class YourSynthDataset(SynthDatasetBase):
    # Implement the required methods.
    def sample(self) -> Any:
        ...

axon = bt.axon(wallet=self.wallet, config=self.config)
axon.serve(netuid=self.config.netuid, subtensor=self.subtensor)
axon.start()

organic_scoring = YourOrganicScoring(
    axon=axon,
    synth_dataset=YourSynthDataset(),
    organic_queue=YourOrganicQueue(),
    trigger_frequency=15,
    trigger="seconds",
)
organic_scoring.start()
```


## Additional Information

TODO: SN1 implementation reference.

Feel free to reach out us through the [Bittensor discord](https://discord.gg/UqAxyhrf) (alpha 1 - SN1 channel).
