import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { Save, Play, Square, AlertTriangle } from 'lucide-react'

export default function Settings({ isDemo }) {
  const [cfg, setCfg] = useState(null)
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState(null)

  useEffect(() => { api.getSettings().then(setCfg) }, [])

  const set = (key, val) => setCfg(prev => ({ ...prev, [key]: val }))

  const save = async () => {
    setSaving(true)
    setMsg(null)
    try {
      await api.updateSettings(cfg)
      setMsg({ type: 'ok', text: 'Settings saved — applies to next trade' })
    } catch (e) {
      setMsg({ type: 'err', text: e.message })
    } finally {
      setSaving(false)
    }
  }

  const startEngine = async () => {
    await api.startEngine()
    setMsg({ type: 'ok', text: 'Engine started' })
  }

  const stopEngine = async () => {
    await api.stopEngine()
    setMsg({ type: 'ok', text: 'Engine stopped' })
  }

  const squareOff = async () => {
    if (!window.confirm('Square off ALL open positions?')) return
    await api.squareOff()
    setMsg({ type: 'ok', text: 'All positions squared off' })
  }

  if (!cfg) return <div className="text-gray-500">Loading...</div>

  return (
    <div className="max-w-lg space-y-6">

      {/* Demo notice */}
      {isDemo && (
        <div className="card border-yellow-700/50 bg-yellow-900/20 text-yellow-300 text-sm">
          <strong>Demo mode</strong> — settings and engine controls are read-only here.
          Run the backend locally to make live changes.
        </div>
      )}

      {/* Engine controls */}
      <div className="card space-y-3">
        <h2 className="text-sm font-semibold text-gray-400">Engine Controls</h2>
        <div className="flex gap-3">
          <Btn icon={<Play size={14} />} label="Start Engine" color="green" onClick={startEngine} />
          <Btn icon={<Square size={14} />} label="Stop Engine" color="gray" onClick={stopEngine} />
          <Btn icon={<AlertTriangle size={14} />} label="Square Off All" color="red" onClick={squareOff} />
        </div>
      </div>

      {/* Capital */}
      <div className="card space-y-4">
        <h2 className="text-sm font-semibold text-gray-400">Capital & Position Sizing</h2>
        <Field
          label="Total Capital (₹)"
          value={cfg.trading_capital}
          onChange={v => set('trading_capital', parseFloat(v))}
          type="number" min={1000}
        />
        <Field
          label="Max Positions"
          value={cfg.max_positions}
          onChange={v => set('max_positions', parseInt(v))}
          type="number" min={1} max={10}
        />
        <Field
          label="Capital per Position (%)"
          value={(cfg.position_size_pct * 100).toFixed(0)}
          onChange={v => set('position_size_pct', parseFloat(v) / 100)}
          type="number" min={5} max={100}
        />
      </div>

      {/* Risk */}
      <div className="card space-y-4">
        <h2 className="text-sm font-semibold text-gray-400">Risk Management</h2>
        <Field
          label="Stop Loss (%)"
          value={(cfg.stop_loss_pct * 100).toFixed(1)}
          onChange={v => set('stop_loss_pct', parseFloat(v) / 100)}
          type="number" min={0.5} max={10} step={0.5}
          hint="Initial hard stop loss from entry"
        />
        <Field
          label="Profit Target (%)"
          value={(cfg.target_pct * 100).toFixed(1)}
          onChange={v => set('target_pct', parseFloat(v) / 100)}
          type="number" min={1} max={20} step={0.5}
          hint="Exit entire position when this gain is reached"
        />
        <Field
          label="Trailing Stop Loss (%)"
          value={(cfg.trailing_sl_pct * 100).toFixed(1)}
          onChange={v => set('trailing_sl_pct', parseFloat(v) / 100)}
          type="number" min={0.5} max={10} step={0.5}
          hint="SL trails behind highest price by this %. SL never drops below entry once profitable."
        />
      </div>

      {/* Market hours (read-only, change via .env) */}
      <div className="card space-y-2">
        <h2 className="text-sm font-semibold text-gray-400">Market Hours (IST)</h2>
        <div className="grid grid-cols-3 gap-3 text-sm">
          <InfoRow label="Open" value={cfg.market_open} />
          <InfoRow label="Square-off" value={cfg.square_off_time} />
          <InfoRow label="Close" value={cfg.market_close} />
        </div>
        <p className="text-xs text-gray-600 mt-1">Change via MARKET_OPEN / SQUARE_OFF_TIME in .env</p>
      </div>

      {msg && (
        <div className={`text-sm px-3 py-2 rounded-lg ${
          msg.type === 'ok' ? 'bg-green-900/40 text-green-300' : 'bg-red-900/40 text-red-300'
        }`}>
          {msg.text}
        </div>
      )}

      <button
        onClick={save}
        disabled={saving}
        className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-semibold transition-colors"
      >
        <Save size={14} />
        {saving ? 'Saving...' : 'Save Settings'}
      </button>
    </div>
  )
}

function Field({ label, value, onChange, type = 'text', hint, ...rest }) {
  return (
    <div>
      <label className="block text-xs text-gray-400 mb-1">{label}</label>
      <input
        type={type}
        value={value}
        onChange={e => onChange(e.target.value)}
        className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-blue-500"
        {...rest}
      />
      {hint && <p className="text-xs text-gray-600 mt-0.5">{hint}</p>}
    </div>
  )
}

function InfoRow({ label, value }) {
  return (
    <div className="bg-gray-800 rounded-lg px-3 py-2">
      <div className="text-xs text-gray-500">{label}</div>
      <div className="font-semibold">{value}</div>
    </div>
  )
}

function Btn({ icon, label, color, onClick }) {
  const colors = {
    green: 'bg-green-900 hover:bg-green-800 text-green-300',
    red:   'bg-red-900 hover:bg-red-800 text-red-300',
    gray:  'bg-gray-800 hover:bg-gray-700 text-gray-300',
  }
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-colors ${colors[color]}`}
    >
      {icon} {label}
    </button>
  )
}
