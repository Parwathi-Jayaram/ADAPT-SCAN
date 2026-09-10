import { resetSimulation, stepSimulation, getSimulationState, getRegions, getMetrics, getScenarios, triggerEvent } from '../services/simulationManager.js'

export function handleReset(req, res) {
  try {
    const body = req.body || {}
    const result = resetSimulation({
      scenario: body.scenario,
      strategy: body.strategy,
      num_regions: body.num_regions,
      seed: body.seed,
      budget_total: body.budget_total,
    })
    return res.status(200).json(result)
  } catch (error) {
    return res.status(400).json({ success: false, message: error.message })
  }
}

export function handleStep(req, res) {
  try {
    const body = req.body || {}
    const result = stepSimulation(body.session_id, body.override_region_id)
    return res.status(200).json(result)
  } catch (error) {
    return res.status(400).json({ success: false, message: error.message })
  }
}

export function handleRegions(req, res) {
  try {
    const sessionId = req.query.session_id
    if (!sessionId) return res.status(400).json({ success: false, message: 'session_id is required.' })
    const result = getRegions(sessionId)
    return res.status(200).json(result)
  } catch (error) {
    return res.status(400).json({ success: false, message: error.message })
  }
}

export function handleMetrics(req, res) {
  try {
    const sessionId = req.query.session_id
    if (!sessionId) return res.status(400).json({ success: false, message: 'session_id is required.' })
    const result = getMetrics(sessionId)
    return res.status(200).json(result)
  } catch (error) {
    return res.status(400).json({ success: false, message: error.message })
  }
}

export function handleScenarios(req, res) {
  try {
    const result = getScenarios()
    return res.status(200).json(result)
  } catch (error) {
    return res.status(400).json({ success: false, message: error.message })
  }
}

export function handleTriggerEvent(req, res) {
  try {
    const body = req.body || {}
    if (!body.session_id || !body.event_type) {
      return res.status(400).json({ success: false, message: 'session_id and event_type are required.' })
    }
    const result = triggerEvent(body.session_id, body.event_type)
    return res.status(200).json(result)
  } catch (error) {
    return res.status(400).json({ success: false, message: error.message })
  }
}
