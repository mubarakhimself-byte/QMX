/**
 * DEMO instruments: CFDs through cTrader (IC Markets) and crypto through CCXT
 * exchanges (operator, 2026-10-07: "we are going back to trading CFD").
 * One list so Home, Portfolio and the Library agree on prices and names.
 */
export type MarketKind = "fx" | "index" | "metal" | "energy" | "crypto";

export type Instrument = {
  sym: string;
  name: string;
  kind: MarketKind;
  px: number;
  chg: number;
  digits: number;
};

export const MARKETS: Instrument[] = [
  {
    sym: "EURUSD",
    name: "Euro / US dollar",
    kind: "fx",
    px: 1.0883,
    chg: 0.22,
    digits: 5,
  },
  {
    sym: "GBPUSD",
    name: "Pound / US dollar",
    kind: "fx",
    px: 1.3021,
    chg: -0.14,
    digits: 5,
  },
  {
    sym: "USDJPY",
    name: "US dollar / yen",
    kind: "fx",
    px: 149.32,
    chg: 0.31,
    digits: 3,
  },
  {
    sym: "XAUUSD",
    name: "Gold",
    kind: "metal",
    px: 2384.1,
    chg: -0.22,
    digits: 2,
  },
  {
    sym: "US500",
    name: "US 500 index",
    kind: "index",
    px: 5612.4,
    chg: 0.48,
    digits: 1,
  },
  {
    sym: "NAS100",
    name: "Nasdaq 100 index",
    kind: "index",
    px: 19742.6,
    chg: 0.71,
    digits: 1,
  },
  {
    sym: "USOIL",
    name: "WTI crude oil",
    kind: "energy",
    px: 71.85,
    chg: -1.12,
    digits: 2,
  },
  {
    sym: "BTC",
    name: "Bitcoin",
    kind: "crypto",
    px: 64210,
    chg: 1.83,
    digits: 0,
  },
  { sym: "ETH", name: "Ether", kind: "crypto", px: 3118, chg: 2.41, digits: 1 },
  {
    sym: "SOL",
    name: "Solana",
    kind: "crypto",
    px: 141.2,
    chg: -3.1,
    digits: 2,
  },
];

export const isCfd = (kind: MarketKind) => kind !== "crypto";

/** The instrument behind a bot's symbol ("BTCUSDT" is BTC on an exchange). */
export const instrumentFor = (symbol: string) =>
  MARKETS.find((m) => m.sym === symbol.replace(/USDT$/, ""));
