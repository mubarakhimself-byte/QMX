// Demo content for the board widgets that is not one of his things: the
// economic calendar, headlines, open and closed positions, the jobs behind
// "Running now", and pods. Numbers are samples. Pods are not in the backend
// yet (being built, not merged): their shape here is an assumption, marked
// in pods() below.
import type { Fixture } from "./model";

const LONG_HOST = "trading-node-frankfurt-02.contabo-vps.internal";
const LONG_UNIT = "Gold London-open breakout with volatility filter and news guard v14-final";
export const serverName = (f: Fixture) => (f === "worst" ? LONG_HOST : "vps-fra");

// ------------------------------------------------------------ the calendar
export type Event = { id: string; city: "tok" | "lon" | "nyc"; zone: string; at: [number, number]; title: string; impact: "high" | "medium"; syms: string[] };
export const events: Event[] = [
  { id: "e1", city: "tok", zone: "Asia/Tokyo", at: [8, 50], title: "Japan GDP, quarter", impact: "medium", syms: ["USDJPY", "JP225"] },
  { id: "e2", city: "lon", zone: "Europe/London", at: [7, 0], title: "UK retail sales", impact: "medium", syms: ["UK100"] },
  { id: "e3", city: "lon", zone: "Europe/London", at: [10, 0], title: "Euro area inflation, flash", impact: "high", syms: ["EURUSD"] },
  { id: "e4", city: "nyc", zone: "America/New_York", at: [8, 30], title: "US CPI", impact: "high", syms: ["XAUUSD", "NAS100", "EURUSD"] },
  { id: "e5", city: "nyc", zone: "America/New_York", at: [10, 0], title: "US consumer sentiment", impact: "medium", syms: ["NAS100"] },
  { id: "e6", city: "nyc", zone: "America/New_York", at: [10, 30], title: "EIA crude stocks", impact: "medium", syms: ["USOIL"] },
  { id: "e7", city: "nyc", zone: "America/New_York", at: [14, 0], title: "Fed minutes", impact: "high", syms: ["XAUUSD", "NAS100", "BTCUSD"] },
  { id: "e8", city: "nyc", zone: "America/New_York", at: [16, 30], title: "API crude stocks", impact: "medium", syms: ["USOIL"] },
];

// Tomorrow's calendar, for a big Markets widget once today's is shown.
export const tomorrow: Event[] = [
  { id: "t1", city: "tok", zone: "Asia/Tokyo", at: [8, 50], title: "Japan trade balance", impact: "medium", syms: ["USDJPY"] },
  { id: "t2", city: "lon", zone: "Europe/London", at: [7, 0], title: "UK GDP, month", impact: "high", syms: ["UK100"] },
  { id: "t3", city: "lon", zone: "Europe/London", at: [12, 30], title: "ECB meeting account", impact: "medium", syms: ["EURUSD"] },
  { id: "t4", city: "nyc", zone: "America/New_York", at: [8, 30], title: "US jobless claims", impact: "medium", syms: ["NAS100"] },
  { id: "t5", city: "nyc", zone: "America/New_York", at: [8, 30], title: "US producer prices", impact: "high", syms: ["XAUUSD", "NAS100"] },
  { id: "t6", city: "nyc", zone: "America/New_York", at: [10, 30], title: "Natural gas storage", impact: "medium", syms: ["USOIL"] },
  { id: "t7", city: "nyc", zone: "America/New_York", at: [13, 0], title: "Baker Hughes rig count", impact: "medium", syms: ["USOIL"] },
  { id: "t8", city: "nyc", zone: "America/New_York", at: [14, 0], title: "Fed speaker", impact: "medium", syms: ["XAUUSD"] },
];

