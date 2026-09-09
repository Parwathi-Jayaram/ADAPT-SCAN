from m1_decision.m1_controller import M1Controller
from m2_signal.m3_integration import M2M3Bridge


# ---------------------------------------------------------
# 1. Create M1 and M3/M2 bridge
# ---------------------------------------------------------

m1 = M1Controller()

bridge = M2M3Bridge(
    noise_level="medium",
    seed=42,
    use_real_data=False
)


# ---------------------------------------------------------
# 2. Initialize one M3 scenario
# ---------------------------------------------------------

bridge.reset_scenario(
    scenario_id="S1",
    seed=42
)


# ---------------------------------------------------------
# 3. Define available regions
# ---------------------------------------------------------

regions = [
    f"R{i}"
    for i in range(1, 21)
]


# ---------------------------------------------------------
# 4. Store observations received from M2
# ---------------------------------------------------------

observations = {}


# ---------------------------------------------------------
# 5. Initial scanning budget
# ---------------------------------------------------------

remaining_budget = 100.0


# ---------------------------------------------------------
# 6. Run the closed-loop scanning process
# ---------------------------------------------------------

for time_step in range(10):

    print("\n" + "=" * 60)
    print(f"TIME STEP {time_step}")
    print("=" * 60)


    # -----------------------------------------------------
    # M1 decides which region should be scanned
    # -----------------------------------------------------

    decision = m1.choose_next_scan(
        region_ids=regions,
        remaining_budget=remaining_budget,
        time_step=time_step,
        observations=observations
    )

    selected_region = decision.action.region_id

    print(
        f"M1 selected region: {selected_region}"
    )


    # -----------------------------------------------------
    # M3 performs the actual scan
    # -----------------------------------------------------

    processed_observation = bridge.scan_region(
        selected_region
    )


    # -----------------------------------------------------
    # M2 processes M3's scan result
    # -----------------------------------------------------

    observations[selected_region] = (
        processed_observation
    )


    print(
        f"M2 detected: "
        f"{processed_observation['detected']}"
    )

    print(
        f"Signal strength: "
        f"{processed_observation['strength']:.3f}"
    )

    print(
        f"SNR: "
        f"{processed_observation['snr']:.3f}"
    )

    print(
        f"Confidence: "
        f"{processed_observation['confidence']:.3f}"
    )


    # -----------------------------------------------------
    # M1 updates its belief using M2's observation
    # -----------------------------------------------------

    updated_belief = (
        m1.process_observation_dict(
            processed_observation
        )
    )


    print(
        f"M1 updated belief for "
        f"{selected_region}: "
        f"{updated_belief:.3f}"
    )


    # -----------------------------------------------------
    # Reduce scanning budget
    # -----------------------------------------------------

    remaining_budget -= 1.0

    print(
        f"Remaining budget: "
        f"{remaining_budget:.1f}"
    )


print("\n" + "=" * 60)
print("CLOSED LOOP COMPLETED")
print("=" * 60)

print(
    "\nM1 -> M3 -> M2 -> M1 loop is working."
)