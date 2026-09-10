const simulations = new Map()

const SIGNAL_TYPES = ['RADAR', 'COMM', 'ECM', 'UNKNOWN', 'SILENT']

function rng(min = 0, max = 1) { return min + Math.random() * (max - min) }
function clamp(v, lo = 0, hi = 1) { return Math.max(lo, Math.min(hi, v)) }

function initRegions(count) {
  return Array.from({ length: count }, (_, i) => ({
    id: `R${i + 1}`,
    freqMHz: 100 + i * 250 + Math.floor(rng(0, 100)),
    bwMHz: Math.floor(rng(10, 50)),
    signalStrength: rng(0.1, 0.95),
    threatLevel: rng(0, 1),
    uncertainty: rng(0.55, 1),
    beliefProb: rng(0.3, 0.7),
    lastScanned: -1,
    signalType: SIGNAL_TYPES[Math.floor(rng(0, SIGNAL_TYPES.length))],
    active: Math.random() > 0.35,
    priority: rng(0, 1),
  }))
}

function computeUtility(r, step, strategy) {
  const staleness = r.lastScanned < 0 ? 1 : clamp((step - r.lastScanned) / 12)
  switch (strategy) {
    case 'RANDOM':
      return Math.random()
    case 'ROUND_ROBIN':
      return r.lastScanned < 0 ? 9999 : step - r.lastScanned
    case 'THREAT_PRIORITY':
      return r.threatLevel * r.priority + r.signalStrength * 0.2
    case 'ADAPT_SCAN': {
      const ig = r.uncertainty * staleness
      const tv = r.threatLevel * r.priority
      const tu = staleness * 0.6 + r.uncertainty * 0.4
      const cost = 0.08 + (1 - r.priority) * 0.15
      return (ig * 0.38 + tv * 0.35 + tu * 0.17) / (cost + 0.01)
    }
    default:
      return Math.random()
  }
}

function computeAdaptUtility(r, step) {
  const staleness = r.lastScanned < 0 ? 1 : clamp((step - r.lastScanned) / 12)
  const ig = r.uncertainty * staleness
  const tv = r.threatLevel * r.priority
  const tu = staleness * 0.6 + r.uncertainty * 0.4
  const cost = 0.08 + (1 - r.priority) * 0.15
  return (ig * 0.38 + tv * 0.35 + tu * 0.17) / (cost + 0.01)
}

function selectNext(regions, step, strategy) {
  let best = regions[0]
  let bestU = computeUtility(regions[0], step, strategy)
  for (const r of regions.slice(1)) {
    const u = computeUtility(r, step, strategy)
    if (u > bestU) { bestU = u; best = r }
  }
  return best.id
}

function getTopCandidates(regions, step) {
  return regions
    .map(r => ({
      id: r.id,
      utility: computeAdaptUtility(r, step),
      infoGain: 0,
      threatScore: r.threatLevel,
      trackingValue: 0,
      scanCost: 0.1,
    }))
    .sort((a, b) => b.utility - a.utility)
    .slice(0, 5)
}

function getRegionStatus(r) {
  if (!r.active) return 'SILENT'
  if (r.beliefProb > 0.78) return 'TRACKED'
  if (r.threatLevel > 0.7 && r.beliefProb > 0.5) return 'HIGH PRIORITY'
  if (r.uncertainty > 0.65) return 'UNCERTAIN'
  if (r.lastScanned < 0) return 'NEW'
  return 'OBSERVING'
}

function buildRecord(r, step, strategy, detected) {
  const staleness = r.lastScanned < 0 ? 1 : clamp((step - r.lastScanned) / 12)
  const ig = clamp(r.uncertainty * staleness)
  const tv = clamp(r.threatLevel * r.priority)
  const tu = clamp(staleness * 0.6 + r.uncertainty * 0.4)
  const cost = clamp(0.08 + (1 - r.priority) * 0.15)
  const why = []
  if (ig > 0.6) why.push('high information gain')
  if (tv > 0.55) why.push('elevated threat value')
  if (staleness > 0.7) why.push('stale observation')
  if (tu > 0.5) why.push('tracking urgency')
  const explanation = why.length
    ? `${r.id} selected — ${why.join(', ')}; cost/utility ratio optimal under ${strategy.replace('_', '-')} policy.`
    : `${r.id} selected by ${strategy.replace('_', ' ').toLowerCase()} policy.`
  return {
    step,
    regionId: r.id,
    infoGain: ig,
    threatValue: tv,
    uncertainty: r.uncertainty,
    trackingUrgency: tu,
    scanCost: cost,
    detectedSignal: detected,
    explanation,
    strategy,
  }
}

function buildObservation(regionId, timestep, seed) {
  const detected = (seed + timestep + regionId.length) % 5 !== 0
  return {
    region_id: regionId,
    detected,
    strength: detected ? 0.63 : 0.18,
    bandwidth: 0.41,
    snr: detected ? 7.2 : 2.1,
    confidence: detected ? 0.72 : 0.31,
    features: ['synthetic', detected ? 'signal-present' : 'noise-dominant'],
  }
}

