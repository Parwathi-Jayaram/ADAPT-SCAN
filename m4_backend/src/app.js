import express from 'express'
import cors from 'cors'
import helmet from 'helmet'
import authRoutes from './routes/authRoutes.js'
import scanRoutes from './routes/scanRoutes.js'
import simulationRoutes from './routes/simulationRoutes.js'
import publicSimulationRoutes from './routes/publicSimulationRoutes.js'
import { errorHandler, notFoundHandler } from './middleware/errorHandler.js'

const app = express()

app.use(helmet())
app.use(cors({
  origin: true,
  credentials: true,
}))
app.use(express.json())

app.use('/api/auth', authRoutes)

app.get('/api/health', (req, res) => {
  res.json({
    ok: true,
    message: 'Adapt Scan backend is running',
    timestamp: new Date().toISOString(),
  })
})

app.use('/api', scanRoutes)
app.use('/api', publicSimulationRoutes)
app.use('/api/simulation', simulationRoutes)

app.get('/', (req, res) => {
  res.json({
    service: 'Adapt Scan API',
    status: 'ready',
  })
})

app.use(notFoundHandler)
app.use(errorHandler)

export default app
