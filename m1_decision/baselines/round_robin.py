from ..core.action import ScanAction


class RoundRobinPolicy:
    """
    Baseline policy that scans regions sequentially.
    """

    def __init__(self):
        self.current_index = 0

    def select_action(self, region_ids):
        """
        Select the next region in sequential order.
        """

        if not region_ids:
            raise ValueError("region_ids cannot be empty.")

        # Select current region
        selected_region = region_ids[self.current_index]

        # Move to the next region
        self.current_index = (
            self.current_index + 1
        ) % len(region_ids)

        return ScanAction(selected_region)