export type Headline = { id: string; text: string; source: string; ago: string; syms: string[] };
const baseHeadlines: Headline[] = [
  { id: "h1", text: "Gold holds near record as traders wait for US inflation", source: "Reuters", ago: "12m", syms: ["XAUUSD"] },
  { id: "h2", text: "Dollar slips against the yen after Tokyo GDP beat", source: "Bloomberg", ago: "38m", syms: ["USDJPY"] },
  { id: "h3", text: "ECB speakers keep a December cut on the table", source: "FT", ago: "1h", syms: ["EURUSD"] },
  { id: "h4", text: "Nasdaq futures flat ahead of CPI; chip stocks firm", source: "CNBC", ago: "1h", syms: ["NAS100"] },
  { id: "h5", text: "Bitcoin steadies above 63,000 after weekend swing", source: "CoinDesk", ago: "2h", syms: ["BTCUSD"] },
  { id: "h6", text: "Oil edges up on supply worries before inventory data", source: "Reuters", ago: "2h", syms: ["USOIL"] },
  { id: "h7", text: "UK retail sales miss; pound little changed", source: "Bloomberg", ago: "3h", syms: ["UK100"] },
  { id: "h8", text: "Silver tracks gold higher in quiet Asian trade", source: "Kitco", ago: "4h", syms: ["XAGUSD"] },
  { id: "h9", text: "Treasury yields edge lower before the inflation print", source: "Reuters", ago: "5h", syms: ["XAUUSD", "NAS100"] },
  { id: "h10", text: "Yen weakens as Tokyo officials stay quiet on intervention", source: "Nikkei", ago: "6h", syms: ["USDJPY"] },
  { id: "h11", text: "FTSE opens higher, miners lead", source: "Bloomberg", ago: "7h", syms: ["UK100"] },
  { id: "h12", text: "Crypto funds see a third week of inflows", source: "CoinDesk", ago: "8h", syms: ["BTCUSD"] },
  { id: "h13", text: "OPEC delegates see no change to output at next meeting", source: "Reuters", ago: "9h", syms: ["USOIL"] },
  { id: "h14", text: "Euro steady as German factory orders beat", source: "FT", ago: "10h", syms: ["EURUSD"] },
  { id: "h15", text: "Asian stocks mixed after a quiet Wall Street close", source: "Bloomberg", ago: "11h", syms: ["JP225"] },
  { id: "h16", text: "Gold miners rally with bullion near the high", source: "Kitco", ago: "12h", syms: ["XAUUSD"] },
];
export const headlines = (f: Fixture): Headline[] =>
  f === "worst"
    ? [{ id: "hw", text: "Central bank officials signal that the pace of balance-sheet reduction may slow sooner than markets expect, lifting bonds and gold", source: "Reuters via the news and sentiment scanner", ago: "1m", syms: ["XAUUSD", "EURUSD", "NAS100", "USDJPY"] }, ...baseHeadlines]
    : baseHeadlines;

// --------------------------------------------------------------- positions
export type Position = { id: string; unit: string; name: string; mode: "live" | "paper"; sym: string; side: string; entry: string; now: string; stop: string; opened: string; where: string };
export type Closed = { id: string; unit: string; name: string; mode: "live" | "paper"; sym: string; side: string; result: string; at: string };
export function positions(f: Fixture): { open: Position[]; closed: Closed[] } {
  if (f === "first") return { open: [], closed: [] };
  const host = serverName(f);
  const open: Position[] = [
    { id: "p1", unit: "u-gold", name: f === "worst" ? LONG_UNIT : "Gold breakout", mode: "live", sym: "XAUUSD", side: "Long 0.20", entry: "2,371.4", now: f === "worst" ? "-1,284,019.55R" : "+0.6R", stop: "2,358.0", opened: "08:02", where: host },
    { id: "p2", unit: "u-btc", name: "BTC trend", mode: "paper", sym: "BTCUSD", side: "Long 0.05", entry: "63,120", now: "+1.1R", stop: "61,900", opened: "Mon", where: "This PC" },
    { id: "p3", unit: "u-london", name: "London fade", mode: "paper", sym: "EURUSD", side: "Short 0.30", entry: "1.0874", now: "-0.2R", stop: "1.0896", opened: "09:14", where: "This PC" },
  ];
  const closed: Closed[] = [
    { id: "c1", unit: "u-index", name: "Index open drive", mode: "paper", sym: "NAS100", side: "Long", result: "+0.9R", at: "15:02" },
    { id: "c2", unit: "u-london", name: "London fade", mode: "paper", sym: "EURUSD", side: "Short", result: "-1.0R", at: "08:41" },
    { id: "c3", unit: "u-gold", name: "Gold breakout", mode: "live", sym: "XAUUSD", side: "Short", result: "+1.4R", at: "07:55" },
    { id: "c4", unit: "u-btc", name: "BTC trend", mode: "paper", sym: "BTCUSD", side: "Long", result: "+0.4R", at: "03:10" },
    { id: "c5", unit: "u-index", name: "Index open drive", mode: "paper", sym: "NAS100", side: "Short", result: "-0.5R", at: "Yesterday" },
    { id: "c6", unit: "u-london", name: "London fade", mode: "paper", sym: "EURUSD", side: "Short", result: "+0.7R", at: "Yesterday" },
    ...older,
  ];
  return { open, closed };
}

