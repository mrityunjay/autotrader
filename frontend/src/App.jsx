import { useState, useEffect, useCallback } from 'react'
import { createWebSocket } from './api/client'
import Dashboard from './components/Dashboard'
import Positions from './components/Positions'
import TradeLog from './components/TradeLog'
import StockScorer from './components/StockScorer'
import Settings from './components/Settings'
import { Activity, LayoutDashboard, List, BarChart2, Settings2 } from 'lucide-react'

const TABS = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'positions', label: 'Positions', icon: Activity },
  { id: 'trades',    label: 'Trade Log', icon: List },
  { id: 'scorer',    label: 'Scorer',    icon: BarChart2 },
  { id: 'settings',  label: 'Settings',  icon: Settings2 },
]

export default function App() {
  const [tab, setTab] = useState('dashboard')
  const [liveData, setLiveData] = useState(null)

  useEffect(() => {
    const ws = createWebSocket((data) => {
      if (data.type === 'update') setLiveData(data)
    })
    return () => ws.close()
  }, [])

  const status  = liveData?.status    || null
  const livePos = liveData?.positions || []

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-3 bg-gray-900 border-b border-gray-800">
        <div className="flex items-center gap-2">
          <Activity size={20} className="text-green-400" />
          <span className="text-lg font-bold tracking-wide">AutoTrader</span>
          <span className="text-xs text-gray-500 ml-2">NSE Intraday</span>
        </div>
        <div className="flex items-center gap-4 text-sm">
          {status && (
            <>
              <span className={status.engine_running ? 'text-green-400' : 'text-gray-500'}>
                {status.engine_running ? '● LIVE' : '○ OFFLINE'}
              </span>
              <span className={status.is_market_open ? 'text-green-400' : 'text-gray-500'}>
                {status.is_market_open ? 'Market Open' : 'Market Closed'}
              </span>
              <PnLBadge value={status.total_pnl_today} />
            </>
          )}
        </div>
      </header>

      {/* Nav */}
      <nav className="flex gap-1 px-6 py-2 bg-gray-900 border-b border-gray-800">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-colors
              ${tab === id ? 'bg-gray-700 text-white' : 'text-gray-400 hover:text-white hover:bg-gray-800'}`}
          >
            <Icon size={14} /> {label}
          </button>
        ))}
      </nav>

      {/* Content */}
      <main className="flex-1 p-6">
        {tab === 'dashboard' && <Dashboard status={status} positions={livePos} />}
        {tab === 'positions' && <Positions livePositions={livePos} />}
        {tab === 'trades'    && <TradeLog />}
        {tab === 'scorer'    && <StockScorer />}
        {tab === 'settings'  && <Settings />}
      </main>
    </div>
  )
}

function PnLBadge({ value }) {
  if (value === null || value === undefined) return null
  const cls = value > 0 ? 'text-green-400' : value < 0 ? 'text-red-400' : 'text-gray-400'
  return (
    <span className={`font-semibold ${cls}`}>
      {value >= 0 ? '+' : ''}₹{value.toFixed(0)}
    </span>
  )
}
