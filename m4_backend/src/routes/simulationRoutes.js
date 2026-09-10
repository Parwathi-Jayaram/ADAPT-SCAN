import express from 'express'

const router = express.Router()

router.use((req, res) => {
  res.status(404).json({ success: false, message: 'Legacy simulation endpoint not available. Use /api/simulation/reset and /api/simulation/step.' })
})

export default router
