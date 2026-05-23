// When running on GitHub Pages, point to your deployed backend URL.
// When running locally (npm run dev), the Vite proxy handles /api → localhost:8000.
const BASE = import.meta.env.VITE_API_URL
  ? import.meta.env.VITE_API_URL.replace(/\/$/, '') + '/api'
  : '/api'

async function get(path) {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) throw new Error(`GET ${path} → ${res.status}`)
  return res.json()
}

async function post(path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) throw new Error(`POST ${path} → ${res.status}`)
  return res.json()
}

async function patch(path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`PATCH ${path} → ${res.status}`)
  return res.json()
}

async function del(path) {
  const res = await fetch(`${BASE}${path}`, { method: 'DELETE' })
  if (!res.ok) throw new Error(`DELETE ${path} → ${res.status}`)
  return res.json()
}

export const api = {
  getStatus: () => get('/status'),
  getPositions: () => get('/positions'),
  getTrades: (limit = 50) => get(`/trades?limit=${limit}`),
  getTodayTrades: () => get('/trades/today'),
  getTodayScores: () => get('/scores/today'),
  refreshScores: () => post('/scores/refresh'),
  closePosition: (id) => del(`/positions/${id}`),
  startEngine: () => post('/engine/start'),
  stopEngine: () => post('/engine/stop'),
  squareOff: () => post('/engine/squareoff'),
  getSettings: () => get('/settings'),
  updateSettings: (body) => patch('/settings', body),
  getDailyPnL: (days = 30) => get(`/pnl/daily?days=${days}`),
}

export function createWebSocket(onMessage) {
  const apiBase = import.meta.env.VITE_API_URL || ''
  const wsBase = apiBase
    ? apiBase.replace(/^https?/, (p) => (p === 'https' ? 'wss' : 'ws'))
    : `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}`
  const ws = new WebSocket(`${wsBase}/api/ws`)
  ws.onmessage = (e) => onMessage(JSON.parse(e.data))
  ws.onerror = (e) => console.warn('WS error', e)
  return ws
}