// The week before: enough history that a big widget is never short of rows.
const days = ["Mon", "Mon", "Fri", "Fri", "Thu", "Thu", "Wed", "Wed", "Tue", "Tue", "Mon 3rd", "Mon 3rd", "Fri 31st", "Fri 31st", "Thu 30th", "Thu 30th", "Wed 29th", "Wed 29th"];
const who = [
  ["u-gold", "Gold breakout", "live", "XAUUSD"],
  ["u-london", "London fade", "paper", "EURUSD"],
  ["u-btc", "BTC trend", "paper", "BTCUSD"],
  ["u-index", "Index open drive", "paper", "NAS100"],
] as const;
const older: Closed[] = days.map((at, i) => {
  const [unit, name, mode, sym] = who[i % 4];
  const r = [0.9, -1.0, 1.4, 0.3, -0.5, 2.1, -1.0, 0.6, 0.2, -0.4, 1.1, -1.0, 0.8, 0.5, -0.7, 1.6, -1.0, 0.4][i];
  return { id: `c-old${i}`, unit, name, mode, sym, side: i % 3 ? "Long" : "Short", result: `${r > 0 ? "+" : "-"}${Math.abs(r).toFixed(1)}R`, at };
});

// ------------------------------------------------------- jobs (Running now)
export type JobState = "run" | "needs" | "done" | "down" | "next";
export type Job = { id: string; name: string; where: string; state: JobState; of?: string };
export function jobs(f: Fixture): Job[] {
  if (f === "first") return [];
  const host = serverName(f);
  const out: Job[] = [];
  const add = (j: Job) => out.push(j);
  const cells = f === "worst" ? 212 : 24;
  for (let i = 1; i <= cells; i++) add({ id: `sw${i}`, of: "r-518", name: `Sweep cell ${i} of ${cells}: Gold breakout`, where: "This PC", state: i <= cells * 0.54 ? "done" : i <= cells * 0.54 + 3 ? "run" : "next" });
  for (let i = 1; i <= 12; i++) add({ id: `wf${i}`, of: "r-516", name: `Walk-forward fold ${i} of 12: London fade v3`, where: host, state: i <= 6 ? "done" : i === 7 ? "run" : "next" });
  add({ id: "j-topup", of: "r-topup", name: "Data top-up · 09:00", where: "This PC", state: "run" });
  for (let i = 1; i <= 8; i++) add({ id: `tu${i}`, of: "w-topup", name: `Data top-up · 0${i}:00`, where: "This PC", state: "done" });
  add({ id: "j-h1", of: "r-helper1", name: "Researcher · reading 14 backtest results", where: host, state: "run" });
  add({ id: "j-h2", of: "r-helper2", name: "Data analyst · rebuilding EURUSD H1 bars", where: "This PC", state: "needs" });
  add({ id: "j-n", of: "r-nightly", name: "Nightly evidence · 02:00", where: host, state: "down" });
  add({ id: "j-b", of: "r-brief", name: "Morning brief · 07:00", where: "This PC", state: "done" });
  add({ id: "j-r", of: "r-515", name: "Robustness: Gold breakout XAGUSD", where: host, state: "next" });
  if (f === "worst") for (let i = 1; i <= 1000; i++) add({ id: `x${i}`, name: `Backtest ${i}`, where: i % 2 ? "This PC" : host, state: i % 97 ? "done" : "down" });
  return out;
}