function createSimulation(payload = {}) {
  const budgetTotal = Number(payload.budget_total) || 100
  const scenario = payload.scenario || 'NORMAL'
  const strategy = payload.strategy || 'ADAPT_SCAN'
  const numRegions = Number(payload.num_regions) || 12
  const seed = Number.isInteger(payload.seed) ? payload.seed : Math.floor(Math.random() * 10000)

  const sim = {
    session_id: payload.session_id || `sim-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    scenario,
    strategy,
    seed,
    timestep: 0,
    budget_total: budgetTotal,
    budget_remaining: budgetTotal,
    current_scan: null,
    regions: initRegions(numRegions),
    history: [],
    decision_events: [],
    done: false,
  }

  simulations.set(sim.session_id, sim)
  return sim
}

function getSimulation(sessionId) {
  const sim = simulations.get(sessionId)
  if (!sim) throw new Error('Simulation not found.')
  return sim
}

export function resetSimulation(payload = {}) {
  const existing = payload.session_id ? simulations.get(payload.session_id) : null
  const sim = createSimulation({
    session_id: existing ? existing.session_id : undefined,
    scenario: payload.scenario || existing?.scenario || 'NORMAL',
    strategy: payload.strategy || existing?.strategy || 'ADAPT_SCAN',
    num_regions: payload.num_regions || existing?.regions?.length || 12,
    budget_total: payload.budget_total || existing?.budget_total || 100,
    seed: payload.seed ?? existing?.seed,
  })
  return buildResponse(sim)
}

export function stepSimulation(sessionId, overrideRegionId) {
  const sim = getSimulation(sessionId)
  if (sim.done) return buildResponse(sim)

  const selectedAction = overrideRegionId || selectNext(sim.regions, sim.timestep, sim.strategy)
  const region = sim.regions.find(r => r.id === selectedAction)
  if (!region) throw new Error('Unknown scan region.')
  if (sim.budget_remaining < 1) {
    sim.done = true
    return buildResponse(sim)
  }

  sim.timestep += 1
  sim.budget_remaining -= 1
  sim.current_scan = selectedAction

  const beliefBefore = region.beliefProb
  const uncBefore = region.uncertainty
  const statusBefore = getRegionStatus(region)

  const observation = buildObservation(selectedAction, sim.timestep, sim.seed)
  const detected = observation.detected

  region.lastScanned = sim.timestep
  region.beliefProb = clamp(detected ? beliefBefore * 0.3 + 0.65 : beliefBefore * 0.6)
  region.uncertainty = clamp(uncBefore * (detected ? 0.5 : 0.85))

  const statusAfter = getRegionStatus(region)

  const scanRecord = buildRecord(region, sim.timestep, sim.strategy, detected)
  sim.history.push(scanRecord)

  const scanDelta = {
    regionId: selectedAction,
    beliefBefore: Math.round(beliefBefore * 100) / 100,
    beliefAfter: Math.round(region.beliefProb * 100) / 100,
    uncBefore: Math.round(uncBefore * 100) / 100,
    uncAfter: Math.round(region.uncertainty * 100) / 100,
    statusBefore,
    statusAfter,
    detected,
  }

  const utility = computeAdaptUtility(region, sim.timestep)
  const informationGain = scanRecord.infoGain
  const decision = {
    region_id: selectedAction,
    utility: Math.round(utility * 100) / 100,
    information_gain: Math.round(informationGain * 100) / 100,
    threat_score: Math.round(region.threatLevel * 100) / 100,
    uncertainty: Math.round(region.uncertainty * 100) / 100,
    tracking_value: Math.round(region.existence || region.beliefProb * 100) / 100,
    scan_cost: Math.round(scanRecord.scanCost * 100) / 100,
    reason: `Selected ${selectedAction} because it has high uncertainty and expected information value relative to its scan cost.`,
  }

  const eventId = sim.decision_events.length
  sim.decision_events.push({
    id: eventId,
    step: sim.timestep,
    elapsed: sim.timestep * 1.2,
    type: overrideRegionId ? 'override' : 'ai',
    regionId: selectedAction,
    label: decision.reason,
    detected,
    record: scanRecord,
  })

  if (sim.budget_remaining <= 0) {
    sim.done = true
  }

  return buildResponse(sim, {
    decision,
    scan_result: observation,
    scan_delta: scanDelta,
    scan_record: scanRecord,
  })
}

export function getSimulationState(sessionId) {
  return buildResponse(getSimulation(sessionId))
}

export function getRegions(sessionId) {
  const sim = getSimulation(sessionId)
  return { regions: sim.regions }
}

export function getMetrics(sessionId) {
  const sim = getSimulation(sessionId)
  const history = sim.history
  const detectionRate = history.length ? history.filter(r => r.detectedSignal).length / history.length : 0
  const avgInfoGain = history.length ? history.reduce((s, r) => s + r.infoGain, 0) / history.length : 0
  const avgThreat = history.length ? history.reduce((s, r) => s + r.threatValue, 0) / history.length : 0
  return {
    detection_rate: Math.round(detectionRate * 1000) / 1000,
    avg_info_gain: Math.round(avgInfoGain * 1000) / 1000,
    avg_threat: Math.round(avgThreat * 1000) / 1000,
    budget_remaining: sim.budget_remaining,
    budget_total: sim.budget_total,
  }
}

export function getScenarios() {
  return [
    { id: 'NORMAL', name: 'Normal', description: 'Low complexity, low uncertainty', num_emitters: 8, noise_level: '0.12', budget: 100 },
    { id: 'DYNAMIC', name: 'Dynamic Env', description: 'Changing emitters', num_emitters: 12, noise_level: '0.30', budget: 100 },
    { id: 'HIGH_NOISE', name: 'High Noise', description: 'Reduced observation quality', num_emitters: 10, noise_level: '0.72', budget: 100 },
    { id: 'LIMITED', name: 'Limited Budget', description: 'Resource-constrained sensing', num_emitters: 12, noise_level: '0.25', budget: 35 },
    { id: 'SUDDEN', name: 'Sudden Threat', description: 'New high-priority emitter', num_emitters: 14, noise_level: '0.30', budget: 100 },
    { id: 'HIGH_UNC', name: 'High Uncertainty', description: 'Large information gaps', num_emitters: 16, noise_level: '0.60', budget: 100 },
    { id: 'STRESS', name: 'Stress Test', description: 'Multiple simultaneous changes', num_emitters: 20, noise_level: '0.80', budget: 40 },
  ]
}

export function triggerEvent(sessionId, eventType) {
  const sim = getSimulation(sessionId)
  switch (eventType) {
    case 'introduce_emitter': {
      const inactive = sim.regions.filter(r => !r.active)
      if (inactive.length > 0) {
        const r = inactive[Math.floor(Math.random() * inactive.length)]
        r.active = true
        r.threatLevel = rng(0.5, 1)
        r.priority = rng(0.5, 1)
      }
      break
    }
    case 'increase_noise':
      sim.regions.forEach(r => { r.uncertainty = clamp(r.uncertainty + 0.15) })
      break
    case 'reduce_budget':
      sim.budget_remaining = Math.max(0, Math.floor(sim.budget_remaining * 0.85))
      if (sim.budget_remaining <= 0) sim.done = true
      break
    case 'uncertainty_spike': {
      const active = sim.regions.filter(r => r.active)
      if (active.length > 0) {
        const r = active[Math.floor(Math.random() * active.length)]
        r.uncertainty = 1
      }
      break
    }
    case 'signal_disappears': {
      const active = sim.regions.filter(r => r.active)
      if (active.length > 0) {
        const r = active[Math.floor(Math.random() * active.length)]
        r.active = false
        r.beliefProb = 0
      }
      break
    }
    case 'reset_environment':
      sim.regions = initRegions(sim.regions.length)
      sim.history = []
      sim.decision_events = []
      sim.timestep = 0
      sim.budget_remaining = sim.budget_total
      sim.current_scan = null
      sim.done = false
      break
  }
  return getSimulationState(sessionId)
}

function buildResponse(sim, extra = {}) {
  const intelligence = {
    detected_count: sim.regions.filter(r => r.active && r.beliefProb >= 0.5).length,
    high_priority_count: sim.regions.filter(r => r.threatLevel >= 0.7).length,
    uncertainty_hotspots: sim.regions.filter(r => r.uncertainty >= 0.6).length,
  }

  const history = sim.history
  const detectionRate = history.length ? history.filter(r => r.detectedSignal).length / history.length : 0
  const avgInfoGain = history.length ? history.reduce((s, r) => s + r.infoGain, 0) / history.length : 0
  const avgThreat = history.length ? history.reduce((s, r) => s + r.threatValue, 0) / history.length : 0

  return {
    session_id: sim.session_id,
    step: sim.timestep,
    done: sim.done,
    observation_state: {
      regions: sim.regions,
      timestep: sim.timestep,
      budget_remaining: sim.budget_remaining,
      budget_total: sim.budget_total,
      budget_remaining_frac: sim.budget_total > 0 ? sim.budget_remaining / sim.budget_total : 0,
      current_scan: sim.current_scan,
      scenario: sim.scenario,
      intelligence,
    },
    decision: extra.decision || null,
    scan_result: extra.scan_result || null,
    scan_delta: extra.scan_delta || null,
    scan_record: extra.scan_record || null,
    candidates: getTopCandidates(sim.regions, sim.timestep),
    belief_state: Object.fromEntries(sim.regions.map(r => [r.id, Math.round(r.beliefProb * 100) / 100])),
    history: sim.history,
    decision_events: sim.decision_events,
    metrics: {
      detection_rate: Math.round(detectionRate * 1000) / 1000,
      avg_info_gain: Math.round(avgInfoGain * 1000) / 1000,
      avg_threat: Math.round(avgThreat * 1000) / 1000,
      budget_remaining: sim.budget_remaining,
      budget_total: sim.budget_total,
    },
    ...extra,
  }
}
