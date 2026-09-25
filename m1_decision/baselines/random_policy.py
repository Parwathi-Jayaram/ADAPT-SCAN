import random

from ..core.action import ScanAction


class RandomPolicy:
    """
    Baseline policy that randomly selects one region to scan.
    """

    def __init__(self, seed=None):
        """
        Create the random policy.

        seed:
            Optional value used to make the policy reproducible.
        """

        self.rng = random.Random(seed)

    def select_action(self, region_ids):
        """
        Randomly select one region from the available regions.

        Parameters:
            region_ids: list of region IDs

        Returns:
            ScanAction containing the selected region.
        """

        if not region_ids:
            raise ValueError("region_ids cannot be empty.")

        selected_region = self.rng.choice(region_ids)

        return ScanAction(selected_region)