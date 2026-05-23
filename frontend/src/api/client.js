import * as mock from './mockData.js'

const BASE = import.meta.env.VITE_API_URL
  ? import.meta.env.VITE_API_URL.replace(/\/$/, '') + '/api'
  : '/api'

// Try the backend; on any network failure fall through to demo data.
async function get(path) {
  try {
    const res = await fetch(`${BASE}${path}`)
    if (!res.ok) throw new Error(res.status)
    return res.json()
  } catch {
    return null   // caller decides what to do with null
  }
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

// Probe once at startup; result cached for the session.
let _demoMode = null
async function isDemoMode() {
  if (_demoMode !== null) return _demoMode
  const result = await get('/status')
  _demoMode = result === null
  return _demoMode
}

export async function getConnectionMode() {
  return (await isDemoMode()) ? 'demo' : 'live'
}

export const api = {
  getStatus:      async () => (await get('/status'))         ?? mock.mockStatus,
  getPositions:   async () => (await get('/positions'))      ?? [],
  getTrades:      async (limit = 50) => (await get(`/trades?limit=${limit}`)) ?? mock.mockTrades,
  getTodayTrades: async () => (await get('/trades/today'))   ?? mock.mockTrades.filter(t => t.created_at?.startsWith(new Date().toISOString().slice(0,10))),
  getTodayScores: async () => (await get('/scores/today'))   ?? mock.mockScores,
  getDailyPnL:    async (days = 30) => (await get(`/pnl/daily?days=${days}`)) ?? mock.mockDailyPnl,
  refreshScores:  () => post('/scores/refresh'),
  closePosition:  (id) => del(`/positions/${id}`),
  startEngine:    () => post('/engine/start'),
  stopEngine:     () => post('/engine/stop'),
  squareOff:      () => post('/engine/squareoff'),
  getSettings:    async () => (await get('/settings')) ?? {
    trading_capital: 50000, max_positions: 5, stop_loss_pct: 0.02,
    target_pct: 0.045, trailing_sl_pct: 0.02, position_size_pct: 0.20,
    market_open: '09:15', market_close: '15:30', square_off_time: '15:10',
  },
  updateSettings: (body) => patch('/settings', body),
}

export function createWebSocket(onMessage) {
  // In demo mode send a mock update every 3 seconds instead of a real WS.
  isDemoMode().then(demo => {
    if (demo) {
      let tick = 0
      const interval = setInterval(() => {
        tick++
        // Slightly move LTP prices each tick to simulate live market
        const positions = mock.mockPositions.map(p => ({
          ...p,
          ltp: +(p.ltp + (Math.random() - 0.48) * p.ltp * 0.0015).toFixed(2),
        }))
        positions.forEach(p => {
          p.unrealized_pnl = +((p.ltp - p.entry_price) * p.quantity).toFixed(2)
          p.unrealized_pnl_pct = +((p.ltp - p.entry_price) / p.entry_price * 100).toFixed(2)
        })
        const unrealized = positions.reduce((s, p) => s + p.unrealized_pnl, 0)
        onMessage({
          type: 'update',
          status: { ...mock.mockStatus, unrealized_pnl: +unrealized.toFixed(2), total_pnl_today: +(mock.mockStatus.realized_pnl_today + unrealized).toFixed(2) },
          positions,
          timestamp: new Date().toISOString(),
        })
      }, 3000)
      return { close: () => clearInterval(interval) }
    }
  })

  // Also attempt real WS (no-op in demo since backend unreachable)
  try {
    const apiBase = import.meta.env.VITE_API_URL || ''
    const wsBase = apiBase
      ? apiBase.replace(/^https?/, p => p === 'https' ? 'wss' : 'ws')
      : `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}`
    const ws = new WebSocket(`${wsBase}/api/ws`)
    ws.onmessage = e => onMessage(JSON.parse(e.data))
    return ws
  } catch {
    return { close: () => {} }
  }
}
