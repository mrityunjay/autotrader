// Demo data shown on GitHub Pages (no backend available)

export const mockStatus = {
  total_capital: 50000,
  deployed_capital: 18750,
  available_capital: 31250,
  open_positions: 3,
  realized_pnl_today: 1240,
  unrealized_pnl: 387,
  total_pnl_today: 1627,
  is_market_open: true,
  engine_running: true,
}

export const mockPositions = [
  {
    trade_id: 1,
    symbol: "RELIANCE-EQ",
    entry_price: 2845.50,
    quantity: 2,
    initial_sl: 2788.59,
    current_sl: 2845.50,  // locked at entry — in profit
    target: 2973.55,
    highest_price: 2921.00,
    ltp: 2910.20,
    in_profit_zone: true,
    unrealized_pnl: 129.40,
    unrealized_pnl_pct: 2.27,
  },
  {
    trade_id: 2,
    symbol: "HDFCBANK-EQ",
    entry_price: 1712.30,
    quantity: 5,
    initial_sl: 1678.05,
    current_sl: 1712.30,
    target: 1789.35,
    highest_price: 1748.00,
    ltp: 1741.80,
    in_profit_zone: true,
    unrealized_pnl: 147.50,
    unrealized_pnl_pct: 1.72,
  },
  {
    trade_id: 3,
    symbol: "INFY-EQ",
    entry_price: 1556.75,
    quantity: 4,
    initial_sl: 1525.62,
    current_sl: 1525.62,
    target: 1626.80,
    highest_price: 1556.75,
    ltp: 1539.20,
    in_profit_zone: false,
    unrealized_pnl: -70.20,
    unrealized_pnl_pct: -1.13,
  },
]

export const mockTrades = [
  { id: 1, symbol: "RELIANCE-EQ", entry_price: 2845.50, exit_price: null, quantity: 2, pnl: null, status: "OPEN", score: 82, created_at: today("09:22"), closed_at: null },
  { id: 2, symbol: "HDFCBANK-EQ", entry_price: 1712.30, exit_price: null, quantity: 5, pnl: null, status: "OPEN", score: 78, created_at: today("09:23"), closed_at: null },
  { id: 3, symbol: "INFY-EQ",     entry_price: 1556.75, exit_price: null, quantity: 4, pnl: null, status: "OPEN", score: 71, created_at: today("09:24"), closed_at: null },
  { id: 4, symbol: "SBIN-EQ",     entry_price: 832.40,  exit_price: 869.05, quantity: 8, pnl: 293.20, status: "CLOSED_TARGET",   score: 88, created_at: today("09:22"), closed_at: today("11:14") },
  { id: 5, symbol: "TCS-EQ",      entry_price: 3920.00, exit_price: 3958.80, quantity: 1, pnl: 38.80,  status: "CLOSED_TRAILING",  score: 74, created_at: today("09:25"), closed_at: today("12:02") },
  { id: 6, symbol: "AXISBANK-EQ", entry_price: 1187.50, exit_price: 1163.75, quantity: 5, pnl: -118.75, status: "CLOSED_STOPLOSS", score: 65, created_at: today("09:26"), closed_at: today("10:08") },
  { id: 7, symbol: "BAJFINANCE-EQ", entry_price: 7210.00, exit_price: 7530.45, quantity: 1, pnl: 320.45, status: "CLOSED_TARGET", score: 91, created_at: yesterday("09:21"), closed_at: yesterday("13:45") },
  { id: 8, symbol: "HCLTECH-EQ",  entry_price: 1643.20, exit_price: 1610.50, quantity: 3, pnl: -98.10, status: "CLOSED_STOPLOSS", score: 60, created_at: yesterday("09:23"), closed_at: yesterday("10:22") },
  { id: 9, symbol: "TITAN-EQ",    entry_price: 3412.00, exit_price: 3568.15, quantity: 1, pnl: 156.15, status: "CLOSED_TARGET",   score: 85, created_at: yesterday("09:22"), closed_at: yesterday("14:30") },
  { id: 10,symbol: "ITC-EQ",      entry_price: 458.30,  exit_price: 465.90,  quantity: 12, pnl: 91.20, status: "CLOSED_TRAILING", score: 76, created_at: yesterday("09:25"), closed_at: yesterday("12:18") },
]

