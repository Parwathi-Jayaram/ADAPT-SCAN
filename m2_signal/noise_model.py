import random


# Noise configurations for different simulation difficulty levels.
NOISE_LEVELS = {
    "low": {
        "noise_strength": 0.03,  # Lowered from 0.05
        "missing_probability": 0.00
    },
    "medium": {
        "noise_strength": 0.08,  # Lowered from 0.15
        "missing_probability": 0.03  # Lowered from 0.05
    },
    "high": {
        "noise_strength": 0.15,  # Lowered from 0.30
        "missing_probability": 0.08  # Lowered from 0.15
    }
}


def get_noise_config(level="medium"):
    """
    Return the noise configuration for a given difficulty level.

    Parameters
    ----------
    level : str
        Supported levels:
        - low
        - medium
        - high

    Returns
    -------
    dict
        Noise configuration.
    """

    if level not in NOISE_LEVELS:
        raise ValueError(
            f"Unsupported noise level: {level}"
        )

    return NOISE_LEVELS[level].copy()


def apply_noise(value, noise_strength, seed=None):
    """
    Apply random measurement noise to a value.

    The same seed produces the same noisy value.
    """

    rng = random.Random(seed)

    noise = rng.gauss(
        0,
        noise_strength
    )

    noisy_value = value + noise

    # Keep normalized values within [0, 1]
    noisy_value = max(0.0, min(1.0, noisy_value))

    return noisy_value


if __name__ == "__main__":

    for level in ["low", "medium", "high"]:

        config = get_noise_config(level)

        print(f"\n{level.upper()} NOISE")
        print(config)

    value = 0.8

    noisy_value_1 = apply_noise(
        value,
        noise_strength=0.15,
        seed=42
    )

    noisy_value_2 = apply_noise(
        value,
        noise_strength=0.15,
        seed=42
    )

    print("\nOriginal value:", value)
    print("Noisy value 1:", noisy_value_1)
    print("Noisy value 2:", noisy_value_2)
    print("Reproducible:", noisy_value_1 == noisy_value_2)