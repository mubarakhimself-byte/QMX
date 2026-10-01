/**
 * DEMO DATA ONLY. Deterministic sample values for design review.
 * Not market data, not from the daemon, never persisted. Every surface
 * that renders this must show the Demo banner.
 */

/** Small seeded PRNG so demo screens look the same on every load. */
function rng(seed: number) {
  let s = seed >>> 0;
  return () => {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 4294967296;
  };
}

export type Candle = {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
};

export function demoCandles(days = 160, start = 1.085, seed = 7): Candle[] {
  const r = rng(seed);
  const out: Candle[] = [];
  let price = start;
  const d = new Date(Date.UTC(2026, 3, 1));
  while (out.length < days) {
    d.setUTCDate(d.getUTCDate() + 1);
    if (d.getUTCDay() === 0 || d.getUTCDay() === 6) continue;
    const open = price;
    const drift = (r() - 0.48) * 0.009;
    const close = +(open * (1 + drift)).toFixed(5);
    const high = +(Math.max(open, close) * (1 + r() * 0.004)).toFixed(5);
    const low = +(Math.min(open, close) * (1 - r() * 0.004)).toFixed(5);
    out.push({
      time: d.toISOString().slice(0, 10),
      open: +open.toFixed(5),
      high,
      low,
      close,
      volume: Math.round(40_000 + r() * 90_000),
    });
    price = close;
  }
  return out;
}

export type Quote = {
  symbol: string;
  last: number;
  change: number;
  spark: number[];
};

export function demoWatchlist(): Quote[] {
  const symbols: [string, number][] = [
    ["EURUSD", 1.0912],
    ["GBPUSD", 1.2745],
    ["USDJPY", 148.32],
    ["XAUUSD", 2384.1],
    ["US500", 5521.4],
    ["BTCUSD", 64210],
  ];
  return symbols.map(([symbol, last], i) => {
    const r = rng(100 + i);
    const spark: number[] = [];
    let v = last;
    for (let k = 0; k < 24; k++) {
      v *= 1 + (r() - 0.5) * 0.006;
      spark.push(v);
    }
    return {
      symbol,
      last: spark[spark.length - 1],
      change: (spark[spark.length - 1] / spark[0] - 1) * 100,
      spark,
    };
  });
}

export type CalendarEvent = {
  time: string;
  ccy: string;
  event: string;
  impact: "high" | "medium" | "low";
  forecast: string;
  previous: string;
};

export const DEMO_CALENDAR: { day: string; events: CalendarEvent[] }[] = [
  {
    day: "Today",
    events: [
      {
        time: "08:00",
        ccy: "EUR",
        event: "German CPI (m/m)",
        impact: "high",
        forecast: "0.2%",
        previous: "0.3%",
      },
      {
        time: "10:00",
        ccy: "EUR",
        event: "Eurozone unemployment",
        impact: "medium",
        forecast: "6.4%",
        previous: "6.4%",
      },
      {
        time: "14:30",
        ccy: "USD",
        event: "Initial jobless claims",
        impact: "medium",
        forecast: "221K",
        previous: "218K",
      },
      {
        time: "16:00",
        ccy: "USD",
        event: "ISM manufacturing PMI",
        impact: "high",
        forecast: "47.8",
        previous: "47.2",
      },
    ],
  },
  {
    day: "Tomorrow",
    events: [
      {
        time: "01:30",
        ccy: "AUD",
        event: "Retail sales (m/m)",
        impact: "medium",
        forecast: "0.3%",
        previous: "0.5%",
      },
      {
        time: "09:30",
        ccy: "GBP",
        event: "Services PMI",
        impact: "low",
        forecast: "52.1",
        previous: "52.4",
      },
      {
        time: "14:30",
        ccy: "USD",
        event: "Non-farm payrolls",
        impact: "high",
        forecast: "165K",
        previous: "142K",
      },
    ],
  },
];

export const DEMO_NEWS = [
  {
    age: "4m",
    source: "Sample Wire",
    title: "Euro area inflation cools for a second month, sample headline",
    tag: "EUR",
  },
  {
    age: "18m",
    source: "Sample Wire",
    title: "Treasury yields edge higher ahead of payrolls, sample headline",
    tag: "USD",
  },
  {
    age: "41m",
    source: "Desk note",
    title: "Gold holds near range highs as dollar softens, sample headline",
    tag: "XAU",
  },
  {
    age: "1h",
    source: "Sample Wire",
    title: "Bank of Japan minutes show split on next hike, sample headline",
    tag: "JPY",
  },
  {
    age: "2h",
    source: "Desk note",
    title: "Equity index futures flat into the US open, sample headline",
    tag: "US500",
  },
];

export type Position = {
  symbol: string;
  side: "Long" | "Short";
  size: number;
  pnl: number;
  exposure: number;
};

export const DEMO_BOOK: Position[] = [
  { symbol: "EURUSD", side: "Long", size: 1.2, pnl: 412.5, exposure: 38 },
  { symbol: "XAUUSD", side: "Long", size: 0.4, pnl: -96.2, exposure: 24 },
  { symbol: "USDJPY", side: "Short", size: 0.8, pnl: 158.0, exposure: 21 },
  { symbol: "US500", side: "Long", size: 0.2, pnl: -42.7, exposure: 17 },
];

export const DEMO_METRICS: [string, string][] = [
  ["Sharpe (90d)", "1.42"],
  ["Max drawdown", "−6.8%"],
  ["Win rate", "54.1%"],
  ["Avg R multiple", "1.31"],
  ["Trades (90d)", "187"],
  ["Exposure used", "62%"],
];
