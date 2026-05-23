import { useState } from 'react'
import { api } from '../api/client'
import { X, TrendingUp, TrendingDown } from 'lucide-react'

export default function Positions({ livePositions }) {
  const [closing, setClosing] = useState(null)

  const handleClose = async (tradeId, symbol) => {
    if (!window.confirm(`Close ${symbol} position?`)) return
    setClosing(tradeId)
    try {
      await api.closePosition(tradeId)
    } catch (e) {
      alert('Failed to close: ' + e.message)
    } finally {
      setClosing(null)
    }
  }

  if (!livePositions?.length) {
    return (
      <div className="card flex items-center justify-center h-40 text-gray-500">
        No open positions
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <h2 className="text-sm font-semibold text-gray-400">Open Positions ({livePositions.length})</h2>
      {livePositions.map(pos => (
        <PositionCard
          key={pos.trade_id}
          pos={pos}
          onClose={() => handleClose(pos.trade_id, pos.symbol)}
          isClosing={closing === pos.trade_id}
        />
      ))}
    </div>
  )
}

function PositionCard({ pos, onClose, isClosing }) {
  const pnl = pos.unrealized_pnl || 0
  const pnlPct = pos.unrealized_pnl_pct || 0
  const ltp = pos.ltp

  // Progress bar: 0% = entry, 100% = target
  const range = pos.target - pos.entry_price
  const progress = ltp ? Math.max(0, Math.min(100, ((ltp - pos.entry_price) / range) * 100)) : 0

  // SL progress
  const slPct = ((pos.current_sl - pos.entry_price) / pos.entry_price * 100).toFixed(1)

  return (
    <div className="card relative">
      <div className="flex items-start justify-between mb-3">
        <div>
          <span className="font-bold text-base">{pos.symbol.replace('-EQ', '')}</span>
          <span className="text-gray-500 text-xs ml-2">
            {pos.quantity} shares × ₹{pos.entry_price}
          </span>
        </div>
        <div className="flex items-center gap-3">
          <div className={`text-right ${pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            <div className="font-bold">{pnl >= 0 ? '+' : ''}₹{Math.abs(pnl).toFixed(0)}</div>
            <div className="text-xs">{pnlPct.toFixed(2)}%</div>
          </div>
          <button
            onClick={onClose}
            disabled={isClosing}
            className="p-1.5 rounded-lg bg-gray-800 hover:bg-red-900 text-gray-400 hover:text-red-400 transition-colors"
            title="Close position"
          >
            <X size={14} />
          </button>
        </div>
      </div>

      {/* Price levels */}
      <div className="grid grid-cols-4 gap-2 text-xs mb-3">
        <Level label="Entry" value={`₹${pos.entry_price}`} />
        <Level label="LTP" value={ltp ? `₹${ltp}` : '—'} highlight />
        <Level label="Stop Loss" value={`₹${pos.current_sl}`} color="text-red-400"
          sub={`${slPct}%`} />
        <Level label="Target" value={`₹${pos.target}`} color="text-green-400" />
      </div>

      {/* Progress bar: SL ← entry → target */}
      <div className="relative h-2 bg-gray-800 rounded-full overflow-hidden">
        {/* SL zone (red, left) */}
        <div
          className="absolute left-0 top-0 h-full bg-red-900/60"
          style={{ width: '20%' }}
        />
        {/* Progress (green) */}
        <div
          className="absolute top-0 h-full bg-green-500 transition-all duration-500"
          style={{ left: '20%', width: `${progress * 0.6}%` }}
        />
        {/* Target zone */}
        <div
          className="absolute right-0 top-0 h-full bg-green-900/40"
          style={{ width: '20%' }}
        />
      </div>
      <div className="flex justify-between text-xs text-gray-600 mt-0.5">
        <span>SL ₹{pos.current_sl}</span>
        {pos.in_profit_zone && (
          <span className="text-green-500 text-xs">🔒 SL locked at entry</span>
        )}
        <span>Target ₹{pos.target}</span>
      </div>
    </div>
  )
}

function Level({ label, value, sub, color = 'text-white', highlight }) {
  return (
    <div className={`text-center p-1.5 rounded ${highlight ? 'bg-gray-800' : ''}`}>
      <div className="text-gray-500 text-xs">{label}</div>
      <div className={`font-semibold ${color}`}>{value}</div>
      {sub && <div className="text-gray-500 text-xs">{sub}</div>}
    </div>
  )
}