// -------------------------------------------------------------------- pods
// ASSUMPTION (pods are not merged in the backend yet): a pod is a named group
// of units of one trading style with its own risk rule (risk per trade, a
// day stop in R, a cap on open trades). Each unit sits in one pod; a pod has
// a live side and a paper side, each with today's result. "Room" is how much
// of the day stop is left, live side.
export type Pod = {
  id: string;
  name: string;
  style: string;
  units: string[];
  live: { today: string; open: number } | null;
  paper: { today: string; open: number } | null;
  room: { left: number; stop: number };
  rules: [string, string][];
};
export function pods(f: Fixture): Pod[] {
  if (f === "first") return [];
  const list: Pod[] = [
    { id: "pod-break", name: "Breakouts", style: "Session-open breakouts", units: ["u-gold"], live: { today: "+0.8R", open: 1 }, paper: null, room: { left: 4.2, stop: 6 }, rules: [["Risk per trade", "0.5%"], ["Day stop", "-6R"], ["Open at once", "2"]] },
    { id: "pod-scalp", name: "Scalpers", style: "Fast fades and opening drives", units: ["u-london", "u-index"], live: null, paper: { today: "-0.3R", open: 1 }, room: { left: 5.7, stop: 6 }, rules: [["Risk per trade", "0.25%"], ["Day stop", "-6R"], ["Open at once", "3"]] },
    { id: "pod-trend", name: "Trend", style: "Multi-day trend following", units: ["u-btc"], live: null, paper: { today: "+1.4R", open: 1 }, room: { left: 8, stop: 8 }, rules: [["Risk per trade", "0.75%"], ["Day stop", "-8R"], ["Open at once", "4"]] },
    { id: "pod-revert", name: "Mean reversion", style: "Range and reversal trades", units: ["u-asia", "u-oil"], live: null, paper: null, room: { left: 5, stop: 5 }, rules: [["Risk per trade", "0.5%"], ["Day stop", "-5R"], ["Open at once", "2"]] },
  ];
  if (f !== "worst") return list;
  return [
    { id: "pod-long", name: "London and New York opening-range breakouts with news guard", style: "Session-open breakouts", units: ["u-gold", ...Array.from({ length: 13 }, (_, i) => `u-x${i + 1}`)], live: { today: "-1,284,019.55R", open: 9 }, paper: { today: "+0.1R", open: 1 }, room: { left: 0.2, stop: 6 }, rules: [["Risk per trade", "0.5%"], ["Day stop", "-6R"], ["Open at once", "12"]] },
    ...list.slice(1),
    { id: "pod-jo", name: "Jo", style: "Test pod", units: ["u-x20"], live: null, paper: null, room: { left: 1, stop: 1 }, rules: [["Risk per trade", "0.1%"], ["Day stop", "-1R"], ["Open at once", "1"]] },
  ];
}

