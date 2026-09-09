from .core.belief import BeliefState
from .core.state import DecisionState
from .core.observation import Observation
from .intelligence.belief_updater import BeliefUpdater
from .decision_engine import DecisionEngine


class M1Controller:
    """
    Public interface for the M1 Decision Intelligence module.

    M1Controller hides the internal M1 components from the
    rest of the system.

    Flow:
        Observation
            ↓
        BeliefUpdater
            ↓
        BeliefState
            ↓
        DecisionEngine
            ↓
        Decision
    """

    def __init__(self):
        self.belief_state = BeliefState()
        self.belief_updater = BeliefUpdater()
        self.decision_engine = DecisionEngine()

    def process_observation(self, observation):
        """
        Update M1's belief using a processed observation.

        Parameters
        ----------
        observation:
            Observation received from the signal-processing layer.

        Returns
        -------
        float
            Updated belief probability.
        """

        return self.belief_updater.update_belief_state(
            observation,
            self.belief_state,
        )

    def process_observation_dict(self, data):
        """
        Convert an M2 processed observation dictionary into
        an M1 Observation object and update M1's belief.

        Parameters
        ----------
        data:
            Processed observation dictionary received from M2.

        Returns
        -------
        float
            Updated belief probability.
        """

        observation = Observation(
            region_id=data["region_id"],
            detected=data["detected"],
            strength=data.get("strength"),
            bandwidth=data.get("bandwidth"),
            snr=data.get("snr"),
            confidence=data.get("confidence"),
            features=data.get("features"),
            timestamp=data.get("timestamp"),
        )

        return self.process_observation(observation)

    def choose_next_scan(
        self,
        region_ids,
        remaining_budget,
        time_step,
        observations=None,
    ):
        """
        Select the next region to scan.

        Parameters
        ----------
        region_ids:
            Regions currently available for scanning.

        remaining_budget:
            Remaining scan budget.

        time_step:
            Current simulation time-step.

        observations:
            Previously observed-region information.

        Returns
        -------
        Decision
            M1's selected decision.
        """

        state = DecisionState(
            belief=self.belief_state,
            remaining_budget=remaining_budget,
            time_step=time_step,
            observations=observations or {},
        )

        return self.decision_engine.select_next_scan(
            state,
            region_ids,
        )