export const mockScores = [
  { symbol: "BAJFINANCE-EQ", token: "317",   score: 91, rsi: 54.2, macd_hist: 12.4, volume_ratio: 2.3, momentum_1d: 1.8, momentum_5d: 3.2, last_price: 7380.00, selected: 1 },
  { symbol: "SBIN-EQ",       token: "3045",  score: 88, rsi: 57.1, macd_hist: 8.7,  volume_ratio: 1.9, momentum_1d: 1.2, momentum_5d: 2.8, last_price: 851.20, selected: 1 },
  { symbol: "RELIANCE-EQ",   token: "2885",  score: 82, rsi: 51.8, macd_hist: 6.2,  volume_ratio: 1.6, momentum_1d: 0.9, momentum_5d: 2.1, last_price: 2910.20, selected: 1 },
  { symbol: "HDFCBANK-EQ",   token: "1333",  score: 78, rsi: 48.5, macd_hist: 4.1,  volume_ratio: 1.5, momentum_1d: 0.7, momentum_5d: 1.9, last_price: 1741.80, selected: 1 },
  { symbol: "TITAN-EQ",      token: "3506",  score: 76, rsi: 52.3, macd_hist: 3.8,  volume_ratio: 1.4, momentum_1d: 0.6, momentum_5d: 1.5, last_price: 3580.50, selected: 1 },
  { symbol: "INFY-EQ",       token: "1594",  score: 71, rsi: 44.6, macd_hist: 2.1,  volume_ratio: 1.2, momentum_1d: -0.4, momentum_5d: 0.9, last_price: 1539.20, selected: 0 },
  { symbol: "TCS-EQ",        token: "11536", score: 68, rsi: 46.0, macd_hist: 1.8,  volume_ratio: 1.1, momentum_1d: 0.2, momentum_5d: 0.7, last_price: 3955.00, selected: 0 },
  { symbol: "WIPRO-EQ",      token: "3787",  score: 62, rsi: 42.0, macd_hist: 0.9,  volume_ratio: 1.0, momentum_1d: -0.2, momentum_5d: 0.4, last_price: 548.30, selected: 0 },
  { symbol: "AXISBANK-EQ",   token: "5900",  score: 55, rsi: 38.5, macd_hist: -1.2, volume_ratio: 0.9, momentum_1d: -0.8, momentum_5d: -0.5, last_price: 1168.40, selected: 0 },
  { symbol: "ONGC-EQ",       token: "2475",  score: 48, rsi: 35.2, macd_hist: -3.4, volume_ratio: 0.8, momentum_1d: -1.1, momentum_5d: -1.8, last_price: 261.50, selected: 0 },
]

export const mockDailyPnl = [
  { date: daysAgo(13), realized_pnl: 820,  trades_count: 5, winning_trades: 3, losing_trades: 2 },
  { date: daysAgo(12), realized_pnl: -210, trades_count: 4, winning_trades: 1, losing_trades: 3 },
  { date: daysAgo(11), realized_pnl: 1450, trades_count: 5, winning_trades: 4, losing_trades: 1 },
  { date: daysAgo(10), realized_pnl: 340,  trades_count: 3, winning_trades: 2, losing_trades: 1 },
  { date: daysAgo(9),  realized_pnl: -180, trades_count: 4, winning_trades: 1, losing_trades: 3 },
  { date: daysAgo(8),  realized_pnl: 980,  trades_count: 5, winning_trades: 3, losing_trades: 2 },
  { date: daysAgo(7),  realized_pnl: 1120, trades_count: 5, winning_trades: 4, losing_trades: 1 },
  { date: daysAgo(6),  realized_pnl: 560,  trades_count: 4, winning_trades: 3, losing_trades: 1 },
  { date: daysAgo(5),  realized_pnl: -340, trades_count: 5, winning_trades: 2, losing_trades: 3 },
  { date: daysAgo(4),  realized_pnl: 890,  trades_count: 4, winning_trades: 3, losing_trades: 1 },
  { date: daysAgo(3),  realized_pnl: 1680, trades_count: 5, winning_trades: 4, losing_trades: 1 },
  { date: daysAgo(2),  realized_pnl: 720,  trades_count: 4, winning_trades: 3, losing_trades: 1 },
  { date: daysAgo(1),  realized_pnl: 1050, trades_count: 5, winning_trades: 4, losing_trades: 1 },
  { date: daysAgo(0),  realized_pnl: 1240, trades_count: 3, winning_trades: 2, losing_trades: 1 },
]

function today(time) {
  return new Date().toISOString().slice(0, 10) + 'T' + time + ':00'
}
function yesterday(time) {
  const d = new Date(); d.setDate(d.getDate() - 1)
  return d.toISOString().slice(0, 10) + 'T' + time + ':00'
}
function daysAgo(n) {
  const d = new Date(); d.setDate(d.getDate() - n)
  return d.toISOString().slice(0, 10)
}
