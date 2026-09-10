"""ADAPT-SCAN Backend — FastAPI integration layer for M4."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "m1_decision"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "m3_simulator"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import uuid
import random
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# M3 Simulator
from m3_simulator.environment import Environment
from m3_simulator.scenarios import SCENARIO_CONFIGS, list_scenarios

# M1 Decision
from m1_decision.m1_controller import M1Controller
from m1_decision.core.decision import Decision
from m1_decision.core.action import ScanAction
from m1_decision.baselines.random_policy import RandomPolicy
from m1_decision.baselines.round_robin import RoundRobinPolicy
from m1_decision.baselines.threat_priority import ThreatPriorityPolicy
from m1_decision.baselines.information_gain import InformationGainPolicy

# Schemas
from common.schemas import (
    RegionState,
    ScanDelta,
    ScanRecord,
    DecisionResponse,
    CandidateRank,
    ObservationState,
    SimulationResetRequest,
    SimulationStepRequest,
    EventRequest,
)


app = FastAPI(title="ADAPT-SCAN API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Scenario mapping ──────────────────────────────────────────────────────────

FRONTEND_TO_BACKEND_SCENARIO: Dict[str, str] = {
    "NORMAL": "S1",
    "DYNAMIC": "S4",
    "HIGH_NOISE": "S8",
    "LIMITED": "S6",
    "SUDDEN": "S7",
    "HIGH_UNC": "S5",
    "STRESS": "S8",
}


# ─── Session state ─────────────────────────────────────────────────────────────

class Session:
    def __init__(self, session_id: str, env: Environment, controller: M1Controller, strategy: str):
        self.session_id = session_id
        self.env = env
        self.controller = controller
        self.strategy = strategy
        self.random_policy = RandomPolicy(seed=env.seed)
        self.round_robin = RoundRobinPolicy()
        self.threat_policy = ThreatPriorityPolicy()
        self.info_gain_policy = InformationGainPolicy()
        self.history: List[ScanRecord] = []
        self.decision_events: List[Dict[str, Any]] = []
        self.event_id_counter = 0
        self.override_next: Optional[str] = None
        self.prev_observation: Optional[Dict[str, Any]] = None


sessions: Dict[str, Session] = {}


def get_session(session_id: str) -> Session:
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return sessions[session_id]


def _get_region_freq(index: int) -> int:
    return 100 + index * 250


def _build_region_state(
    region_id: str,
    obs: Dict[str, Any],
    belief_prob: float,
    emitters: Dict[str, List[Any]],
    strategy: str,
) -> RegionState:
    idx = int(region_id.replace("R", "")) - 1
    freq = _get_region_freq(idx)

    active = False
    signal_type = "UNKNOWN"
    priority = 0.0
    bw = 0
    strength = 0.0

    if region_id in emitters:
        active_emitters = [e for e in emitters[region_id] if getattr(e, "exists", False)]
        if active_emitters:
            active = True
            e = active_emitters[0]
            if getattr(e, "is_intermittent", False):
                signal_type = "COMM"
            else:
                signal_type = "RADAR"
            priority = getattr(e, "threat_relevance", 0.5)
            bw = int(getattr(e, "bandwidth", 0.3) * 50)
            strength = getattr(e, "strength", 0.5)

    status = "unknown"
    if obs.get("status") == "scanned":
        if belief_prob > 0.78:
            status = "TRACKED"
        elif obs.get("threat_relevance", 0) > 0.7 and belief_prob > 0.5:
            status = "HIGH PRIORITY"
        elif obs.get("uncertainty", 0) > 0.65:
            status = "UNCERTAIN"
        else:
            status = "OBSERVING"

    return RegionState(
        region_id=region_id,
        existence=float(obs.get("detected") or 0.0),
        uncertainty=obs.get("uncertainty", 0.9),
        threat_relevance=obs.get("threat_relevance", 0.0),
        last_observed=obs.get("last_observed", -1),
        status=status,
        detected=obs.get("detected"),
        strength=obs.get("strength"),
        snr=obs.get("snr"),
        confidence=obs.get("confidence"),
        freqMHz=freq,
        bwMHz=bw,
        signalStrength=strength,
        signalType=signal_type,
        active=active,
        priority=priority,
        beliefProb=belief_prob,
    )


def _compute_candidates(
    session: Session,
    region_ids: List[str],
) -> List[CandidateRank]:
    env = session.env
    obs_state = env.get_observation_state()
    step = obs_state["timestep"]
    strategy = session.strategy

    candidates: List[CandidateRank] = []

    for rid in region_ids:
        last_scan = None
        for scan in reversed(env.scan_history):
            if scan.region_id == rid:
                last_scan = scan
                break

        belief = session.controller.belief_state.get_probability(rid)
        threat = obs_state["regions"][int(rid.replace("R", "")) - 1].get("threat_relevance", 0.0)
        unc = 1.0 - belief

        staleness = 1.0 if last_scan is None else max(0.0, (step - last_scan.timestamp)) / 12.0
        ig = max(0.0, min(1.0, unc * staleness))
        tracking_urgency = max(0.0, min(1.0, staleness * 0.6 + unc * 0.4))
        threat_value = max(0.0, min(1.0, threat))
        cost = max(0.0, 0.08 + (1.0 - max(0.0, min(1.0, threat))) * 0.15)

        if strategy == "RANDOM":
            utility = random.random()
        elif strategy == "ROUND_ROBIN":
            utility = 9999.0 if last_scan is None else float(step - last_scan.timestamp)
        elif strategy == "THREAT_PRIORITY":
            utility = threat * max(0.0, min(1.0, threat)) + (last_scan.strength if last_scan else 0.0) * 0.2
        else:
            utility = (ig * 0.38 + threat_value * 0.35 + tracking_urgency * 0.17) / (cost + 0.01)

        candidates.append(CandidateRank(
            id=rid,
            utility=utility,
            info_gain=ig,
            threat_score=threat_value,
            tracking_value=tracking_urgency,
            scan_cost=cost,
        ))

    candidates.sort(key=lambda c: c.utility, reverse=True)
    return candidates[:5]


def _select_action(session: Session, region_ids: List[str]) -> tuple[ScanAction, str]:
    strategy = session.strategy
    env = session.env
    step = env.timestep
    budget = env.budget_remaining
    belief = session.controller.belief_state

    if strategy == "RANDOM":
        return session.random_policy.select_action(region_ids), "random"
    elif strategy == "ROUND_ROBIN":
        return session.round_robin.select_action(region_ids), "round_robin"
    elif strategy == "THREAT_PRIORITY":
        return session.threat_policy.select_action(region_ids, belief), "threat_priority"
    elif strategy == "INFORMATION_GAIN":
        return ScanAction(session.info_gain_policy.select_region(belief, region_ids)), "information_gain"
    else:
        observations: Dict[str, Dict[str, Any]] = {}
        for rid in region_ids:
            last_scan = None
            for scan in reversed(env.scan_history):
                if scan.region_id == rid:
                    last_scan = scan
                    break
            observations[rid] = {"last_observed": last_scan.timestamp if last_scan else None}

        decision: Decision = session.controller.choose_next_scan(
            region_ids=region_ids,
            remaining_budget=budget,
            time_step=step,
            observations=observations,
        )
        return decision.action, decision.reason


def _region_status(status: str, belief_prob: float, threat: float, unc: float) -> str:
    if status != "scanned":
        return "unknown"
    if belief_prob > 0.78:
        return "TRACKED"
    if threat > 0.7 and belief_prob > 0.5:
        return "HIGH PRIORITY"
    if unc > 0.65:
        return "UNCERTAIN"
    return "OBSERVING"


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/scenarios")
def get_scenarios():
    result = []
    for sid, cfg in SCENARIO_CONFIGS.items():
        result.append({
            "id": sid,
            "name": cfg.get("name", sid),
            "description": cfg.get("description", ""),
            "num_emitters": cfg.get("num_emitters", 1),
            "noise_level": cfg.get("noise_level", "low"),
            "budget": cfg.get("budget", 100),
        })
    return result


@app.post("/api/simulation/reset")
def reset_simulation(req: SimulationResetRequest):
    session_id = str(uuid.uuid4())

    backend_scenario = FRONTEND_TO_BACKEND_SCENARIO.get(req.scenario, req.scenario)
    if backend_scenario not in SCENARIO_CONFIGS:
        raise HTTPException(status_code=400, detail=f"Unknown scenario: {req.scenario}")

    env = Environment(num_regions=req.num_regions, seed=req.seed or 42)
    controller = M1Controller()

    obs = env.reset(scenario=backend_scenario, seed=req.seed)

    session = Session(
        session_id=session_id,
        env=env,
        controller=controller,
        strategy=req.strategy,
    )
    session.prev_observation = obs
    sessions[session_id] = session

    region_states = []
    emitters = env.ground_truth.emitters
    for r in obs["regions"]:
        rid = r["region_id"]
        bp = controller.belief_state.get_probability(rid)
        region_states.append(_build_region_state(rid, r, bp, emitters, req.strategy))

    return {
        "session_id": session_id,
        "strategy": req.strategy,
        "scenario": backend_scenario,
        "observation_state": ObservationState(
            regions=region_states,
            timestep=obs["timestep"],
            budget_remaining=obs["budget_remaining"],
            budget_total=obs["budget_total"],
            budget_remaining_frac=obs["budget_remaining_frac"],
            current_scan=obs.get("current_scan"),
            scenario=backend_scenario,
            intelligence=obs.get("intelligence", {}),
        ).model_dump(by_alias=True),
        "belief_state": {rid: controller.belief_state.get_probability(rid) for rid in [f"R{i}" for i in range(1, req.num_regions + 1)]},
        "done": False,
    }


@app.post("/api/simulation/step")
def simulation_step(req: SimulationStepRequest):
    session = get_session(req.session_id)
    env = session.env
    controller = session.controller
    strategy = session.strategy

    if env.is_done():
        return _build_done_response(session)

    region_ids = [f"R{i}" for i in range(1, env.num_regions + 1)]

    prev_observation = env.get_observation_state()

    override = req.override_region_id
    if override and override in region_ids:
        action_region = override
        is_override = True
        session.override_next = None
    elif session.override_next:
        action_region = session.override_next
        is_override = True
        session.override_next = None
    else:
        try:
            scan_action, reason = _select_action(session, region_ids)
            action_region = scan_action.region_id
            is_override = False
        except ValueError:
            return _build_done_response(session)

    prev_beliefs = {rid: controller.belief_state.get_probability(rid) for rid in region_ids}

    observation, reward, done, info = env.step(action_region)

    scan_result = info.get("scan_result")
    if scan_result:
        from m1_decision.core.observation import Observation
        obs_obj = Observation(
            region_id=scan_result["region_id"],
            detected=scan_result["detected"],
            strength=scan_result.get("strength"),
            bandwidth=scan_result.get("bandwidth"),
            snr=scan_result.get("snr"),
            confidence=scan_result.get("confidence"),
            timestamp=scan_result.get("timestamp"),
        )
        controller.process_observation(obs_obj)

    new_beliefs = {rid: controller.belief_state.get_probability(rid) for rid in region_ids}

    region_states = []
    emitters = env.ground_truth.emitters
    for r in observation["regions"]:
        rid = r["region_id"]
        bp = new_beliefs.get(rid, 0.0)
        region_states.append(_build_region_state(rid, r, bp, emitters, strategy))

    obs_state = ObservationState(
        regions=region_states,
        timestep=observation["timestep"],
        budget_remaining=observation["budget_remaining"],
        budget_total=observation["budget_total"],
        budget_remaining_frac=observation["budget_remaining_frac"],
        current_scan=observation.get("current_scan"),
        scenario=observation.get("scenario", env.scenario_id),
        intelligence=observation.get("intelligence", {}),
    )

    candidates = _compute_candidates(session, region_ids)
    top_candidate = candidates[0] if candidates else None

    if scan_result:
        detected = scan_result["detected"]
        confidence = scan_result.get("confidence", 0.5)
        bp_before = prev_beliefs.get(action_region, 0.0)
        bp_after = new_beliefs.get(action_region, 0.0)
        unc_before = 1.0 - bp_before
        unc_after = 1.0 - bp_after

        prev_region_obs = next((r for r in prev_observation["regions"] if r["region_id"] == action_region), {})
        prev_threat = prev_region_obs.get("threat_relevance", 0.0)
        status_before = _region_status(prev_region_obs.get("status", "unknown"), bp_before, prev_threat, unc_before)

        curr_region_obs = next((r for r in observation["regions"] if r["region_id"] == action_region), {})
        curr_threat = curr_region_obs.get("threat_relevance", 0.0)
        status_after = _region_status(curr_region_obs.get("status", "scanned"), bp_after, curr_threat, unc_after)

        scan_delta = ScanDelta(
            region_id=action_region,
            belief_before=bp_before,
            belief_after=bp_after,
            unc_before=unc_before,
            unc_after=unc_after,
            status_before=status_before,
            status_after=status_after,
            detected=detected,
        )

        record = ScanRecord(
            step=env.timestep,
            region_id=action_region,
            info_gain=top_candidate.info_gain if top_candidate else 0.0,
            threat_value=top_candidate.threat_score if top_candidate else 0.0,
            uncertainty=unc_after,
            tracking_urgency=top_candidate.tracking_value if top_candidate else 0.0,
            scan_cost=scan_result.get("scan_cost", 1.0),
            detected_signal=detected,
            explanation=f"Scanned {action_region} — {'detected' if detected else 'no signal'} at confidence {confidence:.2f}.",
            strategy=strategy,
        )

        session.history.insert(0, record)
        session.history = session.history[:60]

        session.decision_events.append({
            "id": session.event_id_counter,
            "step": env.timestep,
            "elapsed": 0,
            "type": "override" if is_override else "ai",
            "regionId": action_region,
            "label": f"{'Operator override' if is_override else 'AI selected'} {action_region} — {'HIT' if detected else 'NIL'}",
            "detected": detected,
            "record": record.model_dump(by_alias=True),
        })
        session.event_id_counter += 1

        if strategy == "ADAPT_SCAN" and not is_override:
            _, reason = _select_action(session, region_ids)
        elif is_override:
            reason = f"Operator override selected {action_region}."
        else:
            reason = f"{strategy.replace('_', ' ').title()} policy selected {action_region}."

        decision = DecisionResponse(
            region_id=action_region,
            utility=top_candidate.utility if top_candidate else 0.0,
            information_gain=top_candidate.info_gain if top_candidate else 0.0,
            threat_score=top_candidate.threat_score if top_candidate else 0.0,
            uncertainty=unc_after,
            tracking_value=top_candidate.tracking_value if top_candidate else 0.0,
            scan_cost=scan_result.get("scan_cost", 1.0),
            reason=reason,
        )
    else:
        scan_delta = None
        record = None
        decision = DecisionResponse(
            region_id=action_region,
            utility=0.0,
            information_gain=0.0,
            threat_score=0.0,
            uncertainty=0.0,
            tracking_value=0.0,
            scan_cost=0.0,
            reason="Scan skipped — insufficient budget.",
        )

    session.prev_observation = observation

    return {
        "session_id": req.session_id,
        "step": env.timestep,
        "done": done,
        "observation_state": obs_state.model_dump(by_alias=True),
        "decision": decision.model_dump(by_alias=True) if decision else None,
        "scan_result": scan_result,
        "scan_delta": scan_delta.model_dump(by_alias=True) if scan_delta else None,
        "scan_record": record.model_dump(by_alias=True) if record else None,
        "candidates": [c.model_dump(by_alias=True) for c in candidates],
        "history": [h.model_dump(by_alias=True) for h in session.history],
        "decision_events": session.decision_events,
        "metrics": {
            "detection_rate": sum(1 for h in session.history if h.detected_signal) / max(len(session.history), 1),
            "avg_info_gain": sum(h.info_gain for h in session.history) / max(len(session.history), 1),
            "avg_threat": sum(h.threat_value for h in session.history) / max(len(session.history), 1),
            "budget_remaining": env.budget_remaining,
            "budget_total": env.budget_total,
        },
    }


def _build_done_response(session: Session) -> Dict[str, Any]:
    env = session.env
    obs = env.get_observation_state()
    controller = session.controller
    region_states = []
    emitters = env.ground_truth.emitters
    for r in obs["regions"]:
        rid = r["region_id"]
        bp = controller.belief_state.get_probability(rid)
        region_states.append(_build_region_state(rid, r, bp, emitters, session.strategy))

    return {
        "session_id": session.session_id,
        "step": env.timestep,
        "done": True,
        "observation_state": ObservationState(
            regions=region_states,
            timestep=obs["timestep"],
            budget_remaining=obs["budget_remaining"],
            budget_total=obs["budget_total"],
            budget_remaining_frac=obs["budget_remaining_frac"],
            current_scan=obs.get("current_scan"),
            scenario=obs.get("scenario", env.scenario_id),
            intelligence=obs.get("intelligence", {}),
        ).model_dump(by_alias=True),
        "decision": None,
        "scan_result": None,
        "scan_delta": None,
        "scan_record": None,
        "candidates": [],
        "belief_state": {rid: controller.belief_state.get_probability(rid) for rid in [f"R{i}" for i in range(1, env.num_regions + 1)]},
        "history": [h.model_dump(by_alias=True) for h in session.history],
        "decision_events": session.decision_events,
        "metrics": {
            "detection_rate": sum(1 for h in session.history if h.detected_signal) / max(len(session.history), 1),
            "avg_info_gain": sum(h.info_gain for h in session.history) / max(len(session.history), 1),
            "avg_threat": sum(h.threat_value for h in session.history) / max(len(session.history), 1),
            "budget_remaining": env.budget_remaining,
            "budget_total": env.budget_total,
        },
    }


@app.get("/api/regions")
def get_regions(session_id: str):
    session = get_session(session_id)
    env = session.env
    controller = session.controller
    obs = env.get_observation_state()
    emitters = env.ground_truth.emitters
    region_states = []
    for r in obs["regions"]:
        rid = r["region_id"]
        bp = controller.belief_state.get_probability(rid)
        region_states.append(_build_region_state(rid, r, bp, emitters, session.strategy))
    return {"regions": [rs.model_dump(by_alias=True) for rs in region_states]}


@app.get("/api/metrics")
def get_metrics(session_id: str):
    session = get_session(session_id)
    env = session.env
    history = session.history
    return {
        "detection_rate": sum(1 for h in history if h.detected_signal) / max(len(history), 1),
        "avg_info_gain": sum(h.info_gain for h in history) / max(len(history), 1),
        "avg_threat": sum(h.threat_value for h in history) / max(len(history), 1),
        "budget_remaining": env.budget_remaining,
        "budget_total": env.budget_total,
        "steps": env.timestep,
        "scans": len(history),
        "detections": sum(1 for h in history if h.detected_signal),
    }


@app.post("/api/events")
def trigger_event(req: EventRequest):
    session = get_session(req.session_id)
    env = session.env

    event_type = req.event_type
    if event_type == "introduce_emitter":
        silent = [f"R{i}" for i in range(1, env.num_regions + 1) if f"R{i}" not in env.ground_truth.emitters]
        if silent:
            rid = silent[0]
            from m3_simulator.emitter import Emitter
            emitter = Emitter(
                region_id=rid,
                exists=True,
                strength=random.uniform(0.7, 1.0),
                activity=0.9,
                threat_relevance=random.uniform(0.7, 1.0),
                bandwidth=random.uniform(0.3, 0.6),
                is_intermittent=False,
                persistence=1.0,
            )
            env.ground_truth.emitters[rid] = [emitter]
    elif event_type == "increase_noise":
        env.noise_model.set_noise_level("very_high" if env.noise_model.current_noise_level == "high" else "high")
    elif event_type == "reduce_budget":
        env.budget_remaining = max(0.0, env.budget_remaining * 0.85)
    elif event_type == "uncertainty_spike":
        pass
    elif event_type == "signal_disappears":
        tracked = [rid for rid, ems in env.ground_truth.emitters.items() if any(e.exists for e in ems)]
        if tracked:
            rid = random.choice(tracked)
            for e in env.ground_truth.emitters.get(rid, []):
                e.exists = False

    return {"status": "ok", "event": event_type}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
