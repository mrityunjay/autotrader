import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { RefreshCw } from 'lucide-react'

export default function StockScorer() {
  const [scores, setScores] = useState([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  const load = () => {
    api.getTodayScores().then(setScores).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const handleRefresh = async () => {
    setRefreshing(true)
    try {
      await api.refreshScores()
      load()
    } finally {
      setRefreshing(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-gray-400">Today's Scored Stocks</h2>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm text-gray-300 transition-colors"
        >
          <RefreshCw size={13} className={refreshing ? 'animate-spin' : ''} />
          {refreshing ? 'Scoring...' : 'Re-score'}
        </button>
      </div>

      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-gray-500 text-xs border-b border-gray-800">
              <th className="text-left pb-2 pr-4">#</th>
              <th className="text-left pb-2 pr-4">Symbol</th>
              <th className="text-right pb-2 pr-4">Score</th>
              <th className="text-right pb-2 pr-4">RSI</th>
              <th className="text-right pb-2 pr-4">MACD Hist</th>
              <th className="text-right pb-2 pr-4">Vol Ratio</th>
              <th className="text-right pb-2 pr-4">Mom 1D</th>
              <th className="text-right pb-2 pr-4">Mom 5D</th>
              <th className="text-right pb-2">LTP</th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr><td colSpan={9} className="py-8 text-center text-gray-500">Loading scores...</td></tr>
            )}
            {!loading && scores.length === 0 && (
              <tr>
                <td colSpan={9} className="py-8 text-center text-gray-500">
                  No scores yet — click Re-score or wait for 9:05 AM
                </td>
              </tr>
            )}
            {scores.map((s, i) => (
              <tr
                key={s.symbol}
                className={`border-b border-gray-800/40 ${
                  s.selected ? 'bg-green-900/10' : ''
                }`}
              >
                <td className="py-1.5 pr-4 text-gray-600 text-xs">{i + 1}</td>
                <td className="py-1.5 pr-4 font-semibold">
                  {s.symbol.replace('-EQ', '')}
                  {s.selected === 1 && (
                    <span className="ml-1.5 text-xs bg-green-900 text-green-300 px-1.5 py-0.5 rounded">
                      Selected
                    </span>
                  )}
                </td>
                <td className="py-1.5 pr-4 text-right">
                  <ScoreBar value={s.score} />
                </td>
                <td className={`py-1.5 pr-4 text-right ${rsiColor(s.rsi)}`}>
                  {s.rsi?.toFixed(1) ?? '—'}
                </td>
                <td className={`py-1.5 pr-4 text-right ${s.macd_hist > 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {s.macd_hist?.toFixed(3) ?? '—'}
                </td>
                <td className={`py-1.5 pr-4 text-right ${s.volume_ratio > 1.5 ? 'text-yellow-400' : 'text-gray-400'}`}>
                  {s.volume_ratio?.toFixed(1) ?? '—'}x
                </td>
                <td className={`py-1.5 pr-4 text-right ${momColor(s.momentum_1d)}`}>
                  {s.momentum_1d !== null ? `${s.momentum_1d?.toFixed(2)}%` : '—'}
                </td>
                <td className={`py-1.5 pr-4 text-right ${momColor(s.momentum_5d)}`}>
                  {s.momentum_5d !== null ? `${s.momentum_5d?.toFixed(2)}%` : '—'}
                </td>
                <td className="py-1.5 text-right text-gray-300">
                  {s.last_price ? `₹${s.last_price}` : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function ScoreBar({ value }) {
  const pct = Math.min(100, Math.max(0, value))
  const color = pct >= 70 ? 'bg-green-500' : pct >= 45 ? 'bg-yellow-500' : 'bg-red-500'
  return (
    <div className="flex items-center justify-end gap-2">
      <span className="text-xs font-semibold w-8 text-right">{pct.toFixed(0)}</span>
      <div className="w-20 bg-gray-800 rounded-full h-1.5 overflow-hidden">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

function rsiColor(rsi) {
  if (!rsi) return 'text-gray-400'
  if (rsi >= 70) return 'text-red-400'
  if (rsi <= 30) return 'text-blue-400'
  if (rsi >= 45 && rsi <= 65) return 'text-green-400'
  return 'text-gray-300'
}

function momColor(v) {
  if (v === null || v === undefined) return 'text-gray-400'
  return v > 0 ? 'text-green-400' : v < 0 ? 'text-red-400' : 'text-gray-400'
}
