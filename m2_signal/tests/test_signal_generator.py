import sys
from pathlib import Path

# Allow Python to find signal_generator.py
sys.path.append(str(Path(__file__).resolve().parents[1]))

from signal_generator import generate_signal


def test_continuous_signal():
    signal = generate_signal(
        region_id="R7",
        signal_type="continuous",
        seed=42
    )

    assert signal["region_id"] == "R7"
    assert signal["signal_type"] == "continuous"
    assert 0.1 <= signal["bandwidth"] <= 1.0
    assert 0.3 <= signal["strength"] <= 1.0
    assert signal["activity"] == 1.0


def test_intermittent_signal():
    signal = generate_signal(
        region_id="R7",
        signal_type="intermittent",
        seed=42
    )

    assert signal["signal_type"] == "intermittent"
    assert 0.2 <= signal["activity"] <= 0.8


def test_appearing_signal():
    signal = generate_signal(
        region_id="R7",
        signal_type="appearing",
        seed=42
    )

    assert signal["signal_type"] == "appearing"
    assert "start_time" in signal


def test_changing_strength_signal():
    signal = generate_signal(
        region_id="R7",
        signal_type="changing-strength",
        seed=42
    )

    assert signal["signal_type"] == "changing-strength"
    assert "strength_change" in signal


def test_disappearing_signal():
    signal = generate_signal(
        region_id="R7",
        signal_type="disappearing",
        seed=42
    )

    assert signal["signal_type"] == "disappearing"
    assert "end_time" in signal


def test_noisy_signal():
    signal = generate_signal(
        region_id="R7",
        signal_type="noisy",
        seed=42
    )

    assert signal["signal_type"] == "noisy"


def test_overlapping_signal():
    signal = generate_signal(
        region_id="R7",
        signal_type="overlapping",
        seed=42
    )

    assert signal["signal_type"] == "overlapping"


def test_reproducibility():
    signal_1 = generate_signal(
        region_id="R7",
        signal_type="continuous",
        seed=42
    )

    signal_2 = generate_signal(
        region_id="R7",
        signal_type="continuous",
        seed=42
    )

    assert signal_1 == signal_2


def test_different_seeds_produce_different_signals():
    signal_1 = generate_signal(
        region_id="R7",
        signal_type="continuous",
        seed=42
    )

    signal_2 = generate_signal(
        region_id="R7",
        signal_type="continuous",
        seed=100
    )

    assert signal_1 != signal_2


def test_invalid_signal_type():
    try:
        generate_signal(
            region_id="R7",
            signal_type="invalid",
            seed=42
        )

        assert False, "Expected ValueError"

    except ValueError:
        assert True