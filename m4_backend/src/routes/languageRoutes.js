import express from 'express'

const router = express.Router()
const preferences = new Map()

router.get('/', (req, res) => {
  const key = String(req.query.key || 'default')
  const value = preferences.get(key)
  return res.status(200).json({ key, value: value || 'en' })
})

router.post('/', (req, res) => {
  const body = req.body || {}
  const key = String(body.key || 'default')
  const value = String(body.value || 'en')
  preferences.set(key, value)
  return res.status(200).json({ key, value })
})

export default router
