const API_BASE = import.meta.env.DEV
  ? "http://localhost:5000"
  : "http://localhost:5000"

export type SignalType = "RADAR" | "COMM" | "ECM" | "UNKNOWN" | "SILENT"
export type Strategy = "RANDOM" | "ROUND_ROBIN" | "THREAT_PRIORITY" | "ADAPT_SCAN"
export type Theme = "dark" | "light"
export type Lang = "en" | "hi" | "fr" | "es" | "de"
export type Page = "overview" | "emitters" | "decisions" | "analytics" | "benchmarks" | "settings"

export interface Region {
  id: string
  freqMHz: number
  bwMHz: number
  signalStrength: number
  threatLevel: number
  uncertainty: number
  beliefProb: number
  lastScanned: number
  signalType: SignalType
  active: boolean
  priority: number
}

export interface ScanRecord {
  step: number
  regionId: string
  infoGain: number
  threatValue: number
  uncertainty: number
  trackingUrgency: number
  scanCost: number
  detectedSignal: boolean
  explanation: string
  strategy: Strategy
}

export interface Candidate {
  id: string
  utility: number
  infoGain: number
  threatScore: number
  trackingValue: number
  scanCost: number
}

export interface ScanDelta {
  regionId: string
  beliefBefore: number
  beliefAfter: number
  uncBefore: number
  uncAfter: number
  statusBefore: string
  statusAfter: string
  detected: boolean
}

export interface DecisionEvent {
  id: number
  step: number
  elapsed: number
  type: "ai" | "override" | "event"
  regionId: string
  label: string
  detected?: boolean
  record?: ScanRecord
}

export interface ObservationState {
  regions: Region[]
  timestep: number
  budget_remaining: number
  budget_total: number
  budget_remaining_frac: number
  current_scan: string | null
  scenario: string
  intelligence: Record<string, number>
}

export interface StepResponse {
  session_id: string
  step: number
  done: boolean
  observation_state: ObservationState
  decision: {
    region_id: string
    utility: number
    information_gain: number
    threat_score: number
    uncertainty: number
    tracking_value: number
    scan_cost: number
    reason: string
  } | null
  scan_result: any
  scan_delta: ScanDelta | null
  scan_record: ScanRecord | null
  candidates: Candidate[]
  belief_state: Record<string, number>
  history: ScanRecord[]
  decision_events: DecisionEvent[]
  metrics: {
    detection_rate: number
    avg_info_gain: number
    avg_threat: number
    budget_remaining: number
    budget_total: number
  }
}

export interface ResetResponse {
  session_id: string
  strategy: string
  scenario: string
  observation_state: ObservationState
  belief_state: Record<string, number>
  done: boolean
}

export interface Scenario {
  id: string
  name: string
  description: string
  num_emitters: number
  noise_level: string
  budget: number
}

export interface SimConfig {
  emitterCount: number
  noiseLevel: number
  scanBudget: number
  scenario: string
  strategy: Strategy
  dynamicEvents: boolean
  speed: number
}

async function post(path: string, body: any) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`API error ${res.status}`)
  return res.json()
}

async function get(path: string) {
  const res = await fetch(`${API_BASE}${path}`)
  if (!res.ok) throw new Error(`API error ${res.status}`)
  return res.json()
}

export const api = {
  async reset(data: {
    scenario: string
    seed?: number
    strategy: string
    num_regions: number
  }): Promise<ResetResponse> {
    return post("/api/simulation/reset", data)
  },
  async step(data: {
    session_id: string
    override_region_id?: string
  }): Promise<StepResponse> {
    return post("/api/simulation/step", data)
  },
  async getRegions(session_id: string): Promise<{ regions: Region[] }> {
    return get(`/api/regions?session_id=${encodeURIComponent(session_id)}`)
  },
  async getMetrics(session_id: string) {
    return get(`/api/metrics?session_id=${encodeURIComponent(session_id)}`)
  },
  async getScenarios(): Promise<Scenario[]> {
    return get("/api/scenarios")
  },
  async triggerEvent(session_id: string, event_type: string) {
    return post("/api/events", { session_id, event_type })
  },
  async getLanguage(key = "default") {
    return get(`/api/language?key=${encodeURIComponent(key)}`)
  },
  async setLanguage(key = "default", value: string) {
    return post("/api/language", { key, value })
  },
}
