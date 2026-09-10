import express from 'express'
import {
  handleReset,
  handleStep,
  handleRegions,
  handleMetrics,
  handleScenarios,
  handleTriggerEvent,
} from '../controllers/simulationController.js'

const router = express.Router()

router.post('/simulation/reset', handleReset)
router.post('/simulation/step', handleStep)
router.get('/regions', handleRegions)
router.get('/metrics', handleMetrics)
router.get('/scenarios', handleScenarios)
router.post('/events', handleTriggerEvent)

export default router
