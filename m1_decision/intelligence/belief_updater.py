class BeliefUpdater:
    """
    Converts an M1 Observation into an updated belief probability.

    M1 only uses the processed observation provided to it.
    Ground truth is never accessed.
    """

    def __init__(
        self,
        detected_probability=0.70,
        not_detected_probability=0.20,
        confidence_weight=0.30,
    ):
        self.detected_probability = detected_probability
        self.not_detected_probability = not_detected_probability
        self.confidence_weight = confidence_weight

    def update(self, observation, current_probability=0.0):
        """
        Update the belief probability for one region.

        The update uses the processed M2 observation.

        Detection confidence, signal strength, SNR,
        and reliability are combined to estimate
        how strongly the observation should affect belief.
        """

        current_probability = self._clamp(
            current_probability
        )

        confidence = self._clamp(
            observation.confidence
            if observation.confidence is not None
            else 0.5
        )

        if observation.detected:

            strength = self._clamp(
                observation.strength
                if observation.strength is not None
                else 0.0
            )

            snr = max(
                0.0,
                float(
                    observation.snr
                    if observation.snr is not None
                    else 0.0
                )
            )

            # Normalize SNR to approximately [0, 1].
            snr_score = self._clamp(
                snr / 20.0
            )

            # Reliability can be supplied through
            # M2's processed feature vector.
            reliability = 0.5

            if observation.features:
                if len(observation.features) > 5:
                    reliability = self._clamp(
                        observation.features[5]
                    )

            # Combine M2 measurements.
            evidence_strength = (
                0.30 * confidence
                + 0.30 * strength
                + 0.25 * snr_score
                + 0.15 * reliability
            )

            evidence_strength = self._clamp(
                evidence_strength
            )

            # A detected signal should create a
            # meaningful threat belief.
            evidence = (
                self.detected_probability
                + (
                    1.0 - self.detected_probability
                ) * evidence_strength
            )

        else:

            # A non-detection reduces belief.
            evidence = self.not_detected_probability

        updated_probability = (
            (1.0 - self.confidence_weight)
            * current_probability
            + self.confidence_weight
            * evidence
        )

        return self._clamp(
            updated_probability
        )

    def update_belief_state(
        self,
        observation,
        belief_state
    ):
        """
        Update the M1 BeliefState using a processed observation.

        Returns the updated probability.
        """

        current_probability = (
            belief_state.get_probability(
                observation.region_id
            )
        )

        new_probability = self.update(
            observation,
            current_probability,
        )

        belief_state.update_probability(
            observation.region_id,
            new_probability,
        )

        return new_probability

    @staticmethod
    def _clamp(value):
        """
        Keep probability inside [0, 1].
        """

        if value is None:
            return 0.0

        return max(
            0.0,
            min(
                1.0,
                float(value)
            )
        )