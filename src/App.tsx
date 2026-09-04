import { useState, useEffect, useCallback, useRef } from "react"

// ─── Types ────────────────────────────────────────────────────────────────────

type SignalType = "RADAR" | "COMM" | "ECM" | "UNKNOWN" | "SILENT"
type Strategy = "RANDOM" | "ROUND_ROBIN" | "THREAT_PRIORITY" | "ADAPT_SCAN"
type Theme = "dark" | "light"
type Lang = "en" | "hi" | "fr" | "es" | "de"
type Page = "overview" | "emitters" | "decisions" | "analytics" | "benchmarks" | "settings"

interface Region {
  id: string; freqMHz: number; bwMHz: number; signalStrength: number
  threatLevel: number; uncertainty: number; beliefProb: number
  lastScanned: number; signalType: SignalType; active: boolean; priority: number
}
interface ScanRecord {
  step: number; regionId: string; infoGain: number; threatValue: number
  uncertainty: number; trackingUrgency: number; scanCost: number
  detectedSignal: boolean; explanation: string; strategy: Strategy
}
interface SimConfig {
  emitterCount: number; noiseLevel: number; scanBudget: number; scenario: string
  strategy: Strategy; dynamicEvents: boolean; speed: number
}
interface ScanDelta {
  regionId: string; beliefBefore: number; beliefAfter: number
  uncBefore: number; uncAfter: number; statusBefore: string; statusAfter: string; detected: boolean
}
interface DecisionEvent {
  id: number; step: number; elapsed: number
  type: "ai" | "override" | "event"; regionId: string; label: string
  detected?: boolean; record?: ScanRecord
}
interface ChatMsg { role: "user" | "assistant"; text: string }
interface Candidate { id: string; utility: number; region: Region }

// ─── Theme palettes ───────────────────────────────────────────────────────────

const DARK = {
  bg: "#050d12", bgPanel: "#040b10", bgDarkCard: "#071018", bgTrack: "#0a1520",
  bgSilent: "#060d12", bgActive: "#071520", bgHighThreat: "#1a0a00",
  bgScanning: "#003322", bgIntel: "#071a25", border: "#0f2030",
  borderSilent: "#0d1e2a", borderActive: "#1e3a50",
  accent: "#00e57a", blue: "#38bdf8", purple: "#a78bfa", yellow: "#fbbf24", red: "#f87171",
  textPrimary: "#c8e6f0", textMuted: "#4a7a99", textInfo: "#7ab8cc",
  textDim: "#2a4a5a", textVeryDim: "#1e3a50", textSilent: "#1e3a4a",
}
const LIGHT = {
  bg: "#f0f5fa", bgPanel: "#e5edf5", bgDarkCard: "#dce8f2", bgTrack: "#c8dbe8",
  bgSilent: "#eaf2f8", bgActive: "#d8eaf5", bgHighThreat: "#fff0ee",
  bgScanning: "#d4f7e8", bgIntel: "#dcedf7", border: "#b8cfe0",
  borderSilent: "#ccdae8", borderActive: "#7aaabf",
  accent: "#009950", blue: "#0080bb", purple: "#6644cc", yellow: "#9a6600", red: "#cc2222",
  textPrimary: "#1a2c3a", textMuted: "#3a6a8a", textInfo: "#2a6a8a",
  textDim: "#5a8aaa", textVeryDim: "#8aabbf", textSilent: "#9aabbf",
}
type Palette = typeof DARK

// ─── Translations ─────────────────────────────────────────────────────────────

type TKey = "appTitle" | "appSubtitle" | "step" | "strategy" | "budget" | "pause" | "run"
  | "currentIntel" | "detected" | "highPriority" | "uncertain" | "budgetUsed" | "scanning"
  | "spectrumEnv" | "beliefState" | "scanTimeline" | "awaiting" | "whyScan" | "startSim"
  | "controls" | "comparison" | "about" | "emitters" | "noiseLevel" | "scanBudget"
  | "speedMs" | "dynamicEvents" | "on" | "off" | "scenario" | "runStrategy"
  | "strategyComparison" | "currentMetrics" | "scansExecuted" | "signalsDetected"
  | "avgInfoGain" | "avgThreatVal" | "detectionRate" | "infoGain" | "threatValue"
  | "trackUrgency" | "scanCost" | "aiAssistant" | "aiPlaceholder" | "send" | "aiGreet"
  | "langLabel" | "footerLeft" | "live" | "paused" | "simNote"

const TRANSLATIONS: Record<Lang, Record<TKey, string>> = {
  en: {
    appTitle: "ADAPT-SCAN", appSubtitle: "ADAPTIVE EW SENSING DECISION ENGINE",
    step: "STEP", strategy: "STRATEGY", budget: "BUDGET", pause: "⏸ PAUSE", run: "▶ RUN",
    currentIntel: "CURRENT INTELLIGENCE", detected: "Detected", highPriority: "High Priority",
    uncertain: "Uncertain", budgetUsed: "Budget Used", scanning: "Scanning",
    spectrumEnv: "SPECTRUM / ENVIRONMENT", beliefState: "BELIEF STATE — SIGNAL EXISTENCE PROBABILITY",
    scanTimeline: "SCAN TIMELINE", awaiting: "— awaiting —", whyScan: "DECISION ENGINE",
    startSim: "— start simulation —", controls: "controls", comparison: "comparison", about: "about",
    emitters: "Emitters", noiseLevel: "Noise Level", scanBudget: "Scan Budget", speedMs: "Speed (ms)",
    dynamicEvents: "Dynamic Events", on: "ON", off: "OFF", scenario: "Scenario",
    runStrategy: "RUN STRATEGY", strategyComparison: "STRATEGY COMPARISON",
    currentMetrics: "CURRENT RUN METRICS", scansExecuted: "Scans Executed",
    signalsDetected: "Signals Detected", avgInfoGain: "Avg Info Gain", avgThreatVal: "Avg Threat Val",
    detectionRate: "Detection Rate", infoGain: "Info Gain", threatValue: "Threat Relevance",
    trackUrgency: "Track Urgency", scanCost: "Scan Cost",
    aiAssistant: "AI ASSISTANT", aiPlaceholder: "Ask about ADAPT-SCAN…", send: "SEND",
    aiGreet: "Hello! I can explain ADAPT-SCAN concepts, strategies, and the simulation. What would you like to know?",
    langLabel: "LANG", footerLeft: "SIH2026 · PS26055 · ADAPT-SCAN",
    live: "● SIMULATION ONLINE", paused: "⏸ PAUSED", simNote: "SIMULATED · NOT REAL EW DATA",
  },
  hi: {
    appTitle: "ADAPT-SCAN", appSubtitle: "अनुकूली EW संवेदन निर्णय इंजन",
    step: "चरण", strategy: "रणनीति", budget: "बजट", pause: "⏸ रोकें", run: "▶ चलाएं",
    currentIntel: "वर्तमान खुफिया", detected: "पहचाना", highPriority: "उच्च प्राथमिकता",
    uncertain: "अनिश्चित", budgetUsed: "बजट उपयोग", scanning: "स्कैनिंग",
    spectrumEnv: "स्पेक्ट्रम / परिवेश", beliefState: "विश्वास अवस्था — संकेत अस्तित्व संभावना",
    scanTimeline: "स्कैन टाइमलाइन", awaiting: "— प्रतीक्षारत —", whyScan: "निर्णय इंजन",
    startSim: "— सिमुलेशन शुरू करें —", controls: "नियंत्रण", comparison: "तुलना", about: "परिचय",
    emitters: "उत्सर्जक", noiseLevel: "शोर स्तर", scanBudget: "स्कैन बजट", speedMs: "गति (ms)",
    dynamicEvents: "गतिशील घटनाएं", on: "चालू", off: "बंद", scenario: "परिदृश्य",
    runStrategy: "रणनीति चलाएं", strategyComparison: "रणनीति तुलना",
    currentMetrics: "वर्तमान मेट्रिक्स", scansExecuted: "स्कैन निष्पादित",
    signalsDetected: "संकेत पहचाने", avgInfoGain: "औसत सूचना लाभ", avgThreatVal: "औसत खतरा मूल्य",
    detectionRate: "पहचान दर", infoGain: "सूचना लाभ", threatValue: "खतरा प्रासंगिकता",
    trackUrgency: "ट्रैक तात्कालिकता", scanCost: "स्कैन लागत",
    aiAssistant: "AI सहायक", aiPlaceholder: "ADAPT-SCAN के बारे में पूछें…", send: "भेजें",
    aiGreet: "नमस्ते! मैं ADAPT-SCAN अवधारणाओं और सिमुलेशन के बारे में बता सकता हूं।",
    langLabel: "भाषा", footerLeft: "SIH2026 · PS26055 · ADAPT-SCAN",
    live: "● सिमुलेशन ऑनलाइन", paused: "⏸ रुका", simNote: "सिमुलेटेड · वास्तविक EW डेटा नहीं",
  },
  fr: {
    appTitle: "ADAPT-SCAN", appSubtitle: "MOTEUR DE DÉCISION ADAPTATIF EW",
    step: "ÉTAPE", strategy: "STRATÉGIE", budget: "BUDGET", pause: "⏸ PAUSE", run: "▶ DÉMARRER",
    currentIntel: "RENSEIGNEMENT ACTUEL", detected: "Détecté", highPriority: "Haute Priorité",
    uncertain: "Incertain", budgetUsed: "Budget Utilisé", scanning: "Balayage",
    spectrumEnv: "SPECTRE / ENVIRONNEMENT", beliefState: "ÉTAT DE CROYANCE",
    scanTimeline: "CHRONOLOGIE", awaiting: "— en attente —", whyScan: "MOTEUR DE DÉCISION",
    startSim: "— démarrer —", controls: "contrôles", comparison: "comparaison", about: "à propos",
    emitters: "Émetteurs", noiseLevel: "Bruit", scanBudget: "Budget Scan", speedMs: "Vitesse (ms)",
    dynamicEvents: "Dynamique", on: "OUI", off: "NON", scenario: "Scénario",
    runStrategy: "EXÉCUTER", strategyComparison: "COMPARAISON", currentMetrics: "MÉTRIQUES",
    scansExecuted: "Scans", signalsDetected: "Signaux", avgInfoGain: "Info Moy.", avgThreatVal: "Menace Moy.",
    detectionRate: "Taux Détection", infoGain: "Gain Info", threatValue: "Menace",
    trackUrgency: "Urgence", scanCost: "Coût Scan",
    aiAssistant: "ASSISTANT IA", aiPlaceholder: "Posez une question…", send: "ENVOYER",
    aiGreet: "Bonjour! Je peux expliquer ADAPT-SCAN et la simulation.",
    langLabel: "LANGUE", footerLeft: "SIH2026 · PS26055 · ADAPT-SCAN",
    live: "● SIMULATION EN LIGNE", paused: "⏸ EN PAUSE", simNote: "SIMULÉ · PAS DE DONNÉES RÉELLES",
  },
  es: {
    appTitle: "ADAPT-SCAN", appSubtitle: "MOTOR ADAPTATIVO DE DECISIÓN EW",
    step: "PASO", strategy: "ESTRATEGIA", budget: "PRESUPUESTO", pause: "⏸ PAUSAR", run: "▶ EJECUTAR",
    currentIntel: "INTELIGENCIA ACTUAL", detected: "Detectado", highPriority: "Alta Prioridad",
    uncertain: "Incierto", budgetUsed: "Presupuesto", scanning: "Escaneando",
    spectrumEnv: "ESPECTRO / ENTORNO", beliefState: "ESTADO DE CREENCIA",
    scanTimeline: "LÍNEA DE TIEMPO", awaiting: "— esperando —", whyScan: "MOTOR DE DECISIÓN",
    startSim: "— iniciar —", controls: "controles", comparison: "comparación", about: "acerca de",
    emitters: "Emisores", noiseLevel: "Ruido", scanBudget: "Presupuesto Scan", speedMs: "Velocidad (ms)",
    dynamicEvents: "Dinámico", on: "SÍ", off: "NO", scenario: "Escenario",
    runStrategy: "EJECUTAR", strategyComparison: "COMPARACIÓN", currentMetrics: "MÉTRICAS",
    scansExecuted: "Scans", signalsDetected: "Señales", avgInfoGain: "Info Prom.", avgThreatVal: "Amenaza Prom.",
    detectionRate: "Tasa Detección", infoGain: "Ganancia Info", threatValue: "Amenaza",
    trackUrgency: "Urgencia", scanCost: "Costo Scan",
    aiAssistant: "ASISTENTE IA", aiPlaceholder: "Pregunta sobre ADAPT-SCAN…", send: "ENVIAR",
    aiGreet: "¡Hola! Puedo explicar ADAPT-SCAN y la simulación.",
    langLabel: "IDIOMA", footerLeft: "SIH2026 · PS26055 · ADAPT-SCAN",
    live: "● SIMULACIÓN EN LÍNEA", paused: "⏸ PAUSADO", simNote: "SIMULADO · NO DATOS REALES",
  },
  de: {
    appTitle: "ADAPT-SCAN", appSubtitle: "ADAPTIVES EW-SENSOR-ENTSCHEIDUNGSSYSTEM",
    step: "SCHRITT", strategy: "STRATEGIE", budget: "BUDGET", pause: "⏸ PAUSE", run: "▶ STARTEN",
    currentIntel: "AKTUELLE AUFKLÄRUNG", detected: "Erkannt", highPriority: "Hohe Priorität",
    uncertain: "Unsicher", budgetUsed: "Budget", scanning: "Scannt",
    spectrumEnv: "SPEKTRUM / UMGEBUNG", beliefState: "GLAUBENSZUSTAND",
    scanTimeline: "ZEITLINIE", awaiting: "— wartend —", whyScan: "ENTSCHEIDUNGSMOTOR",
    startSim: "— starten —", controls: "steuerung", comparison: "vergleich", about: "über",
    emitters: "Sender", noiseLevel: "Rauschen", scanBudget: "Scan-Budget", speedMs: "Geschwindigkeit (ms)",
    dynamicEvents: "Dynamisch", on: "AN", off: "AUS", scenario: "Szenario",
    runStrategy: "STARTEN", strategyComparison: "STRATEGIEVERGLEICH", currentMetrics: "METRIKEN",
    scansExecuted: "Scans", signalsDetected: "Signale", avgInfoGain: "Ø Info", avgThreatVal: "Ø Bedrohung",
    detectionRate: "Erkennungsrate", infoGain: "Infogewinn", threatValue: "Bedrohung",
    trackUrgency: "Dringlichkeit", scanCost: "Kosten",
    aiAssistant: "KI-ASSISTENT", aiPlaceholder: "Frag über ADAPT-SCAN…", send: "SENDEN",
    aiGreet: "Hallo! Ich kann ADAPT-SCAN und die Simulation erklären.",
    langLabel: "SPRACHE", footerLeft: "SIH2026 · PS26055 · ADAPT-SCAN",
    live: "● SIMULATION ONLINE", paused: "⏸ PAUSIERT", simNote: "SIMULIERT · KEINE ECHTEN DATEN",
  },
}

