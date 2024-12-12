import numpy as np
import bittensor as bt
from typing import List


class ValidatorWeightSettingMixin:
    """Class to handle the functional separation of setting weights for the validator.

    This is an example of a Mixin class that can be used to separate the functionality of setting weights for the validator from the main class.
    """

    def set_weights(self):
        """
        Sets the validator weights to the metagraph hotkeys based on the scores it has received from the miners. The weights determine the trust and incentive level the validator assigns to miner nodes on the network.
        """

        # Check if self.scores contains any NaN values and log a warning if it does.
        if np.isnan(self.scores).any():
            bt.logging.warning(
                "Scores contain NaN values. This may be due to a lack of responses from miners, or a bug in your reward functions."
            )

        # Calculate the average reward for each uid across non-zero values.
        # Replace any NaN values with 0.
        raw_weights = (self.scores / (np.sum(self.scores, axis=0)+1e-6)).astype(np.float32)


        bt.logging.debug("raw_weights", raw_weights)
        bt.logging.debug("raw_weight_uids", self.metagraph.uids)
        # Process the raw weights to final_weights via subtensor limitations.
        (
            processed_weight_uids,
            processed_weights,
        ) = bt.utils.weight_utils.process_weights_for_netuid(
            uids=self.metagraph.uids,
            weights=raw_weights,
            netuid=self.config.netuid,
            subtensor=self.subtensor,
            metagraph=self.metagraph,
        )
        bt.logging.debug("processed_weights", processed_weights)
        bt.logging.debug("processed_weight_uids", processed_weight_uids)

        # Convert to uint16 weights and uids.
        (
            uint_uids,
            uint_weights,
        ) = bt.utils.weight_utils.convert_weights_and_uids_for_emit(
            uids=processed_weight_uids, weights=processed_weights
        )
        bt.logging.debug("uint_weights", uint_weights)
        bt.logging.debug("uint_uids", uint_uids)

        # Set the weights on chain via our subtensor connection.
        result = self.subtensor.set_weights(
            wallet=self.wallet,
            netuid=self.config.netuid,
            uids=uint_uids,
            weights=uint_weights,
            wait_for_finalization=False,
            wait_for_inclusion=False,
            version_key=self.spec_version,
        )

        return result

    def update_scores(self, rewards: np.ndarray, uids: List[int]):
        """Performs exponential moving average on the scores based on the rewards received from the miners."""

        # Check if rewards contains NaN values.
        if np.isnan(rewards).any():
            print(f"Warning: NaN values detected in rewards: {rewards}")
            # Replace any NaN values in rewards with 0.
            rewards = np.nan_to_num(rewards, nan=0)

        # Check if `uids` is already a NumPy array.
        if isinstance(uids, np.ndarray):
            uids_array = uids.copy()  # Create a copy to avoid modifying the original.
        else:
            uids_array = np.array(uids)  # Convert `uids` to a NumPy array.

        # Initialize rewards array for all indices with zeros.
        scattered_rewards = np.zeros_like(self.scores, dtype=np.float32)
        
        # Assign rewards to the appropriate indices based on `uids`.
        scattered_rewards[uids_array] = rewards

        bt.logging.debug(f"Scattered rewards: {scattered_rewards}")

        # Update scores using exponential moving average.
        alpha = self.config.neuron.moving_average_alpha
        self.scores = alpha * scattered_rewards + (1 - alpha) * self.scores

        bt.logging.debug(f"Updated moving avg scores: {self.scores}")
