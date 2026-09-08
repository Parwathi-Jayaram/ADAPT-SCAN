import random


def generate_signal(
    region_id,
    signal_type="continuous",
    seed=None
):
    """
    Generate a synthetic TRUE signal.

    This represents ground truth inside the simulation.
    It must NOT be directly exposed to the AI/decision engine.
    """

    rng = random.Random(seed)

    # Basic signal properties
    bandwidth = rng.uniform(0.1, 1.0)
    strength = rng.uniform(0.3, 1.0)

    # Signal behaviour
    if signal_type == "continuous":

        activity = 1.0
        duration = rng.uniform(5.0, 10.0)

    elif signal_type == "intermittent":

        activity = rng.uniform(0.2, 0.8)
        duration = rng.uniform(1.0, 10.0)

    elif signal_type == "appearing":

        start_time = rng.uniform(0.0, 5.0)
        activity = 1.0
        duration = rng.uniform(1.0, 5.0)

    elif signal_type == "changing-strength":
        
        activity = 1.0
        duration = rng.uniform(5.0, 10.0)
        strength_change = rng.uniform(-0.3, 0.3)

    elif signal_type == "disappearing":

        # Signal exists initially and disappears later
        activity = 1.0
        duration = rng.uniform(1.0, 5.0)

        end_time = rng.uniform(5.0, 10.0)

    elif signal_type == "noisy":

        # This indicates a signal that is difficult to observe.
        # Actual noise will be handled by noise_model.py.
        activity = rng.uniform(0.5, 1.0)
        duration = rng.uniform(1.0, 10.0)

    elif signal_type == "overlapping":

        # Represents a signal that may overlap/confuse
        # with another signal in the same region.
        activity = rng.uniform(0.5, 1.0)
        duration = rng.uniform(1.0, 10.0)

    else:
        raise ValueError(
            f"Unsupported signal type: {signal_type}"
        )

    signal = {
        "region_id": region_id,
        "bandwidth": bandwidth,
        "strength": strength,
        "signal_type": signal_type,
        "activity": activity,
        "duration": duration
    }

    # Behaviour-specific information
    if signal_type == "appearing":
        signal["start_time"] = start_time

    elif signal_type == "changing-strength":
        signal["strength_change"] = strength_change

    elif signal_type == "disappearing":
        signal["end_time"] = end_time

    return signal


if __name__ == "__main__":

    signal_types = [
        "continuous",
        "intermittent",
        "appearing",
        "changing-strength",
        "disappearing",
        "noisy",
        "overlapping"
    ]

    for signal_type in signal_types:

        signal = generate_signal(
            region_id="R7",
            signal_type=signal_type,
            seed=42
        )

        print(f"\n{signal_type}:")
        print(signal)