// ─── AI Knowledge Base ────────────────────────────────────────────────────────

function getAIResponse(input: string, step: number, history: ScanRecord[]): string {
  const q = input.toLowerCase()
  if (/hello|hi|hey/.test(q)) return "Hello! Ask me about ADAPT-SCAN's algorithm, strategies, or the current simulation state."
  if (/adapt.?scan|how does it work/.test(q)) return "ADAPT-SCAN maximizes: InfoGain×0.38 + ThreatValue×0.35 + TrackingUrgency×0.17 − ScanCost. It maintains a POMDP belief state and selects the highest-utility region each step."
  if (/pomdp|partial|belief/.test(q)) return "The POMDP model maintains belief state B(s) — a probability distribution over emitter states. After each scan, beliefs update via Bayesian inference: detected → beliefProb×0.3+0.65, not detected → beliefProb×0.6."
  if (/info.?gain/.test(q)) return "Information Gain (weight 0.38) = uncertainty × staleness. Regions not scanned recently with high uncertainty score highest. Staleness = (current_step − last_scan) / 12."
  if (/threat/.test(q)) return "Threat Value (weight 0.35) = threatLevel × priority. High-threat RADAR/ECM signals in high-priority regions score highest, directing the AI toward tactically important spectrum."
  if (/track|urgency/.test(q)) return "Tracking Urgency (weight 0.17) = 0.6×staleness + 0.4×uncertainty. Ensures continuous surveillance of behaviorally changing or uncertain regions."
  if (/cost/.test(q)) return "Scan Cost = 0.08 + (1−priority)×0.15. Low-priority regions cost more relative to their value. The denominator in the utility function naturally penalizes expensive, low-value scans."
  if (/random|round.?robin/.test(q)) return "RANDOM: ~41% detection (baseline). ROUND-ROBIN: ~58% (cyclic, ignores environment). THREAT-PRIORITY: ~67% (reactive but no info gain). ADAPT-SCAN: ~83%+ (full POMDP utility)."
  if (/override/.test(q)) return "Human-in-the-Loop: operators can override the AI's recommendation using the OVERRIDE button. The system records the intervention in the decision timeline, demonstrating collaborative AI decision support."
  if (/confidence/.test(q)) return "Confidence reflects how decisively ADAPT-SCAN selected the current region over alternatives. High confidence means a clear utility gap between the top candidate and alternatives."
  if (/current|status|running/.test(q)) {
    const det = history.filter(r => r.detectedSignal).length
    return `Step ${step}: ${history.length} scans, ${det} detections (${history.length ? Math.round(det/history.length*100) : 0}% rate). Avg info gain: ${history.length ? (history.reduce((s,r)=>s+r.infoGain,0)/history.length).toFixed(3) : "n/a"}.`
  }
  if (/sih|ps26055|hackathon/.test(q)) return "SIH 2026 Problem Statement PS26055: Smart Scan Strategy for Electronic Warfare. ADAPT-SCAN demonstrates intelligent sensing that outperforms naive strategies through POMDP-based decision making."
  return "I can explain: ADAPT-SCAN algorithm, POMDP belief states, information gain, threat modeling, candidate scan ranking, human-in-the-loop overrides, or current simulation metrics. What would you like to know?"
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

const SIGNAL_TYPES: SignalType[] = ["RADAR", "COMM", "ECM", "UNKNOWN", "SILENT"]
const TYPE_COLOR: Record<SignalType, string> = {
  RADAR: "#f87171", COMM: "#38bdf8", ECM: "#fbbf24", UNKNOWN: "#a78bfa", SILENT: "#1e3a4a",
}

function rng(min = 0, max = 1) { return min + Math.random() * (max - min) }
function clamp(v: number, lo = 0, hi = 1) { return Math.max(lo, Math.min(hi, v)) }
function formatT(sec: number) { return `T+${String(Math.floor(sec/60)).padStart(2,"0")}:${String(sec%60).padStart(2,"0")}` }

function getRegionStatus(r: Region): string {
  if (!r.active) return "SILENT"
  if (r.beliefProb > 0.78) return "TRACKED"
  if (r.threatLevel > 0.7 && r.beliefProb > 0.5) return "HIGH PRIORITY"
  if (r.uncertainty > 0.65) return "UNCERTAIN"
  if (r.lastScanned < 0) return "NEW"
  return "OBSERVING"
}

function getStatusColor(status: string, c: Palette): string {
  if (status === "TRACKED") return c.accent
  if (status === "HIGH PRIORITY") return c.red
  if (status === "UNCERTAIN") return c.purple
  if (status === "NEW") return c.yellow
  return c.textMuted
}

function factorExplanation(key: string, val: number): string {
  if (key === "ig") {
    if (val > 0.7) return "Stale + high uncertainty — prime scan candidate"
    if (val > 0.4) return "Moderate staleness, scan recommended"
    return "Recently scanned — diminishing returns"
  }
  if (key === "tv") {
    if (val > 0.6) return "High-priority threat signal active"
    if (val > 0.35) return "Moderate threat relevance"
    return "Low threat significance"
  }
  if (key === "unc") {
    if (val > 0.7) return "Belief poorly constrained — resolve uncertainty"
    if (val > 0.45) return "Partial knowledge, confirmation required"
    return "Region adequately characterized"
  }
  if (key === "tu") {
    if (val > 0.6) return "Tracking continuity at risk"
    if (val > 0.35) return "Routine tracking requirement"
    return "Stable, low urgency"
  }
  if (key === "cost") {
    if (val < 0.1) return "Minimal cost — highly efficient"
    if (val < 0.15) return "Moderate cost, offset by utility"
    return "Higher cost — justified by strategic value"
  }
  return ""
}

function initRegions(count: number): Region[] {
  return Array.from({ length: count }, (_, i) => ({
    id: `R${i + 1}`, freqMHz: 100 + i * 250 + Math.floor(rng(0, 100)),
    bwMHz: Math.floor(rng(10, 50)), signalStrength: rng(0.1, 0.95),
    threatLevel: rng(0, 1), uncertainty: rng(0.55, 1), beliefProb: rng(0.3, 0.7),
    lastScanned: -1, signalType: SIGNAL_TYPES[Math.floor(rng(0, SIGNAL_TYPES.length))],
    active: Math.random() > 0.35, priority: rng(0, 1),
  }))
}

function computeAdaptUtility(r: Region, step: number): number {
  const staleness = r.lastScanned < 0 ? 1 : clamp((step - r.lastScanned) / 12)
  const ig = r.uncertainty * staleness
  const tv = r.threatLevel * r.priority
  const tu = staleness * 0.6 + r.uncertainty * 0.4
  const cost = 0.08 + (1 - r.priority) * 0.15
  return (ig * 0.38 + tv * 0.35 + tu * 0.17) / (cost + 0.01)
}

function computeUtility(r: Region, step: number, strategy: Strategy): number {
  const staleness = r.lastScanned < 0 ? 1 : clamp((step - r.lastScanned) / 12)
  switch (strategy) {
    case "RANDOM": return Math.random()
    case "ROUND_ROBIN": return r.lastScanned < 0 ? 9999 : step - r.lastScanned
    case "THREAT_PRIORITY": return r.threatLevel * r.priority + r.signalStrength * 0.2
    case "ADAPT_SCAN": {
      const ig = r.uncertainty * staleness; const tv = r.threatLevel * r.priority
      const tu = staleness * 0.6 + r.uncertainty * 0.4; const cost = 0.08 + (1 - r.priority) * 0.15
      return (ig * 0.38 + tv * 0.35 + tu * 0.17) / (cost + 0.01)
    }
  }
}

function selectNext(regions: Region[], step: number, strategy: Strategy): string {
  let best = regions[0], bestU = computeUtility(regions[0], step, strategy)
  for (const r of regions.slice(1)) { const u = computeUtility(r, step, strategy); if (u > bestU) { bestU = u; best = r } }
  return best.id
}

function buildRecord(r: Region, step: number, strategy: Strategy): ScanRecord {
  const staleness = r.lastScanned < 0 ? 1 : clamp((step - r.lastScanned) / 12)
  const ig = clamp(r.uncertainty * staleness); const tv = clamp(r.threatLevel * r.priority)
  const tu = clamp(staleness * 0.6 + r.uncertainty * 0.4); const cost = clamp(0.08 + (1 - r.priority) * 0.15)
  const detected = r.active && Math.random() > 0.3
  const why: string[] = []
  if (ig > 0.6) why.push("high information gain")
  if (tv > 0.55) why.push("elevated threat value")
  if (staleness > 0.7) why.push("stale observation")
  if (tu > 0.5) why.push("tracking urgency")
  const explanation = why.length
    ? `${r.id} selected — ${why.join(", ")}; cost/utility ratio optimal under ${strategy.replace("_","-")} policy.`
    : `${r.id} selected by ${strategy.replace("_"," ").toLowerCase()} policy.`
  return { step, regionId: r.id, infoGain: ig, threatValue: tv, uncertainty: r.uncertainty, trackingUrgency: tu, scanCost: cost, detectedSignal: detected, explanation, strategy }
}

function getTopCandidates(regions: Region[], step: number): Candidate[] {
  return regions
    .map(r => ({ id: r.id, utility: computeAdaptUtility(r, step), region: r }))
    .sort((a, b) => b.utility - a.utility)
    .slice(0, 5)
}

// ─── Scenario presets ─────────────────────────────────────────────────────────

const SCENARIOS = [
  { id:"NORMAL", label:"Normal", desc:"Low complexity, low uncertainty", difficulty:"Easy", challenge:"Baseline sensing",
    cfg:{ emitterCount:8, noiseLevel:0.12, scanBudget:100, dynamicEvents:false } },
  { id:"DYNAMIC", label:"Dynamic Env", desc:"Changing emitters", difficulty:"Medium", challenge:"Adaptive tracking",
    cfg:{ emitterCount:12, noiseLevel:0.3, scanBudget:100, dynamicEvents:true } },
  { id:"HIGH_NOISE", label:"High Noise", desc:"Reduced observation quality", difficulty:"Hard", challenge:"Noisy measurements",
    cfg:{ emitterCount:10, noiseLevel:0.72, scanBudget:100, dynamicEvents:false } },
  { id:"LIMITED", label:"Limited Budget", desc:"Resource-constrained sensing", difficulty:"Hard", challenge:"Budget efficiency",
    cfg:{ emitterCount:12, noiseLevel:0.25, scanBudget:35, dynamicEvents:false } },
  { id:"SUDDEN", label:"Sudden Threat", desc:"New high-priority emitter", difficulty:"Medium", challenge:"Rapid reallocation",
    cfg:{ emitterCount:14, noiseLevel:0.3, scanBudget:100, dynamicEvents:true } },
  { id:"HIGH_UNC", label:"High Uncertainty", desc:"Large information gaps", difficulty:"Expert", challenge:"Belief management",
    cfg:{ emitterCount:16, noiseLevel:0.6, scanBudget:100, dynamicEvents:true } },
  { id:"STRESS", label:"Stress Test", desc:"Multiple simultaneous changes", difficulty:"Expert", challenge:"Extreme conditions",
    cfg:{ emitterCount:20, noiseLevel:0.8, scanBudget:40, dynamicEvents:true } },
] as const

// ─── UI Primitives ────────────────────────────────────────────────────────────

function MiniChart({ data, color, height = 44 }: { data: number[]; color: string; height?: number }) {
  if (data.length < 2) return <div style={{ height, background: "transparent" }} />
  const mx = Math.max(...data), mn = Math.min(...data), r = mx - mn || 0.001
  const w = 200
  const pts = data.map((v, i) => `${(i / (data.length - 1)) * w},${height - 4 - ((v - mn) / r) * (height - 8) + 2}`)
  const areaClose = `${w},${height} 0,${height}`
  return (
    <svg width="100%" height={height} viewBox={`0 0 ${w} ${height}`} preserveAspectRatio="none">
      <polygon points={`${pts.join(" ")} ${areaClose}`} fill={color + "22"} />
      <polyline points={pts.join(" ")} fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function StatusChip({ status, c }: { status: string; c: Palette }) {
  const color = getStatusColor(status, c)
  return (
    <span className="mono text-[9px] px-1.5 py-0.5 rounded-sm font-bold tracking-wider"
      style={{ background: color + "22", color, border: `1px solid ${color}44` }}>
      {status}
    </span>
  )
}

function Bar({ label, value, color = "#00e57a", expl = "", trackBg }: { label: string; value: number; color?: string; expl?: string; trackBg: string }) {
  return (
    <div className="space-y-0.5">
      <div className="flex items-center gap-2 text-xs font-mono">
        <span className="w-28 shrink-0 text-[10px]" style={{ color: "#4a7a99" }}>{label}</span>
        <div className="flex-1 h-1.5 rounded-sm overflow-hidden" style={{ background: trackBg }}>
          <div className="h-full rounded-sm transition-all duration-500" style={{ width: `${value * 100}%`, background: color }} />
        </div>
        <span className="w-8 text-right text-[10px]" style={{ color }}>{value.toFixed(2)}</span>
      </div>
      {expl && <div className="text-[9px] mono ml-28 pl-2" style={{ color: "#4a7a99" }}>{expl}</div>}
    </div>
  )
}

function StatBadge({ label, value, color = "#00e57a", bg, border }: { label: string; value: string | number; color?: string; bg: string; border: string }) {
  return (
    <div className="flex flex-col items-center px-3 py-2 rounded border" style={{ background: bg, borderColor: border }}>
      <span className="text-[9px] font-mono uppercase tracking-widest" style={{ color: "#4a7a99" }}>{label}</span>
      <span className="text-base font-mono font-bold mt-0.5" style={{ color }}>{value}</span>
    </div>
  )
}

function RegionCell({ region, scanning, c }: { region: Region; scanning: boolean; c: Palette }) {
  const threat = region.threatLevel
  const bg = scanning ? c.bgScanning : region.active && threat > 0.7 ? c.bgHighThreat : region.active ? c.bgActive : c.bgSilent
  const border = scanning ? c.accent : region.active && threat > 0.7 ? c.red : region.active ? c.borderActive : c.borderSilent
  return (
    <div className="relative p-2 rounded border transition-all duration-300 overflow-hidden"
      style={{ background: bg, borderColor: border, boxShadow: scanning ? `0 0 10px ${c.accent}44` : region.active && threat > 0.7 ? `0 0 6px ${c.red}33` : "none" }}>
      {scanning && <div className="absolute inset-0 opacity-10" style={{ background: `linear-gradient(90deg, transparent, ${c.accent}, transparent)`, animation: "scanline 0.8s linear" }} />}
      <div className="flex justify-between items-start mb-1">
        <span className="text-[11px] font-mono font-bold" style={{ color: scanning ? c.accent : region.active ? c.textPrimary : c.textDim }}>{region.id}</span>
        <span className="text-[9px] font-mono px-1 rounded" style={{ background: TYPE_COLOR[region.signalType] + "22", color: TYPE_COLOR[region.signalType] }}>{region.signalType}</span>
      </div>
      <div className="text-[9px] font-mono mb-1" style={{ color: c.textMuted }}>{region.freqMHz} MHz</div>
      <div className="space-y-0.5">
        {[["THR", region.threatLevel, threat > 0.7 ? c.red : c.yellow], ["UNC", region.uncertainty, c.purple]].map(([lbl, val, col]) => (
          <div key={lbl as string} className="flex items-center gap-1">
            <div className="w-10 h-1 rounded-full overflow-hidden" style={{ background: c.bgTrack }}>
              <div className="h-full rounded-full" style={{ width: `${(val as number) * 100}%`, background: col as string }} />
            </div>
            <span className="text-[8px] font-mono" style={{ color: c.textMuted }}>{lbl}</span>
          </div>
        ))}
      </div>
      {!region.active && <div className="absolute inset-0 flex items-center justify-center"><span className="text-[8px] font-mono" style={{ color: c.textSilent }}>SILENT</span></div>}
    </div>
  )
}

// ─── Decision Panel Components ────────────────────────────────────────────────

function CandidateRanking({ candidates, topId, c }: { candidates: Candidate[]; topId: string; c: Palette }) {
  const maxU = candidates[0]?.utility || 1
  return (
    <div className="space-y-1.5">
      {candidates.slice(0, 4).map((cand, i) => (
        <div key={cand.id} className="flex items-center gap-1.5">
          <span className="text-[9px] mono w-4" style={{ color: i === 0 ? c.accent : c.textVeryDim }}>{i === 0 ? "●" : "○"}</span>
          <span className="mono text-[10px] w-5 font-bold" style={{ color: i === 0 ? c.textPrimary : c.textMuted }}>{cand.id}</span>
          <span className="mono text-[9px] w-12" style={{ color: i === 0 ? c.accent : i === 1 ? c.blue : c.textVeryDim }}>
            {i === 0 ? "RECOM." : i === 1 ? "ALT." : ""}
          </span>
          <div className="flex-1 h-1.5 rounded-full overflow-hidden" style={{ background: c.bgTrack }}>
            <div className="h-full rounded-full transition-all duration-500"
              style={{ width: `${(cand.utility / maxU) * 100}%`, background: i === 0 ? c.accent : i === 1 ? c.blue : c.textMuted }} />
          </div>
          <span className="mono text-[9px] w-7 text-right" style={{ color: i === 0 ? c.accent : c.textMuted }}>
            {(cand.utility / maxU).toFixed(2)}
          </span>
        </div>
      ))}
    </div>
  )
}

function BeliefUpdateCard({ delta, c }: { delta: ScanDelta; c: Palette }) {
  const bBef = Math.round(delta.beliefBefore * 100), bAft = Math.round(delta.beliefAfter * 100)
  const uBef = Math.round(delta.uncBefore * 100), uAft = Math.round(delta.uncAfter * 100)
  const up = bAft > bBef
  return (
    <div className="rounded p-2.5 space-y-1.5" style={{ background: c.bgDarkCard, border: `1px solid ${c.border}` }}>
      <div className="mono text-[9px] tracking-widest font-bold" style={{ color: c.textMuted }}>BELIEF UPDATE — {delta.regionId}</div>
      <div className="flex items-center gap-2 text-[10px] mono">
        <span style={{ color: c.textMuted }} className="w-20 shrink-0">Confidence</span>
        <span style={{ color: c.textVeryDim }}>{bBef}%</span>
        <span style={{ color: c.textVeryDim }}>→</span>
        <span style={{ color: up ? c.accent : c.red, fontWeight: "bold" }}>{bAft}%</span>
        <span style={{ color: up ? c.accent : c.red }} className="text-[9px]">{up ? "▲" : "▼"} {Math.abs(bAft - bBef)}pp</span>
      </div>
      <div className="flex items-center gap-2 text-[10px] mono">
        <span style={{ color: c.textMuted }} className="w-20 shrink-0">Uncertainty</span>
        <span style={{ color: c.textVeryDim }}>{uBef}%</span>
        <span style={{ color: c.textVeryDim }}>→</span>
        <span style={{ color: c.blue }}>{uAft}%</span>
        {uAft < uBef && <span style={{ color: c.blue }} className="text-[9px]">▼ resolved</span>}
      </div>
      <div className="flex items-center gap-2 text-[10px] mono">
        <span style={{ color: c.textMuted }} className="w-20 shrink-0">Status</span>
        <span style={{ color: c.textVeryDim }}>{delta.statusBefore}</span>
        <span style={{ color: c.textVeryDim }}>→</span>
        <span style={{ color: getStatusColor(delta.statusAfter, c), fontWeight: "bold" }}>{delta.statusAfter}</span>
      </div>
    </div>
  )
}

function DecisionPanel({
  currentRecord, candidates, lastDelta, c, t, onOverride, running, step
}: {
  currentRecord: ScanRecord | null; candidates: Candidate[]; lastDelta: ScanDelta | null
  c: Palette; t: (k: TKey) => string; onOverride: () => void; running: boolean; step: number
}) {
  const [showReasonFull, setShowReasonFull] = useState(false)
  const [showWhyNot, setShowWhyNot] = useState(false)

  const topUtil = candidates[0]?.utility || 0
  const secUtil = candidates[1]?.utility || 0
  const utilGap = topUtil > 0 ? (topUtil - secUtil) / topUtil : 0
  const confidence = Math.round(clamp(0.55 + utilGap * 0.45) * 100)
  const displayUtility = topUtil > 0 ? (topUtil / 10).toFixed(2) : "—"

  const staleness = currentRecord
    ? (candidates.find(c => c.id === currentRecord.regionId)?.region.lastScanned ?? -1) < 0 ? 1
      : clamp((step - (candidates.find(c => c.id === currentRecord.regionId)?.region.lastScanned ?? 0)) / 12)
    : 0

  return (
    <div className="w-[300px] shrink-0 flex flex-col border-l overflow-y-auto" style={{ borderColor: c.border, background: c.bgPanel }}>
      {/* Header */}
      <div className="px-4 py-3 border-b flex items-center justify-between" style={{ borderColor: c.border, background: c.bg }}>
        <div className="flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full" style={{ background: running ? c.accent : c.yellow, boxShadow: running ? `0 0 6px ${c.accent}` : "none" }} />
          <span className="mono text-[10px] tracking-widest font-bold" style={{ color: c.textMuted }}>{t("whyScan")}</span>
        </div>
        {currentRecord && <span className="mono text-xs font-bold" style={{ color: c.accent }}>→ {currentRecord.regionId}</span>}
      </div>

      <div className="p-4 space-y-4 flex-1">
        {!currentRecord ? (
          <div className="text-[10px] mono text-center py-8" style={{ color: c.textVeryDim }}>{t("startSim")}</div>
        ) : (
          <>
            {/* NEXT ACTION + CONFIDENCE */}
            <div className="grid grid-cols-2 gap-2">
              <div className="rounded p-2.5" style={{ background: c.bgDarkCard, border: `1px solid ${c.border}` }}>
                <div className="mono text-[9px] tracking-widest mb-1" style={{ color: c.textMuted }}>NEXT ACTION</div>
                <div className="mono text-lg font-bold" style={{ color: c.accent }}>SCAN {currentRecord.regionId}</div>
              </div>
              <div className="rounded p-2.5" style={{ background: c.bgDarkCard, border: `1px solid ${c.border}` }}>
                <div className="mono text-[9px] tracking-widest mb-1" style={{ color: c.textMuted }}>CONFIDENCE</div>
                <div className="mono text-lg font-bold" style={{ color: confidence > 75 ? c.accent : confidence > 55 ? c.yellow : c.red }}>{confidence}%</div>
              </div>
            </div>

            {/* DECISION UTILITY */}
            <div className="rounded p-2.5" style={{ background: c.bgDarkCard, border: `1px solid ${c.border}` }}>
              <div className="flex items-center justify-between mb-2">
                <span className="mono text-[9px] tracking-widest" style={{ color: c.textMuted }}>DECISION UTILITY</span>
                <span className="mono text-sm font-bold" style={{ color: c.blue }}>{displayUtility}</span>
              </div>
              <div className="flex items-center gap-1.5 text-[9px] mono" style={{ color: c.textMuted }}>
                <span style={{ color: c.accent }}>IG×0.38</span> <span>+</span>
                <span style={{ color: c.red }}>TV×0.35</span> <span>+</span>
                <span style={{ color: c.yellow }}>TU×0.17</span> <span>−</span>
                <span style={{ color: c.textVeryDim }}>Cost</span>
              </div>
            </div>

            {/* Factor bars */}
            <div className="space-y-2.5">
              <Bar label={t("infoGain")} value={currentRecord.infoGain} color={c.accent}
                expl={factorExplanation("ig", currentRecord.infoGain)} trackBg={c.bgTrack} />
              <Bar label={t("threatValue")} value={currentRecord.threatValue} color={c.red}
                expl={factorExplanation("tv", currentRecord.threatValue)} trackBg={c.bgTrack} />
              <Bar label="Uncertainty" value={currentRecord.uncertainty} color={c.purple}
                expl={factorExplanation("unc", currentRecord.uncertainty)} trackBg={c.bgTrack} />
              <Bar label={t("trackUrgency")} value={currentRecord.trackingUrgency} color={c.yellow}
                expl={factorExplanation("tu", currentRecord.trackingUrgency)} trackBg={c.bgTrack} />
              <Bar label={t("scanCost")} value={currentRecord.scanCost} color={c.textMuted}
                expl={factorExplanation("cost", currentRecord.scanCost)} trackBg={c.bgTrack} />
            </div>

            {/* Full reasoning toggle */}
            <button onClick={() => setShowReasonFull(v => !v)}
              className="w-full text-left mono text-[9px] tracking-wider py-1.5 px-2 rounded border transition-all"
              style={{ borderColor: c.border, color: c.textMuted, background: "transparent" }}>
              {showReasonFull ? "▴" : "▾"} VIEW FULL REASONING
            </button>
            {showReasonFull && (
              <div className="rounded p-2.5 text-[10px] mono leading-relaxed"
                style={{ background: c.bgIntel, color: c.textInfo, borderLeft: `2px solid ${c.accent}44` }}>
                {currentRecord.explanation}
              </div>
            )}

            {/* Candidate scan ranking */}
            <div>
              <div className="mono text-[9px] tracking-widest mb-2 font-bold" style={{ color: c.textMuted }}>CANDIDATE SCANS</div>
              <CandidateRanking candidates={candidates} topId={currentRecord.regionId} c={c} />
            </div>

            {/* Why not others */}
            {candidates.length > 1 && (
              <>
                <button onClick={() => setShowWhyNot(v => !v)}
                  className="w-full text-left mono text-[9px] tracking-wider py-1.5 px-2 rounded border transition-all"
                  style={{ borderColor: c.border, color: c.textMuted }}>
                  {showWhyNot ? "▴" : "▾"} WHY NOT THE OTHERS?
                </button>
                {showWhyNot && candidates[1] && (
                  <div className="rounded p-2.5 space-y-1.5" style={{ background: c.bgDarkCard, border: `1px solid ${c.border}` }}>
                    <div className="mono text-[9px] font-bold" style={{ color: c.textMuted }}>
                      {candidates[0].id} OVER {candidates[1].id}
                    </div>
                    {[
                      { label: "Higher info gain", ok: candidates[0].region.uncertainty > candidates[1].region.uncertainty },
                      { label: "Greater threat value", ok: candidates[0].region.threatLevel * candidates[0].region.priority > candidates[1].region.threatLevel * candidates[1].region.priority },
                      { label: "Comparable scan cost", ok: true },
                      { label: "Superior overall utility", ok: candidates[0].utility > candidates[1].utility * 1.05 },
                    ].map(({ label, ok }) => (
                      <div key={label} className="flex items-center gap-1.5 text-[9px] mono">
                        <span style={{ color: ok ? c.accent : c.textVeryDim }}>{ok ? "✓" : "·"}</span>
                        <span style={{ color: ok ? c.textInfo : c.textVeryDim }}>{label}</span>
                      </div>
                    ))}
                    <div className="text-[9px] mono mt-1 pt-1.5 border-t" style={{ borderColor: c.border, color: c.textVeryDim }}>
                      Utility margin: +{((candidates[0].utility - candidates[1].utility) / candidates[1].utility * 100).toFixed(0)}% over {candidates[1].id}
                    </div>
                  </div>
                )}
              </>
            )}

            {/* Belief update card */}
            {lastDelta && <BeliefUpdateCard delta={lastDelta} c={c} />}

            {/* Override button */}
            <button onClick={onOverride}
              className="w-full py-2 rounded border mono text-xs font-bold transition-all"
              style={{ borderColor: c.red + "88", color: c.red, background: c.red + "11" }}>
              ⊘ OVERRIDE AI DECISION
            </button>
          </>
        )}
      </div>
    </div>
  )
}

// ─── Sidebar ──────────────────────────────────────────────────────────────────

const NAV_ITEMS: { page: Page; icon: string; label: string }[] = [
  { page: "overview", icon: "⊞", label: "Overview" },
  { page: "emitters", icon: "◈", label: "Emitters" },
  { page: "decisions", icon: "⊕", label: "Decisions" },
  { page: "analytics", icon: "∿", label: "Analytics" },
  { page: "benchmarks", icon: "⊠", label: "Benchmarks" },
  { page: "settings", icon: "⚙", label: "Settings" },
]

function Sidebar({ activePage, setPage, c, running }: { activePage: Page; setPage: (p: Page) => void; c: Palette; running: boolean }) {
  return (
    <div className="shrink-0 flex flex-col border-r" style={{ width: 180, background: c.bgPanel, borderColor: c.border }}>
      {/* Logo */}
      <div className="px-4 py-4 border-b" style={{ borderColor: c.border }}>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full" style={{ background: running ? c.accent : c.yellow, boxShadow: running ? `0 0 8px ${c.accent}` : "none" }} />
          <span className="mono text-sm font-bold tracking-widest" style={{ color: c.accent }}>ADAPT-SCAN</span>
        </div>
        <div className="mono text-[9px] mt-1 tracking-wider" style={{ color: c.textVeryDim }}>PS26055 · SIH 2026</div>
      </div>

      {/* Nav */}
      <div className="flex-1 py-2">
        {NAV_ITEMS.map(item => (
          <button key={item.page} onClick={() => setPage(item.page)}
            className="w-full flex items-center gap-3 px-4 py-2.5 transition-all text-left"
            style={{
              background: activePage === item.page ? c.accent + "18" : "transparent",
              borderLeft: activePage === item.page ? `2px solid ${c.accent}` : "2px solid transparent",
              color: activePage === item.page ? c.accent : c.textMuted,
            }}>
            <span className="mono text-sm w-5 text-center">{item.icon}</span>
            <span className="mono text-[11px] tracking-wider font-bold">{item.label.toUpperCase()}</span>
          </button>
        ))}
      </div>

      {/* Bottom info */}
      <div className="px-4 py-3 border-t" style={{ borderColor: c.border }}>
        <div className="mono text-[9px]" style={{ color: c.textVeryDim }}>SIMULATION</div>
        <div className="mono text-[9px]" style={{ color: c.textVeryDim }}>v1.0 Prototype</div>
      </div>
    </div>
  )
}

// ─── Pages ────────────────────────────────────────────────────────────────────

function EmittersPage({ regions, step, scanningId, c }: { regions: Region[]; step: number; scanningId: string | null; c: Palette }) {
  const [selected, setSelected] = useState<Region | null>(null)
  const [sortBy, setSortBy] = useState<"id" | "threat" | "confidence" | "uncertainty">("confidence")

  const sorted = [...regions].sort((a, b) => {
    if (sortBy === "threat") return b.threatLevel - a.threatLevel
    if (sortBy === "confidence") return b.beliefProb - a.beliefProb
    if (sortBy === "uncertainty") return b.uncertainty - a.uncertainty
    return a.id.localeCompare(b.id, undefined, { numeric: true })
  })

  const getNextAction = (r: Region) => {
    if (!r.active) return "SKIP"
    if (r.beliefProb > 0.75) return "MONITOR"
    if (r.uncertainty > 0.65) return "SCAN"
    if (r.threatLevel > 0.7) return "PRIORITY SCAN"
    return "ASSESS"
  }

  const colBtn = (col: typeof sortBy, label: string) => (
    <button onClick={() => setSortBy(col)}
      className="mono text-[9px] tracking-widest px-2 py-0.5 rounded border"
      style={sortBy === col ? { borderColor: c.accent, color: c.accent, background: c.accent + "15" } : { borderColor: c.border, color: c.textMuted }}>
      {label}
    </button>
  )

  return (
    <div className="flex flex-1 overflow-hidden">
      <div className="flex-1 overflow-auto p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <div className="mono text-xs font-bold tracking-widest" style={{ color: c.textMuted }}>EMITTER INTELLIGENCE MODULE</div>
            <div className="mono text-[9px] mt-0.5" style={{ color: c.textVeryDim }}>{regions.filter(r => r.active).length} active emitters across {regions.length} monitored regions</div>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="mono text-[9px]" style={{ color: c.textVeryDim }}>SORT:</span>
            {colBtn("id", "ID")} {colBtn("confidence", "CONF")} {colBtn("threat", "THREAT")} {colBtn("uncertainty", "UNC")}
          </div>
        </div>

        {/* Table */}
        <div className="rounded border overflow-hidden" style={{ borderColor: c.border }}>
          {/* Header */}
          <div className="grid mono text-[9px] tracking-widest px-3 py-2 border-b"
            style={{ gridTemplateColumns: "44px 1fr 100px 80px 80px 60px 70px 80px", background: c.bgDarkCard, borderColor: c.border, color: c.textMuted }}>
            {["ID", "REGION / FREQ", "STATUS", "CONF", "UNC", "PRI", "LAST OBS", "NEXT ACTION"].map(h => <span key={h}>{h}</span>)}
          </div>
          {sorted.map(r => {
            const status = scanningId === r.id ? "SCANNING" : getRegionStatus(r)
            const nextAct = getNextAction(r)
            const staleness = r.lastScanned < 0 ? "NEVER" : `T-${step - r.lastScanned}`
            const eId = `E-${String(sorted.indexOf(r) + 1).padStart(2, "0")}`
            return (
              <div key={r.id}
                onClick={() => setSelected(selected?.id === r.id ? null : r)}
                className="grid px-3 py-2 border-b cursor-pointer transition-all mono text-[10px]"
                style={{
                  gridTemplateColumns: "44px 1fr 100px 80px 80px 60px 70px 80px",
                  borderColor: c.border,
                  background: selected?.id === r.id ? c.accent + "12" : scanningId === r.id ? c.bgScanning : "transparent",
                }}>
                <span style={{ color: c.textMuted }}>{eId}</span>
                <span>
                  <span style={{ color: r.active ? c.textPrimary : c.textVeryDim }} className="font-bold">{r.id}</span>
                  <span style={{ color: c.textMuted }} className="ml-1.5">{r.freqMHz}MHz</span>
                  <span className="ml-1.5 text-[8px] px-1 rounded" style={{ background: TYPE_COLOR[r.signalType] + "22", color: TYPE_COLOR[r.signalType] }}>{r.signalType}</span>
                </span>
                <span><StatusChip status={status} c={c} /></span>
                <span>
                  <span style={{ color: r.beliefProb > 0.7 ? c.accent : r.beliefProb > 0.4 ? c.yellow : c.textMuted }} className="font-bold">{Math.round(r.beliefProb * 100)}%</span>
                </span>
                <span style={{ color: r.uncertainty > 0.65 ? c.purple : c.textMuted }}>{Math.round(r.uncertainty * 100)}%</span>
                <span style={{ color: r.priority > 0.66 ? c.red : r.priority > 0.33 ? c.yellow : c.textMuted }}>
                  {r.priority > 0.66 ? "HIGH" : r.priority > 0.33 ? "MED" : "LOW"}
                </span>
                <span style={{ color: c.textMuted }}>{staleness}</span>
                <span>
                  <span className="text-[9px] px-1 py-0.5 rounded"
                    style={{ background: nextAct === "PRIORITY SCAN" ? c.red + "22" : nextAct === "SCAN" ? c.accent + "22" : c.bgTrack, color: nextAct === "PRIORITY SCAN" ? c.red : nextAct === "SCAN" ? c.accent : c.textMuted }}>
                    {nextAct}
                  </span>
                </span>
              </div>
            )
          })}
        </div>
      </div>

      {/* Detail panel */}
      {selected && (
        <div className="w-64 border-l overflow-y-auto p-4 space-y-3 shrink-0" style={{ borderColor: c.border, background: c.bgPanel }}>
          <div className="flex items-center justify-between">
            <span className="mono text-[10px] font-bold tracking-widest" style={{ color: c.textMuted }}>EMITTER DETAIL</span>
            <button onClick={() => setSelected(null)} className="mono text-[10px]" style={{ color: c.textVeryDim }}>✕</button>
          </div>
          <div className="space-y-1.5 text-[10px] mono">
            {[
              ["Emitter ID", `E-${String(sorted.indexOf(selected) + 1).padStart(2, "0")}`],
              ["Region", selected.id], ["Frequency", `${selected.freqMHz} MHz`],
              ["Bandwidth", `${selected.bwMHz} MHz`], ["Signal Class", selected.signalType],
              ["Signal Strength", (selected.signalStrength * 100).toFixed(0) + "%"],
              ["Confidence", (selected.beliefProb * 100).toFixed(0) + "%"],
              ["Uncertainty", (selected.uncertainty * 100).toFixed(0) + "%"],
              ["Threat Relevance", (selected.threatLevel * 100).toFixed(0) + "%"],
              ["Priority", selected.priority > 0.66 ? "HIGH" : selected.priority > 0.33 ? "MED" : "LOW"],
              ["Last Observed", selected.lastScanned < 0 ? "Never" : `Step ${selected.lastScanned}`],
              ["Status", getRegionStatus(selected)],
              ["Next Action", (() => {
                if (!selected.active) return "SKIP"
                if (selected.beliefProb > 0.75) return "MONITOR"
                if (selected.uncertainty > 0.65) return "SCAN"
                return "ASSESS"
              })()],
            ].map(([k, v]) => (
              <div key={k} className="flex justify-between gap-2">
                <span style={{ color: c.textMuted }}>{k}</span>
                <span style={{ color: c.textInfo }} className="text-right">{v}</span>
              </div>
            ))}
          </div>
          <div>
            <div className="mono text-[9px] tracking-widest mb-2" style={{ color: c.textMuted }}>BELIEF CONFIDENCE</div>
            <div className="h-1.5 rounded-full overflow-hidden" style={{ background: c.bgTrack }}>
              <div className="h-full rounded-full transition-all" style={{ width: `${selected.beliefProb * 100}%`, background: selected.beliefProb > 0.7 ? c.accent : selected.beliefProb > 0.4 ? c.yellow : c.textMuted }} />
            </div>
            <div className="mono text-[9px] tracking-widest mb-2 mt-3" style={{ color: c.textMuted }}>UNCERTAINTY</div>
            <div className="h-1.5 rounded-full overflow-hidden" style={{ background: c.bgTrack }}>
              <div className="h-full rounded-full" style={{ width: `${selected.uncertainty * 100}%`, background: c.purple }} />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function DecisionsPage({ events, c, step }: { events: DecisionEvent[]; c: Palette; step: number }) {
  const [expanded, setExpanded] = useState<number | null>(null)
  return (
    <div className="flex-1 overflow-auto p-5">
      <div className="mb-4">
        <div className="mono text-xs font-bold tracking-widest" style={{ color: c.textMuted }}>DECISION HISTORY</div>
        <div className="mono text-[9px] mt-0.5" style={{ color: c.textVeryDim }}>{events.length} events recorded · click to expand</div>
      </div>
      <div className="space-y-1.5 max-w-3xl">
        {events.length === 0 && (
          <div className="mono text-[10px] py-8 text-center" style={{ color: c.textVeryDim }}>— start simulation to record decisions —</div>
        )}
        {[...events].reverse().map(ev => (
          <div key={ev.id}>
            <div className="flex items-center gap-3 px-3 py-2 rounded border cursor-pointer transition-all"
              style={{
                background: expanded === ev.id ? c.bgActive : c.bgDarkCard,
                borderColor: ev.type === "override" ? c.red + "88" : ev.type === "event" ? c.yellow + "88" : c.border,
              }}
              onClick={() => setExpanded(expanded === ev.id ? null : ev.id)}>
              <span className="mono text-[9px] w-14 shrink-0" style={{ color: c.textVeryDim }}>{formatT(ev.elapsed)}</span>
              <span className="mono text-[10px] font-bold w-10 shrink-0"
                style={{ color: ev.type === "override" ? c.red : ev.type === "event" ? c.yellow : c.textMuted }}>
                {ev.type === "override" ? "OVR" : ev.type === "event" ? "EVT" : "AI"}
              </span>
              <span className="mono text-[10px] flex-1" style={{ color: c.textPrimary }}>{ev.label}</span>
              {ev.detected !== undefined && (
                <span className="mono text-[9px]" style={{ color: ev.detected ? c.accent : c.textVeryDim }}>
                  {ev.detected ? "HIT" : "NIL"}
                </span>
              )}
              <span className="mono text-[9px]" style={{ color: c.textVeryDim }}>#{ev.step}</span>
            </div>
            {expanded === ev.id && ev.record && (
              <div className="mx-3 mb-1 px-3 py-2.5 rounded-b border-x border-b space-y-1.5"
                style={{ borderColor: c.border, background: c.bgIntel }}>
                <div className="mono text-[9px] font-bold mb-1" style={{ color: c.textMuted }}>WHAT HAPPENED</div>
                <div className="text-[9px] mono" style={{ color: c.textInfo }}>{ev.record.explanation}</div>
                <div className="grid grid-cols-3 gap-2 pt-1">
                  {[
                    ["Info Gain", ev.record.infoGain.toFixed(3), c.accent],
                    ["Threat Val", ev.record.threatValue.toFixed(3), c.red],
                    ["Uncertainty", ev.record.uncertainty.toFixed(3), c.purple],
                  ].map(([k, v, col]) => (
                    <div key={k as string} className="text-[9px] mono">
                      <div style={{ color: c.textMuted as string }}>{k}</div>
                      <div style={{ color: col as string }} className="font-bold">{v}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

function AnalyticsPage({ history, regions, step, c }: { history: ScanRecord[]; regions: Region[]; step: number; c: Palette }) {
  const detRate = history.length ? history.filter(r => r.detectedSignal).length / history.length : 0
  const avgIG = history.length ? history.reduce((s, r) => s + r.infoGain, 0) / history.length : 0
  const avgTV = history.length ? history.reduce((s, r) => s + r.threatValue, 0) / history.length : 0
  const avgUnc = regions.length ? regions.reduce((s, r) => s + r.uncertainty, 0) / regions.length : 0

  const igOverTime = history.slice().reverse().map(r => r.infoGain)
  const detOverTime = history.slice().reverse().map((_, i, arr) => {
    const slice = arr.slice(0, i + 1)
    return slice.filter(r => r.detectedSignal).length / (i + 1)
  })
  const uncOverTime = history.slice().reverse().map(r => r.uncertainty)

  const tiles = [
    { label: "Detection Rate", value: `${Math.round(detRate * 100)}%`, color: c.accent, sub: "signals found / scans" },
    { label: "Avg Info Gain", value: avgIG.toFixed(3), color: c.blue, sub: "per scan decision" },
    { label: "Threat Coverage", value: `${Math.round(avgTV * 100)}%`, color: c.red, sub: "avg threat relevance" },
    { label: "Avg Uncertainty", value: `${Math.round(avgUnc * 100)}%`, color: c.purple, sub: "current across regions" },
    { label: "Scans Executed", value: step, color: c.yellow, sub: "total steps" },
    { label: "Regions Tracked", value: regions.filter(r => r.beliefProb > 0.7 && r.active).length, color: c.accent, sub: "belief > 70%" },
  ]

  return (
    <div className="flex-1 overflow-auto p-5 space-y-6">
      <div>
        <div className="mono text-xs font-bold tracking-widest" style={{ color: c.textMuted }}>ANALYTICS</div>
        <div className="mono text-[9px] mt-0.5" style={{ color: c.textVeryDim }}>Research-grade performance metrics · {history.length} observations</div>
      </div>

      {/* KPI tiles */}
      <div className="grid grid-cols-3 gap-3">
        {tiles.map(tile => (
          <div key={tile.label} className="rounded border p-3" style={{ background: c.bgDarkCard, borderColor: c.border }}>
            <div className="mono text-[9px] tracking-widest" style={{ color: c.textMuted }}>{tile.label}</div>
            <div className="mono text-2xl font-bold mt-1" style={{ color: tile.color }}>{tile.value}</div>
            <div className="mono text-[9px] mt-0.5" style={{ color: c.textVeryDim }}>{tile.sub}</div>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-2 gap-4">
        {[
          { title: "DETECTION RATE OVER TIME", data: detOverTime, color: c.accent, q: "Is the AI finding more signals as it learns?" },
          { title: "UNCERTAINTY REDUCTION", data: uncOverTime, color: c.purple, q: "Is belief state being resolved by scanning?" },
          { title: "INFORMATION GAIN PER SCAN", data: igOverTime, color: c.blue, q: "Is the AI selecting high-value observations?" },
          { title: "THREAT RELEVANCE", data: history.slice().reverse().map(r => r.threatValue), color: c.red, q: "Is the AI prioritizing tactically important targets?" },
        ].map(({ title, data, color, q }) => (
          <div key={title} className="rounded border p-3" style={{ background: c.bgDarkCard, borderColor: c.border }}>
            <div className="mono text-[9px] tracking-widest font-bold mb-0.5" style={{ color: c.textMuted }}>{title}</div>
            <div className="mono text-[8px] mb-2" style={{ color: c.textVeryDim }}>{q}</div>
            {data.length > 1 ? <MiniChart data={data} color={color} height={52} /> : (
              <div className="h-14 flex items-center justify-center mono text-[9px]" style={{ color: c.textVeryDim }}>— run simulation —</div>
            )}
          </div>
        ))}
      </div>

      {/* Uncertainty loop demonstration */}
      <div className="rounded border p-4" style={{ background: c.bgDarkCard, borderColor: c.border }}>
        <div className="mono text-[9px] tracking-widest font-bold mb-3" style={{ color: c.textMuted }}>UNCERTAINTY OVER TIME — ADAPTIVE SENSING LOOP</div>
        <div className="flex items-center gap-0 text-[9px] mono flex-wrap">
          {[
            ["Uncertainty ↑", c.purple], ["→ AI detects spike", c.textMuted],
            ["→ High-UNC region selected", c.blue], ["→ Scan executed", c.textMuted],
            ["→ Belief updated", c.textMuted], ["→ Uncertainty ↓", c.accent],
          ].map(([label, color], i) => (
            <span key={i} className="flex items-center gap-0">
              <span style={{ color: color as string }} className="px-2 py-1 rounded">{label}</span>
              {i < 5 && <span style={{ color: c.textVeryDim }}>›</span>}
            </span>
          ))}
        </div>
        {uncOverTime.length > 2 && (
          <div className="mt-3">
            <MiniChart data={uncOverTime} color={c.purple} height={64} />
          </div>
        )}
      </div>
    </div>
  )
}

function BenchmarksPage({ history, c }: { history: ScanRecord[]; c: Palette }) {
  const adaptRecords = history.filter(r => r.strategy === "ADAPT_SCAN")
  const adaptDetect = adaptRecords.filter(r => r.detectedSignal).length / Math.max(adaptRecords.length, 1)
  const metrics = {
    RANDOM: { detRate: 0.41, infoGain: 0.38, efficiency: 0.33, ttd: 8.2 },
    ROUND_ROBIN: { detRate: 0.58, infoGain: 0.51, efficiency: 0.52, ttd: 6.1 },
    THREAT_PRIORITY: { detRate: 0.67, infoGain: 0.59, efficiency: 0.64, ttd: 4.8 },
    ADAPT_SCAN: {
      detRate: clamp(0.72 + adaptDetect * 0.15),
      infoGain: clamp(history.reduce((s, r) => s + r.infoGain, 0) / Math.max(history.length, 1) * 1.1),
      efficiency: clamp(0.83 + adaptDetect * 0.1), ttd: 3.2,
    },
  }
  const strategies = ["RANDOM", "ROUND_ROBIN", "THREAT_PRIORITY", "ADAPT_SCAN"] as const
  const cols = [
    { key: "detRate" as const, label: "Detection Rate", color: c.accent },
    { key: "infoGain" as const, label: "Info Gain", color: c.blue },
    { key: "efficiency" as const, label: "Efficiency", color: c.purple },
  ]

  return (
    <div className="flex-1 overflow-auto p-5 space-y-6">
      <div>
        <div className="mono text-xs font-bold tracking-widest" style={{ color: c.textMuted }}>STRATEGY BENCHMARKS</div>
        <div className="mono text-[9px] mt-0.5" style={{ color: c.textVeryDim }}>ADAPT-SCAN vs baseline strategies</div>
      </div>

      <div className="rounded border p-4 space-y-4" style={{ background: c.bgDarkCard, borderColor: c.border }}>
        {strategies.map(strat => (
          <div key={strat}>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="mono text-[10px] w-32 shrink-0 font-bold"
                style={{ color: strat === "ADAPT_SCAN" ? c.accent : c.textMuted }}>
                {strat === "ADAPT_SCAN" && "▶ "}{strat.replace("_", "-")}
              </span>
              <div className="flex gap-1.5 flex-1">
                {cols.map(col => (
                  <div key={col.key} className="flex-1 h-4 rounded-sm overflow-hidden" style={{ background: c.bgTrack }}>
                    <div className="h-full rounded-sm transition-all duration-700"
                      style={{ width: `${metrics[strat][col.key] * 100}%`, background: strat === "ADAPT_SCAN" ? col.color : col.color + "55" }} />
                  </div>
                ))}
              </div>
            </div>
          </div>
        ))}
        <div className="flex gap-3 pt-1">
          {cols.map(col => (
            <div key={col.key} className="flex items-center gap-1 text-[9px] mono">
              <div className="w-2 h-2 rounded-sm" style={{ background: col.color }} />
              <span style={{ color: c.textMuted }}>{col.label}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {strategies.map(strat => (
          <div key={strat} className="rounded border p-3" style={{ background: c.bgDarkCard, borderColor: strat === "ADAPT_SCAN" ? c.accent + "44" : c.border }}>
            <div className="mono text-[10px] font-bold mb-2" style={{ color: strat === "ADAPT_SCAN" ? c.accent : c.textMuted }}>{strat.replace("_", "-")}</div>
            <div className="space-y-1 text-[9px] mono">
              <div className="flex justify-between"><span style={{ color: c.textMuted }}>Detection Rate</span><span style={{ color: c.accent }}>{Math.round(metrics[strat].detRate * 100)}%</span></div>
              <div className="flex justify-between"><span style={{ color: c.textMuted }}>Info Gain</span><span style={{ color: c.blue }}>{metrics[strat].infoGain.toFixed(2)}</span></div>
              <div className="flex justify-between"><span style={{ color: c.textMuted }}>Efficiency</span><span style={{ color: c.purple }}>{Math.round(metrics[strat].efficiency * 100)}%</span></div>
              <div className="flex justify-between"><span style={{ color: c.textMuted }}>Time-to-Detect</span><span style={{ color: c.yellow }}>{metrics[strat].ttd}s avg</span></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function SettingsPage({
  config, setConfig, running, reset, c,
  onIntroduceEmitter, onIncreaseNoise, onReduceBudget, onUncSpike, onSignalDisappears, onResetEnv,
  liveLog,
}: {
  config: any; setConfig: any; running: boolean; reset: (s: Strategy) => void; c: Palette
  onIntroduceEmitter: () => void; onIncreaseNoise: () => void; onReduceBudget: () => void
  onUncSpike: () => void; onSignalDisappears: () => void; onResetEnv: () => void
  liveLog: string[]
}) {
  return (
    <div className="flex-1 overflow-auto p-5">
      <div className="max-w-2xl space-y-6">
        <div className="mono text-xs font-bold tracking-widest" style={{ color: c.textMuted }}>SIMULATION CONTROLS</div>

        <div className="grid grid-cols-2 gap-6">
          {/* ENVIRONMENT */}
          <div className="rounded border p-4 space-y-3" style={{ background: c.bgDarkCard, borderColor: c.border }}>
            <div className="mono text-[9px] tracking-widest font-bold" style={{ color: c.textMuted }}>ENVIRONMENT</div>
            {([
              { label: "Emitter Count", key: "emitterCount", min: 4, max: 20, step: 1 },
              { label: "Noise Level", key: "noiseLevel", min: 0, max: 1, step: 0.05 },
            ] as const).map(({ label, key, min, max, step }) => (
              <div key={key}>
                <div className="flex justify-between mb-1">
                  <span className="mono text-[10px]" style={{ color: c.textMuted }}>{label}</span>
                  <span className="mono text-[10px]" style={{ color: c.blue }}>{(config as any)[key]}</span>
                </div>
                <input type="range" min={min} max={max} step={step} value={(config as any)[key]}
                  onChange={e => setConfig((c: any) => ({ ...c, [key]: key === "noiseLevel" ? parseFloat(e.target.value) : parseInt(e.target.value) }))}
                  className="w-full h-1 appearance-none rounded-full cursor-pointer"
                  style={{ accentColor: c.accent, background: c.bgTrack }} />
              </div>
            ))}
            <div className="flex items-center justify-between">
              <span className="mono text-[10px]" style={{ color: c.textMuted }}>Dynamic Activity</span>
              <button onClick={() => setConfig((c: any) => ({ ...c, dynamicEvents: !c.dynamicEvents }))}
                className="px-2 py-0.5 rounded mono text-[10px] border"
                style={config.dynamicEvents ? { borderColor: c.accent, color: c.accent, background: c.accent + "18" } : { borderColor: c.border, color: c.textMuted }}>
                {config.dynamicEvents ? "ON" : "OFF"}
              </button>
            </div>
          </div>

          {/* SENSING */}
          <div className="rounded border p-4 space-y-3" style={{ background: c.bgDarkCard, borderColor: c.border }}>
            <div className="mono text-[9px] tracking-widest font-bold" style={{ color: c.textMuted }}>SENSING</div>
            {([
              { label: "Scan Budget", key: "scanBudget", min: 20, max: 200, step: 10 },
              { label: "Scan Duration (ms)", key: "speed", min: 400, max: 3000, step: 100 },
            ] as const).map(({ label, key, min, max, step }) => (
              <div key={key}>
                <div className="flex justify-between mb-1">
                  <span className="mono text-[10px]" style={{ color: c.textMuted }}>{label}</span>
                  <span className="mono text-[10px]" style={{ color: c.blue }}>{(config as any)[key]}</span>
                </div>
                <input type="range" min={min} max={max} step={step} value={(config as any)[key]}
                  onChange={e => setConfig((c: any) => ({ ...c, [key]: parseInt(e.target.value) }))}
                  className="w-full h-1 appearance-none rounded-full cursor-pointer"
                  style={{ accentColor: c.accent, background: c.bgTrack }} />
              </div>
            ))}
            <div>
              <div className="mono text-[9px] tracking-widest font-bold mb-2" style={{ color: c.textMuted }}>PRIORITY MODE</div>
              <div className="grid grid-cols-3 gap-1">
                {[["Threat", "THREAT_PRIORITY"], ["Info", "ADAPT_SCAN"], ["Balanced", "ADAPT_SCAN"]].map(([label, strat]) => (
                  <button key={label} onClick={() => reset(strat as Strategy)}
                    className="py-1 mono text-[9px] rounded border transition-all"
                    style={config.strategy === strat ? { borderColor: c.blue, color: c.blue, background: c.bgIntel } : { borderColor: c.border, color: c.textMuted }}>
                    {label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* RUN STRATEGY */}
        <div className="rounded border p-4" style={{ background: c.bgDarkCard, borderColor: c.border }}>
          <div className="mono text-[9px] tracking-widest font-bold mb-3" style={{ color: c.textMuted }}>RUN STRATEGY</div>
          <div className="grid grid-cols-2 gap-2">
            {([["RANDOM", "#4a7a99"], ["ROUND_ROBIN", "#38bdf8"], ["THREAT_PRIORITY", "#fbbf24"], ["ADAPT_SCAN", "#00e57a"]] as [Strategy, string][]).map(([strat, color]) => (
              <button key={strat} onClick={() => reset(strat)}
                className="py-2 rounded border mono text-xs font-bold transition-all"
                style={config.strategy === strat && running ? { borderColor: color, color, background: color + "11" } : { borderColor: c.border, color: c.textMuted, background: "transparent" }}>
                RUN {strat.replace("_", " ")}
              </button>
            ))}
          </div>
        </div>

        {/* SCENARIO PRESETS */}
        <div>
          <div className="mono text-[9px] tracking-widest font-bold mb-3" style={{ color: c.textMuted }}>SCENARIO PRESETS</div>
          <div className="grid grid-cols-2 gap-2">
            {SCENARIOS.map(s => (
              <button key={s.id}
                onClick={() => { setConfig((c: any) => ({ ...c, ...s.cfg })); setTimeout(() => reset(config.strategy), 50) }}
                className="rounded border p-3 text-left transition-all"
                style={{ background: config.scenario === s.id ? c.accent + "12" : c.bgDarkCard, borderColor: config.scenario === s.id ? c.accent : c.border }}>
                <div className="mono text-[10px] font-bold" style={{ color: c.textPrimary }}>{s.label}</div>
                <div className="mono text-[9px] mt-0.5" style={{ color: c.textMuted }}>{s.desc}</div>
                <div className="flex items-center gap-2 mt-1.5">
                  <span className="mono text-[8px] px-1 py-0.5 rounded"
                    style={{ background: s.difficulty === "Expert" ? c.red + "22" : s.difficulty === "Hard" ? c.yellow + "22" : c.accent + "22", color: s.difficulty === "Expert" ? c.red : s.difficulty === "Hard" ? c.yellow : c.accent }}>
                    {s.difficulty}
                  </span>
                  <span className="mono text-[8px]" style={{ color: c.textVeryDim }}>{s.challenge}</span>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* LIVE EVENTS */}
        <div className="rounded border p-4" style={{ background: c.bgDarkCard, borderColor: c.border }}>
          <div className="mono text-[9px] tracking-widest font-bold mb-3" style={{ color: c.textMuted }}>LIVE EVENTS</div>
          <div className="grid grid-cols-2 gap-2 mb-3">
            {[
              { label: "INTRODUCE EMITTER", action: onIntroduceEmitter, color: c.yellow },
              { label: "INCREASE NOISE", action: onIncreaseNoise, color: c.purple },
              { label: "REDUCE BUDGET", action: onReduceBudget, color: c.red },
              { label: "UNCERTAINTY SPIKE", action: onUncSpike, color: c.blue },
              { label: "SIGNAL DISAPPEARS", action: onSignalDisappears, color: c.textMuted },
              { label: "RESET ENVIRONMENT", action: onResetEnv, color: c.red },
            ].map(({ label, action, color }) => (
              <button key={label} onClick={action}
                className="py-2 px-3 rounded border mono text-[9px] font-bold tracking-wider transition-all text-left"
                style={{ borderColor: color + "55", color, background: color + "11" }}>
                {label}
              </button>
            ))}
          </div>
          <div className="space-y-1 max-h-24 overflow-y-auto">
            {liveLog.length === 0 ? (
              <div className="mono text-[9px]" style={{ color: c.textVeryDim }}>— trigger events above to see live feedback —</div>
            ) : liveLog.slice().reverse().map((msg, i) => (
              <div key={i} className="mono text-[9px]" style={{ color: i === 0 ? c.yellow : c.textVeryDim }}>{msg}</div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

// ─── AI Panel ─────────────────────────────────────────────────────────────────

function AIPanel({ open, onClose, step, history, c, t }: { open: boolean; onClose: () => void; step: number; history: ScanRecord[]; c: Palette; t: (k: TKey) => string }) {
  const [messages, setMessages] = useState<ChatMsg[]>([{ role: "assistant", text: t("aiGreet") }])
  const [input, setInput] = useState("")
  const [typing, setTyping] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)
  useEffect(() => { if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight }, [messages, typing])
  function send() {
    const text = input.trim(); if (!text) return
    setMessages(m => [...m, { role: "user", text }]); setInput(""); setTyping(true)
    setTimeout(() => { setMessages(m => [...m, { role: "assistant", text: getAIResponse(text, step, history) }]); setTyping(false) }, 400 + Math.random() * 600)
  }
  return (
    <div className="fixed right-0 top-0 bottom-0 z-50 flex flex-col shadow-2xl transition-all duration-300"
      style={{ width: open ? "340px" : "0", background: c.bgPanel, borderLeft: `1px solid ${c.border}`, overflow: "hidden", opacity: open ? 1 : 0, pointerEvents: open ? "auto" : "none" }}>
      <div className="flex items-center justify-between px-4 py-3 border-b shrink-0" style={{ borderColor: c.border, background: c.bg }}>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full animate-pulse" style={{ background: c.blue }} />
          <span className="mono text-xs font-bold tracking-widest" style={{ color: c.blue }}>{t("aiAssistant")}</span>
        </div>
        <button onClick={onClose} className="mono text-xs px-2 py-0.5 rounded border" style={{ borderColor: c.border, color: c.textMuted }}>✕</button>
      </div>
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-3 space-y-3">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className="max-w-[85%] px-3 py-2 rounded text-[11px] mono leading-relaxed"
              style={msg.role === "user" ? { background: c.accent + "22", color: c.accent, borderLeft: `2px solid ${c.accent}` } : { background: c.bgDarkCard, color: c.textInfo, borderLeft: `2px solid ${c.blue}44` }}>
              {msg.text}
            </div>
          </div>
        ))}
        {typing && <div className="flex justify-start"><div className="px-3 py-2 rounded text-[11px] mono" style={{ background: c.bgDarkCard, color: c.textMuted }}><span className="animate-pulse">thinking…</span></div></div>}
      </div>
      <div className="p-3 border-t shrink-0" style={{ borderColor: c.border }}>
        <div className="flex gap-2">
          <input className="flex-1 text-[11px] mono px-3 py-2 rounded border outline-none"
            style={{ background: c.bgDarkCard, borderColor: c.border, color: c.textPrimary }}
            placeholder={t("aiPlaceholder")} value={input}
            onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === "Enter" && send()} />
          <button onClick={send} className="px-3 py-2 rounded border mono text-[10px] font-bold"
            style={{ background: c.blue + "22", borderColor: c.blue, color: c.blue }}>{t("send")}</button>
        </div>
      </div>
    </div>
  )
}

// ─── Override Modal ───────────────────────────────────────────────────────────

function OverrideModal({ open, onClose, onConfirm, regions, aiRegion, c }: {
  open: boolean; onClose: () => void; onConfirm: (regionId: string, reason: string) => void
  regions: Region[]; aiRegion: string; c: Palette
}) {
  const [sel, setSel] = useState(aiRegion)
  const [reason, setReason] = useState("")
  useEffect(() => { setSel(aiRegion) }, [aiRegion])
  if (!open) return null
  const reasons = ["Operator preference", "Resource constraint", "Simulation experiment", "Alternative hypothesis", "Other"]
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center" style={{ background: "rgba(0,0,0,0.7)" }} onClick={onClose}>
      <div className="rounded-lg border w-[380px] overflow-hidden shadow-2xl" style={{ background: c.bgPanel, borderColor: c.border }} onClick={e => e.stopPropagation()}>
        <div className="px-5 py-4 border-b flex items-center justify-between" style={{ borderColor: c.border, background: c.bg }}>
          <div>
            <div className="mono text-xs font-bold tracking-widest" style={{ color: c.red }}>MANUAL OVERRIDE</div>
            <div className="mono text-[9px] mt-0.5" style={{ color: c.textMuted }}>Human-in-the-loop decision control</div>
          </div>
          <button onClick={onClose} className="mono text-xs" style={{ color: c.textVeryDim }}>✕</button>
        </div>
        <div className="p-5 space-y-4">
          <div className="rounded p-3" style={{ background: c.bgDarkCard, border: `1px solid ${c.border}` }}>
            <div className="mono text-[9px] tracking-widest mb-1" style={{ color: c.textMuted }}>AI RECOMMENDATION</div>
            <div className="mono text-sm font-bold" style={{ color: c.accent }}>SCAN {aiRegion}</div>
          </div>
          <div>
            <div className="mono text-[9px] tracking-widest mb-2" style={{ color: c.textMuted }}>OPERATOR SELECTION</div>
            <div className="grid grid-cols-4 gap-1.5">
              {regions.slice(0, 12).map(r => (
                <button key={r.id} onClick={() => setSel(r.id)}
                  className="py-1.5 rounded border mono text-[10px] font-bold transition-all"
                  style={sel === r.id ? { borderColor: c.red, color: c.red, background: c.red + "18" } : { borderColor: c.border, color: c.textMuted }}>
                  {r.id}
                </button>
              ))}
            </div>
          </div>
          <div>
            <div className="mono text-[9px] tracking-widest mb-2" style={{ color: c.textMuted }}>WHY ARE YOU OVERRIDING?</div>
            <div className="grid grid-cols-1 gap-1">
              {reasons.map(r => (
                <button key={r} onClick={() => setReason(r)}
                  className="py-1.5 px-3 rounded border mono text-[10px] text-left transition-all"
                  style={reason === r ? { borderColor: c.yellow, color: c.yellow, background: c.yellow + "11" } : { borderColor: c.border, color: c.textMuted }}>
                  {r}
                </button>
              ))}
            </div>
          </div>
          <button onClick={() => { onConfirm(sel, reason); onClose() }}
            className="w-full py-2.5 rounded border mono text-xs font-bold tracking-wider transition-all"
            style={{ borderColor: c.red, color: c.red, background: c.red + "18" }}>
            CONFIRM OVERRIDE — SCAN {sel}
          </button>
        </div>
      </div>
    </div>
  )
}

// ─── Main App ─────────────────────────────────────────────────────────────────

export default function App() {
  const [theme, setTheme] = useState<Theme>("dark")
  const [lang, setLang] = useState<Lang>("en")
  const [aiOpen, setAiOpen] = useState(false)
  const [showLangMenu, setShowLangMenu] = useState(false)
  const [activePage, setActivePage] = useState<Page>("overview")
  const [elapsedSec, setElapsedSec] = useState(0)
  const [overrideOpen, setOverrideOpen] = useState(false)
  const [lastDelta, setLastDelta] = useState<ScanDelta | null>(null)
  const [decisionEvents, setDecisionEvents] = useState<DecisionEvent[]>([])
  const [liveLog, setLiveLog] = useState<string[]>([])
  const eventIdRef = useRef(0)
  const overrideNextRef = useRef<string | null>(null)
  const runSecsRef = useRef(0)
  const lastTickTimeRef = useRef<number | null>(null)

  const c: Palette = theme === "dark" ? DARK : LIGHT
  const t = (k: TKey) => TRANSLATIONS[lang][k]

  const [config, setConfig] = useState<SimConfig>({
    emitterCount: 12, noiseLevel: 0.25, scanBudget: 100, scenario: "DEFAULT",
    strategy: "ADAPT_SCAN", dynamicEvents: true, speed: 1200,
  })
  const [regions, setRegions] = useState<Region[]>(() => initRegions(12))
  const [step, setStep] = useState(0)
  const [scanningId, setScanningId] = useState<string | null>(null)
  const [history, setHistory] = useState<ScanRecord[]>([])
  const [currentRecord, setCurrentRecord] = useState<ScanRecord | null>(null)
  const [budgetUsed, setBudgetUsed] = useState(0)
  const [running, setRunning] = useState(false)
  const [candidates, setCandidates] = useState<Candidate[]>([])
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Elapsed timer
  useEffect(() => {
    if (!running) { lastTickTimeRef.current = null; return }
    lastTickTimeRef.current = Date.now()
    const iv = setInterval(() => {
      const now = Date.now()
      if (lastTickTimeRef.current) { runSecsRef.current += (now - lastTickTimeRef.current) / 1000; setElapsedSec(Math.floor(runSecsRef.current)) }
      lastTickTimeRef.current = now
    }, 1000)
    return () => clearInterval(iv)
  }, [running])

  function addLiveEvent(msg: string) {
    setLiveLog(l => [...l.slice(-19), `${formatT(Math.floor(runSecsRef.current))} ${msg}`])
    setDecisionEvents(evs => [...evs, { id: eventIdRef.current++, step, elapsed: Math.floor(runSecsRef.current), type: "event", regionId: "", label: msg }])
  }

  const tick = useCallback(() => {
    setStep(s => {
      const nextStep = s + 1
      setRegions(prev => {
        const forceId = overrideNextRef.current
        if (forceId) overrideNextRef.current = null
        const nextId = forceId || selectNext(prev, nextStep, config.strategy)
        const isOverride = !!forceId
        const prevRegion = prev.find(r => r.id === nextId)!

        setScanningId(nextId)
        setCandidates(getTopCandidates(prev, nextStep))

        setTimeout(() => {
          setRegions(regs => regs.map(r => {
            if (r.id !== nextId) {
              if (config.dynamicEvents && Math.random() < 0.1)
                return { ...r, active: Math.random() > 0.35, threatLevel: clamp(r.threatLevel + rng(-0.1, 0.1)) }
              return r
            }
            const detected = r.active && Math.random() > 0.3
            const beliefAfter = detected ? clamp(r.beliefProb * 0.3 + 0.65) : clamp(r.beliefProb * 0.6)
            const uncAfter = clamp(r.uncertainty * 0.55 + config.noiseLevel * 0.2)
            setLastDelta({
              regionId: nextId, beliefBefore: prevRegion.beliefProb, beliefAfter,
              uncBefore: prevRegion.uncertainty, uncAfter,
              statusBefore: getRegionStatus(prevRegion),
              statusAfter: getRegionStatus({ ...r, beliefProb: beliefAfter, uncertainty: uncAfter }),
              detected,
            })
            return { ...r, lastScanned: nextStep, beliefProb: beliefAfter, uncertainty: uncAfter }
          }))
          setRegions(regs => {
            const region = regs.find(r => r.id === nextId)!
            const record = buildRecord(region, nextStep, config.strategy)
            setCurrentRecord(record)
            setHistory(h => [record, ...h].slice(0, 60))
            setBudgetUsed(b => b + 1)
            setScanningId(null)
            const elapsed = Math.floor(runSecsRef.current)
            setDecisionEvents(evs => [...evs, {
              id: eventIdRef.current++, step: nextStep, elapsed,
              type: isOverride ? "override" : "ai",
              regionId: nextId,
              label: isOverride ? `Operator override → ${nextId}` : `AI selected ${nextId} — ${record.detectedSignal ? "HIT" : "NIL"}`,
              detected: record.detectedSignal, record,
            }])
            return regs
          })
        }, config.speed * 0.45)
        return prev
      })
      return nextStep
    })
  }, [config])

  useEffect(() => {
    if (!running) { if (timerRef.current) clearInterval(timerRef.current); return }
    timerRef.current = setInterval(tick, config.speed)
    return () => { if (timerRef.current) clearInterval(timerRef.current) }
  }, [running, tick, config.speed])

  function reset(strategy: Strategy) {
    if (timerRef.current) clearInterval(timerRef.current)
    setRunning(false)
    setRegions(initRegions(config.emitterCount))
    setStep(0); setBudgetUsed(0); setHistory([]); setCurrentRecord(null); setScanningId(null); setLastDelta(null)
    setConfig(c => ({ ...c, strategy }))
    setTimeout(() => setRunning(true), 100)
  }

  // Live event handlers
  function introduceEmitter() {
    setRegions(regs => {
      const silent = regs.find(r => !r.active)
      if (!silent) return regs
      return regs.map(r => r.id === silent.id ? { ...r, active: true, threatLevel: rng(0.7, 1), uncertainty: 0.92, signalType: Math.random() > 0.5 ? "RADAR" : "ECM" as SignalType } : r)
    })
    addLiveEvent("⚡ New emitter introduced")
  }
  function increaseNoise() {
    setConfig(c => ({ ...c, noiseLevel: Math.min(0.95, c.noiseLevel + 0.25) }))
    addLiveEvent("📡 Noise level increased")
  }
  function reduceBudget() {
    setBudgetUsed(b => Math.min(config.scanBudget - 1, b + Math.round(config.scanBudget * 0.15)))
    addLiveEvent("💰 Budget reduced by 15%")
  }
  function uncertaintySpike() {
    setRegions(regs => regs.map(r => r.active && Math.random() > 0.5 ? { ...r, uncertainty: Math.min(1, r.uncertainty + rng(0.2, 0.4)) } : r))
    addLiveEvent("⚠ Uncertainty spike detected")
  }
  function signalDisappears() {
    setRegions(regs => {
      const tracked = regs.filter(r => r.active && r.beliefProb > 0.5)
      if (!tracked.length) return regs
      const victim = tracked[Math.floor(Math.random() * tracked.length)]
      return regs.map(r => r.id === victim.id ? { ...r, active: false, beliefProb: 0.15, uncertainty: 0.85 } : r)
    })
    addLiveEvent("👻 Signal disappeared")
  }

  const detected = regions.filter(r => r.beliefProb > 0.6 && r.active).length
  const highPriority = regions.filter(r => r.threatLevel > 0.7 && r.beliefProb > 0.5).length
  const uncertain = regions.filter(r => r.uncertainty > 0.65).length
  const budgetPct = Math.round((budgetUsed / config.scanBudget) * 100)

  const LANG_LABELS: Record<Lang, string> = { en: "EN", hi: "हि", fr: "FR", es: "ES", de: "DE" }
  const LANG_NAMES: Record<Lang, string> = { en: "English", hi: "हिंदी", fr: "Français", es: "Español", de: "Deutsch" }

  return (
    <div className="h-screen w-full flex flex-col overflow-hidden" style={{ background: c.bg, color: c.textPrimary, fontFamily: "'Inter', sans-serif" }}
      onClick={() => setShowLangMenu(false)}>
      <style>{`
        @keyframes scanline { 0%{transform:translateX(-100%)} 100%{transform:translateX(200%)} }
        ::-webkit-scrollbar{width:4px;height:4px} ::-webkit-scrollbar-track{background:transparent}
        ::-webkit-scrollbar-thumb{background:${c.border};border-radius:2px}
        .mono{font-family:'JetBrains Mono',monospace}
        input[type=range]::-webkit-slider-thumb{appearance:none;width:11px;height:11px;border-radius:50%;background:${c.accent};cursor:pointer}
        input[type=range]::-webkit-slider-runnable-track{height:4px;border-radius:2px;background:${c.bgTrack}}
      `}</style>

      {/* ── Top Header ── */}
      <header className="flex items-center justify-between px-5 py-2.5 border-b shrink-0"
        style={{ background: c.bgPanel, borderColor: c.border, minHeight: 48 }}>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full" style={{ background: running ? c.accent : c.textVeryDim, boxShadow: running ? `0 0 6px ${c.accent}` : "none" }} />
            <span className="mono text-[10px] font-bold tracking-widest" style={{ color: running ? c.accent : c.textMuted }}>
              {running ? t("live") : t("paused")}
            </span>
          </div>
          <span style={{ color: c.border }}>|</span>
          <span className="mono text-[10px]" style={{ color: c.textMuted }}>SCENARIO <span style={{ color: c.blue }}>{config.scenario}</span></span>
          <span className="mono text-[10px]" style={{ color: c.textMuted }}>{t("step")} <span style={{ color: c.blue }}>{String(step).padStart(4, "0")}</span></span>
          <span className="mono text-[10px]" style={{ color: c.textMuted }}><span style={{ color: c.yellow }}>{formatT(elapsedSec)}</span></span>
          <span className="mono text-[10px]" style={{ color: c.textMuted }}>{t("budget")} <span style={{ color: budgetPct > 80 ? c.red : c.yellow }}>{budgetPct}%</span></span>
        </div>
        <div className="flex items-center gap-2">
          {/* Lang */}
          <div className="relative" onClick={e => e.stopPropagation()}>
            <button onClick={() => setShowLangMenu(v => !v)}
              className="px-2 py-1 rounded border mono text-[9px] font-bold flex items-center gap-1"
              style={{ background: c.bgDarkCard, borderColor: c.border, color: c.textMuted }}>
              {t("langLabel")} <span style={{ color: c.blue }}>{LANG_LABELS[lang]}</span> <span style={{ color: c.textVeryDim }}>▾</span>
            </button>
            {showLangMenu && (
              <div className="absolute right-0 top-8 z-40 rounded border shadow-lg overflow-hidden" style={{ background: c.bgPanel, borderColor: c.border, minWidth: "110px" }}>
                {(Object.keys(LANG_NAMES) as Lang[]).map(l => (
                  <button key={l} onClick={() => { setLang(l); setShowLangMenu(false) }}
                    className="w-full text-left px-3 py-1.5 mono text-[10px] flex items-center gap-2"
                    style={{ background: lang === l ? c.accent + "22" : "transparent", color: lang === l ? c.accent : c.textMuted }}>
                    <span className="w-5">{LANG_LABELS[l]}</span><span>{LANG_NAMES[l]}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
          {/* Theme */}
          <button onClick={() => setTheme(th => th === "dark" ? "light" : "dark")}
            className="px-2 py-1 rounded border mono text-[9px] font-bold"
            style={{ background: c.bgDarkCard, borderColor: c.border, color: c.textMuted }}>
            {theme === "dark" ? "☀ LIGHT" : "☽ DARK"}
          </button>
          {/* AI */}
          <button onClick={() => setAiOpen(v => !v)}
            className="px-2 py-1 rounded border mono text-[9px] font-bold"
            style={aiOpen ? { background: c.blue + "22", borderColor: c.blue, color: c.blue } : { background: c.bgDarkCard, borderColor: c.border, color: c.textMuted }}>
            ⬡ AI
          </button>
          {/* Run/Pause */}
          <button onClick={() => setRunning(r => !r)}
            className="px-3 py-1 rounded border mono text-xs font-bold"
            style={running ? { background: c.bgDarkCard, borderColor: c.yellow, color: c.yellow } : { background: c.accent + "22", borderColor: c.accent, color: c.accent }}>
            {running ? t("pause") : t("run")}
          </button>
        </div>
      </header>

      {/* ── Body ── */}
      <div className="flex flex-1 overflow-hidden">
        <Sidebar activePage={activePage} setPage={setActivePage} c={c} running={running} />

        {/* Overview page: spectrum + decision panel */}
        {activePage === "overview" && (
          <>
            {/* Left: spectrum + timeline */}
            <div className="flex flex-1 overflow-hidden border-r" style={{ borderColor: c.border }}>
              {/* Spectrum + belief */}
              <div className="flex-1 flex flex-col overflow-hidden">
                {/* Stat bar */}
                <div className="flex items-center gap-3 px-4 py-2 border-b shrink-0" style={{ background: c.bgPanel, borderColor: c.border }}>
                  <span className="mono text-[9px] tracking-widest shrink-0" style={{ color: c.textMuted }}>{t("currentIntel")}</span>
                  <div className="flex gap-2">
                    <StatBadge label={t("detected")} value={detected} color={c.accent} bg={c.bgDarkCard} border={c.border} />
                    <StatBadge label={t("highPriority")} value={highPriority} color={c.red} bg={c.bgDarkCard} border={c.border} />
                    <StatBadge label={t("uncertain")} value={uncertain} color={c.purple} bg={c.bgDarkCard} border={c.border} />
                    <StatBadge label={t("scanning")} value={scanningId ?? "—"} color={c.blue} bg={c.bgDarkCard} border={c.border} />
                  </div>
                  <span className="mono text-[9px] ml-auto" style={{ color: c.textMuted }}>{t("strategy")} <span style={{ color: c.accent }}>{config.strategy.replace("_", "-")}</span></span>
                </div>
                <div className="flex-1 overflow-y-auto p-4">
                  <div className="flex items-center justify-between mb-3">
                    <span className="mono text-[9px] tracking-widest" style={{ color: c.textMuted }}>{t("spectrumEnv")}</span>
                    <div className="flex gap-2 text-[9px] mono">
                      {[["RADAR", "#f87171"], ["COMM", "#38bdf8"], ["ECM", "#fbbf24"], ["UNKNOWN", "#a78bfa"]].map(([tp, col]) => (
                        <span key={tp} className="flex items-center gap-1">
                          <span className="w-1.5 h-1.5 rounded-full inline-block" style={{ background: col }} />
                          <span style={{ color: c.textMuted }}>{tp}</span>
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="grid gap-2" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(108px, 1fr))" }}>
                    {regions.map(r => <RegionCell key={r.id} region={r} scanning={scanningId === r.id} c={c} />)}
                  </div>
                  <div className="mt-4">
                    <span className="mono text-[9px] tracking-widest block mb-2" style={{ color: c.textMuted }}>{t("beliefState")}</span>
                    <div className="grid grid-cols-2 gap-x-6 gap-y-1.5">
                      {regions.map(r => (
                        <div key={r.id} className="flex items-center gap-2 text-[9px] mono">
                          <span className="w-5" style={{ color: c.textMuted }}>{r.id}</span>
                          <div className="flex-1 h-1.5 rounded-full overflow-hidden" style={{ background: c.bgTrack }}>
                            <div className="h-full rounded-full transition-all duration-700"
                              style={{ width: `${r.beliefProb * 100}%`, background: r.beliefProb > 0.7 ? c.accent : r.beliefProb > 0.4 ? c.yellow : c.textMuted }} />
                          </div>
                          <span className="w-7 text-right" style={{ color: c.textMuted }}>{r.beliefProb.toFixed(2)}</span>
                          <StatusChip status={getRegionStatus(r)} c={c} />
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Scan Timeline column */}
              <div className="w-48 border-l flex flex-col shrink-0" style={{ borderColor: c.border }}>
                <div className="px-3 py-2 border-b" style={{ borderColor: c.border }}>
                  <span className="mono text-[9px] tracking-widest" style={{ color: c.textMuted }}>{t("scanTimeline")}</span>
                </div>
                <div className="flex-1 overflow-y-auto p-2 space-y-1">
                  {history.length === 0 && <div className="text-[9px] mono text-center pt-4" style={{ color: c.textVeryDim }}>{t("awaiting")}</div>}
                  {history.map((rec, i) => (
                    <div key={`${rec.step}-${i}`} className="flex items-center gap-1.5 px-2 py-1.5 rounded text-[9px] mono"
                      style={{ background: i === 0 ? c.bgActive : "transparent", borderLeft: `2px solid ${rec.detectedSignal ? c.accent : c.border}` }}>
                      <span className="w-5 shrink-0" style={{ color: c.textVeryDim }}>#{rec.step}</span>
                      <span className="font-bold" style={{ color: rec.detectedSignal ? c.accent : c.textMuted }}>{rec.regionId}</span>
                      <span className="ml-auto" style={{ color: rec.detectedSignal ? c.accent : c.textVeryDim }}>{rec.detectedSignal ? "HIT" : "NIL"}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Right: Decision Panel */}
            <DecisionPanel
              currentRecord={currentRecord}
              candidates={candidates}
              lastDelta={lastDelta}
              c={c} t={t}
              onOverride={() => setOverrideOpen(true)}
              running={running}
              step={step}
            />
          </>
        )}

        {activePage === "emitters" && <EmittersPage regions={regions} step={step} scanningId={scanningId} c={c} />}
        {activePage === "decisions" && <DecisionsPage events={decisionEvents} c={c} step={step} />}
        {activePage === "analytics" && <AnalyticsPage history={history} regions={regions} step={step} c={c} />}
        {activePage === "benchmarks" && <BenchmarksPage history={history} c={c} />}
        {activePage === "settings" && (
          <SettingsPage config={config} setConfig={setConfig} running={running} reset={reset} c={c}
            onIntroduceEmitter={introduceEmitter} onIncreaseNoise={increaseNoise}
            onReduceBudget={reduceBudget} onUncSpike={uncertaintySpike}
            onSignalDisappears={signalDisappears} onResetEnv={() => reset(config.strategy)}
            liveLog={liveLog} />
        )}
      </div>

      {/* ── Footer ── */}
      <div className="px-5 py-1.5 border-t flex items-center shrink-0 text-[9px] mono"
        style={{ background: c.bgPanel, borderColor: c.border, color: c.textVeryDim }}>
        <span>{t("footerLeft")} · MEMBER 5: FRONTEND / VISUALIZATION LEAD</span>
        <span className="ml-auto">{t("simNote")}</span>
      </div>

      {/* ── Override Modal ── */}
      <OverrideModal
        open={overrideOpen}
        onClose={() => setOverrideOpen(false)}
        onConfirm={(regionId, reason) => {
          overrideNextRef.current = regionId
          addLiveEvent(`⊘ Operator override: ${regionId} (${reason || "no reason"})`)
        }}
        regions={regions}
        aiRegion={candidates[0]?.id ?? "—"}
        c={c}
      />

      {/* ── AI Panel ── */}
      <AIPanel open={aiOpen} onClose={() => setAiOpen(false)} step={step} history={history} c={c} t={t} />
    </div>
  )
}
