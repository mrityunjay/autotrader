import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { CheckCircle, XCircle, AlertCircle, Clock } from 'lucide-react'

const STATUS_CONFIG = {
  OPEN:              { label: 'Open',         color: 'text-blue-400',   icon: Clock },
  CLOSED_TARGET:     { label: 'Target Hit',   color: 'text-green-400',  icon: CheckCircle },
  CLOSED_STOPLOSS:   { label: 'Stop Loss',    color: 'text-red-400',    icon: XCircle },
  CLOSED_TRAILING:   { label: 'Trailing SL',  color: 'text-yellow-400', icon: AlertCircle },
  CLOSED_SQUAREOFF:  { label: 'Square Off',   color: 'text-gray-400',   icon: Clock },
  CLOSED_MANUAL:     { label: 'Manual',       color: 'text-gray-400',   icon: Clock },
}

export default function TradeLog() {
  const [trades, setTrades] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getTrades(100).then(setTrades).finally(() => setLoading(false))
    const interval = setInterval(() => api.getTrades(100).then(setTrades), 10000)
    return () => clearInterval(interval)
  }, [])

  const closed = trades.filter(t => t.status !== 'OPEN')
  const totalPnl = closed.reduce((s, t) => s + (t.pnl || 0), 0)
  const wins = closed.filter(t => (t.pnl || 0) > 0).length
  const winRate = closed.length ? ((wins / closed.length) * 100).toFixed(0) : 0

  return (
    <div className="space-y-4">
      {/* Summary */}
      {closed.length > 0 && (
        <div className="grid grid-cols-3 gap-4">
          <StatPill label="Total Trades" value={closed.length} />
          <StatPill label="Win Rate" value={`${winRate}%`} />
          <StatPill
            label="Total P&L"
            value={`${totalPnl >= 0 ? '+' : ''}₹${totalPnl.toFixed(0)}`}
            positive={totalPnl > 0}
            negative={totalPnl < 0}
          />
        </div>
      )}

      {/* Table */}
      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-gray-500 text-xs border-b border-gray-800">
              <th className="text-left pb-2 pr-4">Symbol</th>
              <th className="text-right pb-2 pr-4">Entry</th>
              <th className="text-right pb-2 pr-4">Exit</th>
              <th className="text-right pb-2 pr-4">Qty</th>
              <th className="text-right pb-2 pr-4">P&L</th>
              <th className="text-left pb-2 pr-4">Status</th>
              <th className="text-right pb-2">Score</th>
              <th className="text-right pb-2">Time</th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr><td colSpan={8} className="py-8 text-center text-gray-500">Loading...</td></tr>
            )}
            {!loading && trades.length === 0 && (
              <tr><td colSpan={8} className="py-8 text-center text-gray-500">No trades yet</td></tr>
            )}
            {trades.map(trade => {
              const cfg = STATUS_CONFIG[trade.status] || STATUS_CONFIG.OPEN
              const Icon = cfg.icon
              return (
                <tr key={trade.id} className="border-b border-gray-800/40 hover:bg-gray-800/30">
                  <td className="py-2 pr-4 font-semibold">{trade.symbol.replace('-EQ', '')}</td>
                  <td className="py-2 pr-4 text-right text-gray-400">₹{trade.entry_price}</td>
                  <td className="py-2 pr-4 text-right text-gray-400">
                    {trade.exit_price ? `₹${trade.exit_price}` : '—'}
                  </td>
                  <td className="py-2 pr-4 text-right">{trade.quantity}</td>
                  <td className={`py-2 pr-4 text-right font-semibold ${
                    (trade.pnl || 0) > 0 ? 'text-green-400' :
                    (trade.pnl || 0) < 0 ? 'text-red-400' : 'text-gray-400'
                  }`}>
                    {trade.pnl !== null ? `${trade.pnl >= 0 ? '+' : ''}₹${trade.pnl?.toFixed(0)}` : '—'}
                  </td>
                  <td className={`py-2 pr-4 ${cfg.color}`}>
                    <div className="flex items-center gap-1">
                      <Icon size={12} /> {cfg.label}
                    </div>
                  </td>
                  <td className="py-2 text-right text-gray-500">
                    {trade.score ? trade.score.toFixed(0) : '—'}
                  </td>
                  <td className="py-2 text-right text-gray-500 text-xs">
                    {new Date(trade.created_at).toLocaleTimeString('en-IN', {
                      hour: '2-digit', minute: '2-digit'
                    })}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function StatPill({ label, value, positive, negative }) {
  const cls = positive ? 'text-green-400' : negative ? 'text-red-400' : 'text-white'
  return (
    <div className="card text-center">
      <div className="text-xs text-gray-500 mb-1">{label}</div>
      <div className={`font-bold text-lg ${cls}`}>{value}</div>
    </div>
  )
}
