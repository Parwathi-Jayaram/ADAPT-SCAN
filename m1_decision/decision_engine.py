from .core.action import ScanAction
from .core.decision import Decision


class DecisionEngine:
    """
    M1 Decision Intelligence Engine.

    Responsibility:
    Decide which region should be scanned next using the
    current belief state, uncertainty, threat relevance,
    tracking value, scan cost, and remaining budget.

    M1 never accesses ground truth.
    """

    def __init__(
        self,
        information_gain_weight=0.20,
        threat_weight=0.65,
        tracking_weight=0.10,
        uncertainty_weight=0.05,
        default_scan_cost=0.10,
    ):
        self.information_gain_weight = information_gain_weight
        self.threat_weight = threat_weight
        self.tracking_weight = tracking_weight
        self.uncertainty_weight = uncertainty_weight
        self.default_scan_cost = default_scan_cost

    def calculate_information_gain(self, uncertainty):
        """
        Higher uncertainty means a scan can provide more
        useful information.

        Since M2's exact numerical measurement model is not
        fixed yet, M1 treats uncertainty as a normalized
        information-gain signal.
        """

        uncertainty = self._clamp(uncertainty)

        return uncertainty

    def calculate_tracking_value(self, last_observed, current_timestep):
        """
        Estimate the value of scanning a region again.

        Recently observed regions have higher tracking value,
        while regions that have not been observed for a long
        time receive lower tracking value.

        A never-observed region gets maximum tracking value
        because establishing an observation is useful.
        """

        if last_observed is None:
            return 1.0

        age = max(0, current_timestep - last_observed)

        return 1.0 / (1.0 + age)

    def calculate_scan_utility(
        self,
        information_gain,
        threat_score,
        uncertainty,
        tracking_value,
        scan_cost,
    ):
        """
        Calculate the final utility of scanning a region.

        Higher information gain, threat relevance, uncertainty
        and tracking value increase utility.

        Scan cost decreases utility.
        """

        information_gain = self._clamp(information_gain)
        threat_score = self._clamp(threat_score)
        uncertainty = self._clamp(uncertainty)
        tracking_value = self._clamp(tracking_value)

        utility = (
            self.information_gain_weight * information_gain
            + self.threat_weight * threat_score
            + self.tracking_weight * tracking_value
            + self.uncertainty_weight * uncertainty
            - scan_cost
        )

        return max(0.0, utility)

    def select_next_scan(self, state, region_ids):
        """
        Select the region with the highest expected utility.

        Parameters
        ----------
        state:
            DecisionState containing:
            - belief
            - remaining budget
            - current timestep

        region_ids:
            List of regions available for scanning.

        Returns
        -------
        Decision
            The selected scan action and explanation.
        """

        if not region_ids:
            raise ValueError("region_ids cannot be empty.")

        if state.remaining_budget <= 0:
            raise ValueError("No scanning budget remaining.")

        best_decision = None

        for region_id in region_ids:

            probability = state.belief.get_probability(region_id)

            # Treat the belief probability as threat/relevance
            # when detailed threat information is unavailable.
            threat_score = self._clamp(probability)

            uncertainty = 1.0 - threat_score

            information_gain = self.calculate_information_gain(
                uncertainty
            )

            observation_data = state.observations.get(region_id)

            if observation_data is None:
                last_observed = None
            else:
                last_observed = observation_data.get(
                    "last_observed",
                    state.time_step
                )

            tracking_value = self.calculate_tracking_value(
                last_observed,
                state.time_step,
            )

            scan_cost = self.default_scan_cost
            
            # Do not choose a scan that cannot be afforded.
            if scan_cost > state.remaining_budget:
                continue

            utility = self.calculate_scan_utility(
                information_gain=information_gain,
                threat_score=threat_score,
                uncertainty=uncertainty,
                tracking_value=tracking_value,
                scan_cost=scan_cost,
            )

            # Encourage exploration of regions that have not
            # been scanned yet.
            if region_id not in state.observations:
                utility += 0.10

            # Prioritize regions where M2 detected a signal.
            observation = state.observations.get(region_id)

            if observation is not None:
                if observation.get("detected", False):
                    utility += 0.30
            decision = Decision(
                action=ScanAction(region_id),
                utility=utility,
                information_gain=information_gain,
                threat_score=threat_score,
                uncertainty=uncertainty,
                tracking_value=tracking_value,
                scan_cost=scan_cost,
                reason=self._build_reason(
                    region_id=region_id,
                    information_gain=information_gain,
                    threat_score=threat_score,
                    uncertainty=uncertainty,
                    tracking_value=tracking_value,
                ),
            )

            if (
                best_decision is None
                or decision.utility > best_decision.utility
            ):
                best_decision = decision

        if best_decision is None:
            raise ValueError(
                "No region can be scanned within the remaining budget."
            )

        return best_decision

    @staticmethod
    def _build_reason(
        region_id,
        information_gain,
        threat_score,
        uncertainty,
        tracking_value,
    ):
        """
        Generate a human-readable explanation for M4/M5/UI.
        """

        reasons = []

        if threat_score >= 0.70:
            reasons.append("high threat relevance")

        if uncertainty >= 0.70:
            reasons.append("high uncertainty")

        if information_gain >= 0.70:
            reasons.append("high expected information gain")

        if tracking_value >= 0.70:
            reasons.append("useful for tracking")

        if not reasons:
            reasons.append("best available expected utility")

        return (
            f"Selected {region_id} because it has "
            + ", ".join(reasons)
            + "."
        )

    @staticmethod
    def _clamp(value):
        """
        Keep normalized values inside [0, 1].
        """

        if value is None:
            return 0.0

        return max(0.0, min(1.0, float(value)))