from ..core.action import ScanAction


class ThreatPriorityPolicy:
    """
    Baseline policy that selects the region
    with the highest estimated threat probability.
    """

    def select_action(self, region_ids, belief):
        """
        Select the region with the highest threat probability.

        Parameters:
            region_ids: list of region IDs
            belief: BeliefState containing probabilities

        Returns:
            ScanAction for the highest-priority region.
        """

        if not region_ids:
            raise ValueError("region_ids cannot be empty.")

        best_region = region_ids[0]
        best_probability = belief.get_probability(best_region)

        for region_id in region_ids[1:]:
            probability = belief.get_probability(region_id)

            if probability > best_probability:
                best_probability = probability
                best_region = region_id

        return ScanAction(best_region)