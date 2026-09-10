import express from 'express'
import { addSimulationResult, createSession, getMySessions, getSessionById, updateSession } from '../controllers/scanSessionController.js'
import { protect } from '../middleware/authMiddleware.js'

const router = express.Router()

router.get('/sessions', protect, getMySessions)
router.post('/sessions', protect, createSession)
router.get('/sessions/:id', protect, getSessionById)
router.put('/sessions/:id', protect, updateSession)
router.post('/sessions/:id/results', protect, addSimulationResult)

export default router
