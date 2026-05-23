import { useEffect, useState } from 'react'
import { api } from '../api/client'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts'
import { TrendingUp, TrendingDown, DollarSign, Target, Shield, Zap } from 'lucide-react'

export default function Dashboard({ status, positions }) {
  const [pnlHistory, setPnlHistory] = useState([])

  useEffect(() => {
    api.getDailyPnL(14).then(data => {
      setPnlHistory([...data].reverse())
    }).catch(() => {})
  }, [])

  return (
    <div className="space-y-4">
      {/* Stat cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          icon={<DollarSign size={16} />}
          label="Capital"
          value={status ? `₹${status.total_capital.toLocaleString()}` : '—'}
          sub={status ? `₹${status.available_capital.toLocaleString()} free` : ''}
        />
        <StatCard
          icon={<Zap size={16} />}
          label="Today's P&L"
          value={status ? fmtPnl(status.total_pnl_today) : '—'}
          positive={status?.total_pnl_today > 0}
          negative={status?.total_pnl_today < 0}
        />
        <StatCard
          icon={<Target size={16} />}
          label="Realized"
          value={status ? fmtPnl(status.realized_pnl_today) : '—'}
          positive={status?.realized_pnl_today > 0}
          negative={status?.realized_pnl_today < 0}
        />
        <StatCard
          icon={<Shield size={16} />}
          label="Open Positions"
          value={status ? status.open_positions : '—'}
          sub="active trades"
        />
      </div>

      {/* Live positions mini table */}
      {positions && positions.length > 0 && (
        <div className="card">
          <h2 className="text-sm font-semibold text-gray-400 mb-3">Live Positions</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-500 text-xs border-b border-gray-800">
                  <th className="text-left pb-2">Symbol</th>
                  <th className="text-right pb-2">Entry</th>
                  <th className="text-right pb-2">LTP</th>
                  <th className="text-right pb-2">SL</th>
                  <th className="text-right pb-2">Target</th>
                  <th className="text-right pb-2">P&L</th>
                  <th className="text-right pb-2">%</th>
                </tr>
              </thead>
              <tbody>
                {positions.map(pos => (
                  <tr key={pos.trade_id} className="border-b border-gray-800/50">
                    <td className="py-2 font-semibold">{pos.symbol.replace('-EQ', '')}</td>
                    <td className="py-2 text-right text-gray-400">₹{pos.entry_price}</td>
                    <td className="py-2 text-right">{pos.ltp ? `₹${pos.ltp}` : '—'}</td>
                    <td className="py-2 text-right text-red-400">₹{pos.current_sl}</td>
                    <td className="py-2 text-right text-green-400">₹{pos.target}</td>
                    <td className={`py-2 text-right font-semibold ${pnlClass(pos.unrealized_pnl)}`}>
                      {fmtPnl(pos.unrealized_pnl)}
                    </td>
                    <td className={`py-2 text-right ${pnlClass(pos.unrealized_pnl_pct)}`}>
                      {pos.unrealized_pnl_pct?.toFixed(2)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* PnL chart */}
      {pnlHistory.length > 0 && (
        <div className="card">
          <h2 className="text-sm font-semibold text-gray-400 mb-3">Daily P&L (last 14 days)</h2>
          <ResponsiveContainer width="100%" height={180}>
            <AreaChart data={pnlHistory}>
              <defs>
                <linearGradient id="pnlGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis dataKey="date" tick={{ fill: '#6b7280', fontSize: 11 }} />
              <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} />
              <Tooltip
                contentStyle={{ background: '#111827', border: '1px solid #374151' }}
                formatter={(v) => [`₹${v.toFixed(0)}`, 'Realized P&L']}
              />
              <Area
                type="monotone"
                dataKey="realized_pnl"
                stroke="#22c55e"
                fill="url(#pnlGrad)"
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}

function StatCard({ icon, label, value, sub, positive, negative }) {
  const valClass = positive ? 'text-green-400' : negative ? 'text-red-400' : 'text-white'
  return (
    <div className="card flex flex-col gap-1">
      <div className="flex items-center gap-1.5 text-gray-500 text-xs">
        {icon} {label}
      </div>
      <div className={`text-xl font-bold ${valClass}`}>{value}</div>
      {sub && <div className="text-xs text-gray-500">{sub}</div>}
    </div>
  )
}

function fmtPnl(v) {
  if (v === null || v === undefined) return '—'
  return `${v >= 0 ? '+' : ''}₹${Math.abs(v).toFixed(0)}`
}

function pnlClass(v) {
  return v > 0 ? 'text-green-400' : v < 0 ? 'text-red-400' : 'text-gray-400'
}
