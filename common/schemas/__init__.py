from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, List, Any


class RegionState(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    region_id: str = Field(alias="id")
    existence: float
    uncertainty: float
    threat_relevance: float = Field(alias="threatLevel")
    last_observed: Optional[int] = Field(default=None, alias="lastScanned")
    status: str
    detected: Optional[bool] = None
    strength: Optional[float] = None
    bandwidth: Optional[float] = None
    snr: Optional[float] = None
    confidence: Optional[float] = None
    freqMHz: Optional[int] = None
    bwMHz: Optional[int] = None
    signalStrength: Optional[float] = None
    signalType: Optional[str] = None
    active: Optional[bool] = None
    priority: Optional[float] = None
    beliefProb: Optional[float] = None


class ScanDelta(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    region_id: str = Field(alias="regionId")
    belief_before: float = Field(alias="beliefBefore")
    belief_after: float = Field(alias="beliefAfter")
    unc_before: float = Field(alias="uncBefore")
    unc_after: float = Field(alias="uncAfter")
    status_before: str = Field(alias="statusBefore")
    status_after: str = Field(alias="statusAfter")
    detected: bool


class ScanRecord(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    step: int
    region_id: str = Field(alias="regionId")
    info_gain: float = Field(alias="infoGain")
    threat_value: float = Field(alias="threatValue")
    uncertainty: float
    tracking_urgency: float = Field(alias="trackingUrgency")
    scan_cost: float = Field(alias="scanCost")
    detected_signal: bool = Field(alias="detectedSignal")
    explanation: str
    strategy: str


class DecisionResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    region_id: str = Field(alias="regionId")
    utility: float
    information_gain: float = Field(alias="infoGain")
    threat_score: float = Field(alias="threatScore")
    uncertainty: float
    tracking_value: float = Field(alias="trackingValue")
    scan_cost: float = Field(alias="scanCost")
    reason: str


class CandidateRank(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    utility: float
    info_gain: float = Field(alias="infoGain")
    threat_score: float = Field(alias="threatScore")
    tracking_value: float = Field(alias="trackingValue")
    scan_cost: float = Field(alias="scanCost")


class ObservationState(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    regions: List[RegionState]
    timestep: int
    budget_remaining: float = Field(alias="budget_remaining")
    budget_total: float = Field(alias="budget_total")
    budget_remaining_frac: float = Field(alias="budget_remaining_frac")
    current_scan: Optional[str] = Field(default=None, alias="current_scan")
    scenario: str
    intelligence: Dict[str, int]


class SimulationResetRequest(BaseModel):
    scenario: str
    seed: Optional[int] = None
    strategy: str = "ADAPT_SCAN"
    num_regions: int = 20


class SimulationStepRequest(BaseModel):
    session_id: str
    override_region_id: Optional[str] = None


class EventRequest(BaseModel):
    session_id: str
    event_type: str