// ------------------------------------------------- history for the fillers
export const decided = [
  { id: "d1", text: "Allowed: download GBPUSD ticks for 2024", when: "Yesterday", tone: "up" },
  { id: "d2", text: "Promoted BTC trend to paper on BTCUSD", when: "Mon", tone: "up" },
  { id: "d3", text: "Not yet: Index open drive to live, too few trades", when: "Mon", tone: "idle" },
  { id: "d4", text: "Retried Data top-up after a feed timeout", when: "Sun", tone: "up" },
  { id: "d5", text: "Rejected: delete raw EURUSD ticks before 2015", when: "Sat", tone: "idle" },
  { id: "d6", text: "Promoted Gold breakout to live on XAUUSD", when: "12 Oct", tone: "up" },
  { id: "d7", text: "Allowed: the copilot to run a 24-cell sweep", when: "11 Oct", tone: "up" },
  { id: "d8", text: "Not yet: BTC trend to live, drawdown too deep", when: "10 Oct", tone: "idle" },
  { id: "d9", text: "Retried Nightly evidence after a timeout", when: "9 Oct", tone: "up" },
  { id: "d10", text: "Promoted London fade to paper on EURUSD", when: "8 Oct", tone: "up" },
  { id: "d11", text: "Rejected: a proposal that used look-ahead data", when: "7 Oct", tone: "idle" },
  { id: "d12", text: "Allowed: download XAUUSD ticks for 2023", when: "6 Oct", tone: "up" },
  { id: "d13", text: "Promoted Index open drive to paper on NAS100", when: "5 Oct", tone: "up" },
  { id: "d14", text: "Not yet: Asia range to paper, too few trades", when: "4 Oct", tone: "idle" },
  { id: "d15", text: "Retried Data top-up after a feed timeout", when: "3 Oct", tone: "up" },
  { id: "d16", text: "Promoted BTC trend to tested after its sweep", when: "2 Oct", tone: "up" },
  { id: "d17", text: "Allowed: the Researcher to read 40 old backtests", when: "1 Oct", tone: "up" },
  { id: "d18", text: "Rejected: delete unused workflows", when: "30 Sep", tone: "idle" },
];
export const earlier = [
  { id: "y1", text: "BTC trend closed +0.4R on BTCUSD", when: "03:10", tone: "up" },
  { id: "y2", text: "Data top-up ran 8 times", when: "since 01:00", tone: "up" },
  { id: "y3", text: "Weekend watch found nothing to flag", when: "Sun", tone: "idle" },
  { id: "y4", text: "Morning brief: London fade spread above its limit twice", when: "Sun", tone: "paper" },
  { id: "y5", text: "Index open drive closed -0.5R on NAS100", when: "Fri", tone: "down" },
  { id: "y6", text: "Frankfurt node signed in again after a restart", when: "Fri", tone: "up" },
  { id: "y7", text: "Gold breakout closed +1.4R on XAUUSD", when: "Fri", tone: "up" },
  { id: "y8", text: "Nightly evidence passed; 1 proposal written", when: "Fri", tone: "up" },
  { id: "y9", text: "London fade skipped: spread above its limit", when: "Thu", tone: "paper" },
  { id: "y10", text: "Sweep finished: 24 of 24 cells", when: "Thu", tone: "up" },
  { id: "y11", text: "Data top-up failed once, then recovered", when: "Thu", tone: "down" },
  { id: "y12", text: "BTC trend closed -1.0R at its stop", when: "Wed", tone: "down" },
  { id: "y13", text: "Morning brief is ready", when: "Wed", tone: "up" },
  { id: "y14", text: "Home node updated to 0.9.0", when: "Wed", tone: "up" },
  { id: "y15", text: "Index open drive closed +0.9R", when: "Tue", tone: "up" },
  { id: "y16", text: "Nightly evidence passed; nothing to propose", when: "Tue", tone: "up" },
  { id: "y17", text: "Weekend watch found a gap in EURUSD ticks", when: "Mon 3rd", tone: "paper" },
  { id: "y18", text: "Frankfurt node renewed its sign-in", when: "Mon 3rd", tone: "up" },
];

// What the nodes did lately, for the Nodes widget's spare room.
export const nodeLog = [
  { id: "nl1", node: "Home node", text: "Heartbeat steady, 4s", when: "Now", tone: "up" },
  { id: "nl2", node: "Frankfurt node", text: "Placed Gold breakout on XAUUSD", when: "12 Oct", tone: "live" },
  { id: "nl3", node: "Home node", text: "Placed BTC trend on BTCUSD", when: "Mon", tone: "paper" },
  { id: "nl4", node: "Frankfurt node", text: "Restarted after an update", when: "Fri", tone: "up" },
  { id: "nl5", node: "Home node", text: "Sign-in expires in 2 days", when: "Today", tone: "paper" },
  { id: "nl6", node: "Home node", text: "Placed London fade on EURUSD", when: "8 Oct", tone: "paper" },
  { id: "nl7", node: "Frankfurt node", text: "Heartbeat missed once, then back", when: "Thu", tone: "down" },
  { id: "nl8", node: "Home node", text: "Placed Index open drive on NAS100", when: "5 Oct", tone: "paper" },
  { id: "nl9", node: "Frankfurt node", text: "Signed in to cTrader live", when: "1 Oct", tone: "up" },
  { id: "nl10", node: "Home node", text: "Updated to 0.9.0", when: "Wed", tone: "up" },
  { id: "nl11", node: "Home node", text: "Signed in to cTrader demo", when: "28 Sep", tone: "up" },
  { id: "nl12", node: "Frankfurt node", text: "Started on vps-fra", when: "27 Sep", tone: "up" },
  { id: "nl13", node: "Home node", text: "Started on This PC", when: "21 Sep", tone: "up" },
];
