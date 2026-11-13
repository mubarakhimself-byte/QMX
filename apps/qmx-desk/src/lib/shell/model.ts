// His things. The app is the Board's places, and behind every widget row
// is one of these things with its own page. Every thing has a kind, a state and
// a page; a page is a header (who it is, where it is in its life, what you
// can do) plus sections. Kinds, sections and actions are data, so a mini app
// extends a thing by adding a section or an action, never by filling a tile.
//
// Nouns follow kit/refs/grounding/08 (unit lifecycle per market, runs with a
// place, sessions with helpers, workflows with the closed inbox actions).
// Numbers are samples.
import type { Row, State } from "$lib/shell/data";

export type Fixture = "demo" | "worst" | "first";
export type Kind = "unit" | "proposal" | "session" | "run" | "workflow" | "node" | "app";
export type Life = "draft" | "tested" | "paper" | "live" | "stopped" | "retired";

export type Market = { sym: string; life: Life; paused?: boolean; node?: string; target?: Life };

export type Body =
  | { t: "stats"; stats: { label: string; value: string; tone?: "up" | "down" }[] }
  | { t: "spark"; series: number[]; note?: string; mode?: "live" | "paper"; b?: number[] }
  | { t: "links"; ids: string[] }
  | { t: "rows"; rows: Row[] }
  | { t: "table"; cols: string[]; rows: string[][] }
  | { t: "facts"; facts: [string, string][] };

export type Section = { id: string; title: string; icon: string; body: Body; full?: Body; wide?: boolean; guest?: string };

export type Evidence = {
  verdict: string;
  verdictTone: "up" | "down";
  judge: string;
  tries: { n: number; what: string; result: string; tone?: "up" | "down"; counted: boolean }[];
  series: number[];
  stats: { label: string; value: string; tone?: "up" | "down" }[];
  costs: [string, string, ("up" | "down")?][];
  unit: string;
  sym: string;
  from: Life;
  to: Life;
  node: string;
  by: string;
};

export type Obj = {
  id: string;
  kind: Kind;
  name: string;
  word: string; // the state, in his words
  tone: State;
  line?: string;
  where?: string;
  when?: string;
  markets?: Market[];
  sections?: Section[];
  evidence?: Evidence;
  needs?: boolean; // waits for him
  target?: string; // a needs-you item that is really another object (approval lives in a session)
  version?: string;
};

export type Guest = { id: string; name: string; icon: string; hue: number };

// Mini apps bring their own colour. Hues sit between the state colours, and a
// guest is always drawn with a dashed edge and its name, so it never reads as
// a state.
export const guests: Guest[] = [
  { id: "mis", name: "Market intelligence", icon: "radar", hue: 350 },
  { id: "exch", name: "Exchange status", icon: "signal", hue: 115 },
];
export const worstGuests: Guest[] = [
  { id: "news", name: "News and sentiment scanner for the London and New York opens", icon: "radar", hue: 45 },
  { id: "corr", name: "Correlations", icon: "activity", hue: 280 },
  { id: "cal", name: "Economic calendar", icon: "calendar", hue: 175 },
  { id: "scr", name: "Screener", icon: "search", hue: 230 },
];
export const guestInk = (hue: number) => `oklch(0.82 0.11 ${hue})`;
export const guestWash = (hue: number) => `oklch(0.82 0.11 ${hue} / 0.12)`;

const curve = (seed: number, n = 48, drift = 0.6) => {
  let v = 50;
  let s = seed;
  return Array.from({ length: n }, () => {
    s = (s * 9301 + 49297) % 233280;
    v += (s / 233280 - 0.5 + drift * 0.08) * 9;
    return Math.round(v * 10) / 10;
  });
};

export const PC = "This PC";
export const SERVER = "vps-fra";

// ---------------------------------------------------------------- the things
const gold: Obj = {
  id: "u-gold",
  kind: "unit",
  name: "Gold breakout",
  version: "v4",
  word: "live",
  tone: "live",
  line: "Buys the London-open break of the Asian range on gold",
  where: SERVER,
  when: "Today",
  markets: [
    { sym: "XAUUSD", life: "live", node: "n-fra" },
    { sym: "XAGUSD", life: "tested", target: "paper" },
  ],
  sections: [
    {
      id: "results",
      title: "Results",
      icon: "line-chart",
      wide: true,
      body: { t: "spark", series: curve(11, 48, 1), note: "+14.2R since live on 12 Oct · 187 trades", mode: "live" },
      full: { t: "table", cols: ["Month", "Trades", "Result", "Worst day", "Costs"], rows: [["November", "11", "+2.1R", "-1.0R", "$18.40"], ["October", "34", "+6.4R", "-2.2R", "$61.10"], ["September (paper)", "41", "+3.9R", "-1.8R", "$0.00"], ["August (paper)", "38", "+1.8R", "-2.6R", "$0.00"]] },
    },
    {
      id: "numbers",
      title: "Numbers",
      icon: "gauge",
      body: { t: "stats", stats: [{ label: "Today", value: "+0.8R", tone: "up" }, { label: "Expectancy", value: "+0.31R" }, { label: "Max drawdown", value: "-6.8R", tone: "down" }, { label: "Win rate", value: "46%" }] },
    },
    {
      id: "journal",
      title: "Journal",
      icon: "list",
      body: {
        t: "rows",
        rows: [
          { label: "Entered long 0.20 at 2,371.4", meta: "08:02", state: "live" },
          { label: "Asian range 2,358.0 to 2,370.9", meta: "07:59", state: "idle" },
          { label: "Skipped: spread 4.1 above 3.5", meta: "Yesterday", state: "paper" },
          { label: "Closed +1.4R at target", meta: "Mon", state: "up" },
        ],
      },
      full: {
        t: "table",
        cols: ["When", "Market", "What happened", "Why", "Result"],
        rows: [
          ["Today 08:02", "XAUUSD", "Entered long 0.20", "Break of 2,370.9", "+0.6R"],
          ["Today 07:59", "XAUUSD", "Range set", "2,358.0 to 2,370.9", ""],
          ["Yesterday 08:00", "XAUUSD", "Skipped", "Spread 4.1 above 3.5", ""],
          ["Mon 08:04", "XAUUSD", "Entered short 0.20", "Break of 2,341.2", "+1.4R"],
          ["Mon 11:20", "XAUUSD", "Closed at target", "2.0 ranges", "+1.4R"],
          ["Fri 08:01", "XAUUSD", "Entered long 0.20", "Break of 2,402.5", "-1.0R"],
          ["Fri 09:13", "XAUUSD", "Stopped out", "Stop at range low", "-1.0R"],
          ["Thu 08:00", "XAUUSD", "Skipped", "News guard: CPI", ""],
        ],
      },
    },
    {
      id: "where",
      title: "Where it runs",
      icon: "server",
      body: { t: "facts", facts: [["XAUUSD", "Frankfurt node · vps-fra"], ["Account", "cTrader live"], ["XAGUSD", "Not placed yet"], ["Backtests", "This PC"]] },
    },
    {
      id: "position",
      title: "Open position",
      icon: "candlestick",
      body: { t: "stats", stats: [{ label: "XAUUSD", value: "Long 0.20" }, { label: "Entry", value: "2,371.4" }, { label: "Now", value: "+0.6R", tone: "up" }, { label: "Stop", value: "2,358.0" }] },
    },
    {
      id: "proof",
      title: "Proof",
      icon: "scale",
      body: {
        t: "table",
        cols: ["Version", "Verdict", "Tries", "Made"],
        rows: [["v4", "passed", "3", "12 Oct"], ["v3", "failed", "2", "2 Oct"], ["v2", "failed", "4", "28 Sep"], ["v1", "draft", "0", "21 Sep"]],
      },
    },
    { id: "used", title: "Linked", icon: "route", body: { t: "links", ids: ["p-gold", "s-regime", "w-nightly", "n-fra"] } },
  ],
};

const unit = (id: string, name: string, sym: string, life: Life, line: string, today: string, total: string, seed: number, node = "n-home"): Obj => ({
  id,
  kind: "unit",
  name,
  version: "v" + ((seed % 4) + 1),
  word: life,
  tone: life === "live" ? "live" : life === "paper" ? "paper" : life === "tested" ? "idle" : life === "draft" ? "idle" : "down",
  line,
  where: life === "paper" || life === "live" ? PC : undefined,
  when: ["Today", "Yesterday", "Mon", "Sun"][seed % 4],
  markets: [{ sym, life, node: life === "paper" || life === "live" ? node : undefined }],
  sections: [
    { id: "results", title: "Results", icon: "line-chart", wide: true, body: { t: "spark", series: curve(seed, 48, 0.5), note: `${total} since start`, mode: life === "paper" ? "paper" : undefined } },
    { id: "numbers", title: "Numbers", icon: "gauge", body: { t: "stats", stats: [{ label: "Today", value: today, tone: today.startsWith("-") ? "down" : today.startsWith("+") ? "up" : undefined }, { label: "Since start", value: total }] } },
    { id: "where", title: "Where it runs", icon: "server", body: { t: "facts", facts: [[sym, life === "paper" ? "Home node · This PC" : "Not placed"], ["Account", life === "paper" ? "cTrader demo" : "None"]] } },
  ],
});

const londonEv: Evidence = {
  verdict: "Passed",
  verdictTone: "up",
  judge: "9 days on paper match the backtest within its range",
  tries: [
    { n: 1, what: "Stop 1.0 ATR", result: "-2.1%", tone: "down", counted: true },
    { n: 2, what: "Stop 1.5 ATR", result: "+1.8%", tone: "up", counted: true },
    { n: 3, what: "Session filter", result: "+3.0%", tone: "up", counted: true },
    { n: 4, what: "News guard", result: "+3.4%", tone: "up", counted: true },
    { n: 5, what: "Paper, 9 days", result: "+3.1R", tone: "up", counted: true },
  ],
  series: curve(5, 48, 0.4),
  stats: [{ label: "Expectancy", value: "+0.18R" }, { label: "Max drawdown", value: "-4.2R", tone: "down" }, { label: "Trades", value: "212" }, { label: "Paper days", value: "9" }],
  costs: [["Costs ×2", "64% kept", "up"], ["Spread, average", "0.9 pips"], ["Commission, 30 days", "$41.20"], ["Slippage on paper", "0.2 pips"]],
  unit: "u-london",
  sym: "EURUSD",
  from: "paper",
  to: "live",
  node: "Frankfurt node · vps-fra · cTrader live",
  by: "Nightly evidence",
};

const goldEv: Evidence = {
  verdict: "Passed",
  verdictTone: "up",
  judge: "Holds out of sample and after doubled costs",
  tries: [
    { n: 1, what: "Same rules as XAUUSD", result: "-0.8%", tone: "down", counted: true },
    { n: 2, what: "Range from 06:00", result: "+9.4%", tone: "up", counted: true },
    { n: 3, what: "Wider stop, 1.5 ranges", result: "+12.1%", tone: "up", counted: true },
  ],
  series: curve(3, 48, 1.2),
  stats: [{ label: "Expectancy", value: "+0.27R" }, { label: "Max drawdown", value: "-7.9R", tone: "down" }, { label: "Trades", value: "164" }, { label: "Out of sample", value: "+4.1R", tone: "up" }],
  costs: [["Costs ×2", "71% kept", "up"], ["Shuffle test", "-11.2%", "down"], ["Spread, average", "2.4 cents"], ["Commission per trade", "$3.10"]],
  unit: "u-gold",
  sym: "XAGUSD",
  from: "tested",
  to: "paper",
  node: "Home node · This PC · cTrader demo",
  by: "Nightly evidence",
};

const session: Obj = {
  id: "s-regime",
  kind: "session",
  name: "Regime study v3 against v1",
  word: "working",
  tone: "run",
  line: "2 helpers · 2 days",
  where: PC,
  when: "Now",
};

const others: Obj[] = [
  unit("u-london", "London fade", "EURUSD", "paper", "Fades the first London push on EURUSD", "-0.3R", "+3.1R", 5),
  unit("u-btc", "BTC trend", "BTCUSD", "paper", "Follows the four-hour trend on bitcoin", "+1.4R", "+6.7R", 17),
  unit("u-index", "Index open drive", "NAS100", "paper", "Trades the first 30 minutes of the Nasdaq open", "0.0R", "+0.9R", 23),
  unit("u-asia", "Asia range", "USDJPY", "tested", "Range trade during Tokyo hours", "", "-2.3%", 9),
  unit("u-oil", "Oil mean revert", "USOIL", "draft", "Buys oil after three down days", "", "Not judged", 13),

  {
    id: "p-gold",
    kind: "proposal",
    name: "Promote Gold breakout to paper",
    word: "needs you",
    tone: "needs",
    needs: true,
    line: "On XAGUSD · from Nightly evidence",
    when: "12m",
    evidence: goldEv,
  },
  {
    id: "p-london",
    kind: "proposal",
    name: "Promote London fade to live",
    word: "needs you",
    tone: "needs",
    needs: true,
    line: "On EURUSD · after 9 days on paper",
    when: "1h",
    evidence: londonEv,
  },
  {
    id: "a-ticks",
    kind: "session",
    name: "Allow the copilot to download 2024 EURUSD ticks",
    word: "needs you",
    tone: "needs",
    needs: true,
    line: "Approval in Regime study v3 against v1",
    when: "4m",
    target: "s-regime",
  },
  session,
  { id: "s-news", kind: "session", name: "Build a news-sentiment workflow", word: "working", tone: "run", line: "1 helper · 40m", where: PC, when: "40m",
    sections: [{ id: "chat", title: "Last messages", icon: "message-square", wide: true, body: { t: "rows", rows: [{ label: "You: build me a workflow that scores news before the London open", state: "idle" }, { label: "Copilot: drafting 5 steps, testing on last week", state: "run", where: PC }] } }] },
  { id: "s-why", kind: "session", name: "Why didn't London fade trade at 08:00?", word: "settled", tone: "idle", line: "Answered: spread above its limit", when: "Today",
    sections: [{ id: "chat", title: "Answer", icon: "message-square", wide: true, body: { t: "rows", rows: [{ label: "Spread was 1.4 pips at 08:00; the unit's limit is 1.2", state: "up" }, { label: "It traded at 08:07 once the spread fell", state: "idle" }] } }] },
  { id: "s-vr", kind: "session", name: "Explain the variance-ratio reading", word: "settled", tone: "idle", line: "Market intelligence reading", when: "Yesterday" },

  {
    id: "w-nightly",
    kind: "workflow",
    name: "Nightly evidence",
    word: "failed",
    tone: "down",
    needs: true,
    line: "Failed on step 4 of 5 at 02:41",
    where: SERVER,
    when: "02:00",
    sections: [
      {
        id: "lastrun",
        title: "Last run · 02:00",
        icon: "list-tree",
        wide: true,
        body: { t: "table", cols: ["Step", "Kind", "Took", "State"], rows: [["Load datasets", "script", "4s", "done"], ["Backtest 4 units", "app op", "6m 12s", "done"], ["Judge results", "grader", "9s", "done"], ["Write proposal: BTC trend", "agent", "1m 03s", "failed"], ["Save to Library", "library", "", "queued"]] },
      },
      { id: "error", title: "What failed", icon: "stop", body: { t: "rows", rows: [{ label: "The agent step ran out of time writing the BTC trend proposal", state: "down", where: SERVER }, { label: "Two proposals were written before it failed", state: "up" }] } },
      { id: "trigger", title: "When it runs", icon: "calendar-clock", body: { t: "facts", facts: [["Schedule", "Every night at 02:00"], ["Version", "v7, published"], ["Where", "vps-fra"], ["Model", "DeepSeek"]] } },
      { id: "runs", title: "Recent runs", icon: "table", body: { t: "table", cols: ["Night", "Took", "State"], rows: [["Tonight", "8m 31s", "failed"], ["Sun", "7m 58s", "passed"], ["Sat", "8m 10s", "passed"], ["Fri", "7m 44s", "passed"]] } },
    ],
  },
  { id: "w-brief", kind: "workflow", name: "Morning brief", word: "passed", tone: "up", line: "Ran at 07:00 in 41s", where: PC, when: "07:00" },
  { id: "w-topup", kind: "workflow", name: "Data top-up", word: "running", tone: "run", line: "Every hour · 24 runs today", where: PC, when: "Now" },
  { id: "w-news", kind: "workflow", name: "News sentiment", word: "draft", tone: "idle", line: "Draft · not published", when: "Today" },
  { id: "w-weekend", kind: "workflow", name: "Weekend watch", word: "waiting", tone: "idle", line: "Saturday 00:00", where: SERVER, when: "Sat" },

  { id: "r-518", kind: "run", name: "Sweep: Gold breakout, 6 markets × 4 timeframes", word: "running", tone: "run", line: "53% · 13 of 24 cells", where: PC, when: "Now",
    sections: [{ id: "progress", title: "Progress", icon: "loader", body: { t: "stats", stats: [{ label: "Cells done", value: "13 of 24" }, { label: "Best so far", value: "+26.2%", tone: "up" }] } }, { id: "where", title: "Where it runs", icon: "laptop", body: { t: "facts", facts: [["Machine", "This PC"], ["Placed by", "Default"], ["Started", "06:12"]] } }] },
  { id: "r-516", kind: "run", name: "Walk-forward: London fade v3", word: "running", tone: "run", line: "Fold 7 of 12", where: SERVER, when: "Now" },
  { id: "r-topup", kind: "run", name: "Data top-up · 09:00", word: "running", tone: "run", line: "EURUSD, XAUUSD, NAS100", where: PC, when: "Now" },
  { id: "r-helper1", kind: "run", name: "Researcher · reading 14 backtest results", word: "running", tone: "run", line: "Helper in Regime study", where: SERVER, when: "Now" },
  { id: "r-helper2", kind: "run", name: "Data analyst · rebuilding EURUSD H1 bars", word: "waiting", tone: "needs", line: "Waits for your approval", where: PC, when: "Now" },
  { id: "r-515", kind: "run", name: "Robustness: Gold breakout XAGUSD", word: "queued", tone: "idle", line: "After the sweep", where: SERVER, when: "Next" },
  { id: "r-nightly", kind: "run", name: "Nightly evidence · 02:00", word: "failed", tone: "down", line: "Step 4 of 5", where: SERVER, when: "02:00" },
  { id: "r-brief", kind: "run", name: "Morning brief · 07:00", word: "passed", tone: "up", line: "41s", where: PC, when: "07:00" },
  { id: "r-514", kind: "run", name: "Backtest: Oil mean revert H4", word: "done", tone: "up", line: "-2.3%", where: PC, when: "Mon" },

  { id: "n-home", kind: "node", name: "Home node", word: "trading", tone: "up", line: "cTrader demo · 3 units", where: PC, when: "Up 4 days",
    sections: [{ id: "units", title: "Units here", icon: "candlestick", wide: true, body: { t: "links", ids: ["u-london", "u-btc", "u-index"] } }, { id: "health", title: "Health", icon: "activity", body: { t: "facts", facts: [["Heartbeat", "4s ago"], ["Sign-in", "Expires in 2 days"], ["Version", "0.9.0"]] } }] },
  { id: "n-fra", kind: "node", name: "Frankfurt node", word: "trading", tone: "up", line: "cTrader live · 1 unit", where: SERVER, when: "Up 11 days",
    sections: [{ id: "units", title: "Units here", icon: "candlestick", wide: true, body: { t: "links", ids: ["u-gold"] } }, { id: "health", title: "Health", icon: "activity", body: { t: "facts", facts: [["Heartbeat", "2s ago"], ["Sign-in", "OK"], ["Version", "0.9.0"]] } }] },
];

const demo: Obj[] = [gold, ...others];

// ------------------------------------------------------------- worst and first
const longUnit = "Gold London-open breakout with volatility filter and news guard v14-final";
const longHost = "trading-node-frankfurt-02.contabo-vps.internal";
const longSession = "Compare the regime study v3 against v1 on every market we have data for since 2015 and tell me which one to promote";

function worst(list: Obj[]): Obj[] {
  const swap = (s?: string) => s?.replaceAll(SERVER, longHost);
  const out: Obj[] = list.map((o) => ({
    ...o,
    name: o.id === "u-gold" ? longUnit : o.id === "s-regime" ? longSession : o.id === "p-gold" ? `Promote ${longUnit} to paper` : o.id === "r-516" ? "Jo" : o.name,
    where: swap(o.where),
    line: swap(o.line),
    sections: o.sections?.map((s) =>
      s.body.t === "facts" ? { ...s, body: { ...s.body, facts: s.body.facts.map(([k, v]) => [k, swap(v)!] as [string, string]) } } : s.body.t === "stats" ? { ...s, body: { ...s.body, stats: s.body.stats.map((x, i) => (i === 0 ? { ...x, value: "-1,284,019.55R", tone: "down" as const } : x)) } } : s,
    ),
  }));
  // A desk that has been running a long time: many units and runs.
  for (let i = 1; i <= 60; i++) {
    out.push({ id: `u-x${i}`, kind: "unit", name: i % 7 === 0 ? `${longUnit} (copy ${i})` : `Unit ${String(i).padStart(3, "0")}`, word: i % 5 ? "tested" : "draft", tone: "idle", line: "From the overnight agent", when: "Sep", markets: [{ sym: ["EURUSD", "GBPUSD", "XAUUSD"][i % 3], life: i % 5 ? "tested" : "draft" }] });
    out.push({ id: `r-x${i}`, kind: "run", name: `Sweep cell ${i} of 212`, word: i % 9 ? "done" : "failed", tone: i % 9 ? "up" : "down", line: "Backtest", where: i % 2 ? PC : longHost, when: "Sun" });
  }
  return out;
}

// A thing with no sections of its own still gets a page worth opening:
// what it is doing, where it runs and since when.
const basics = (o: Obj): Obj =>
  o.sections?.length || o.kind === "proposal" || o.target
    ? o
    : {
        ...o,
        sections: [
          {
            id: "about",
            title: o.kind === "run" ? "This run" : o.kind === "workflow" ? "This workflow" : o.kind === "session" ? "This session" : "About",
            icon: o.kind === "run" ? "loader" : o.kind === "workflow" ? "workflow" : o.kind === "unit" ? "candlestick" : "message-square",
            wide: true,
            body: { t: "facts", facts: [["State", o.word], ["Where", o.where ?? "Not placed"], ["When", o.when ?? "Not set"], ...(o.line ? [["Detail", o.line] as [string, string]] : [])] },
          },
        ],
      };

const demoFull = demo.map(basics);

export function objects(f: Fixture): Obj[] {
  if (f === "first") return [];
  return f === "worst" ? worst(demoFull).map(basics) : demoFull;
}

// ------------------------------------------------------------- lists (kinds)
export type ListKind = "units" | "sessions" | "runs" | "workflows" | "library" | "needs";
export const lists: { id: ListKind; name: string; icon: string; kinds: Kind[]; groups: [string, (o: Obj) => boolean][]; empty: [string, string] }[] = [
  {
    id: "needs",
    name: "Needs you",
    icon: "inbox",
    kinds: ["proposal", "session", "workflow", "unit", "run", "node"],
    groups: [["Decide", (o) => o.kind === "proposal"], ["Approve", (o) => o.kind === "session"], ["Fix", (o) => o.kind !== "proposal" && o.kind !== "session"]],
    empty: ["Nothing waits for you", "Proposals, approvals and failures land here."],
  },
  {
    id: "units",
    name: "Units",
    icon: "candlestick",
    kinds: ["unit"],
    groups: [["Live", (o) => o.word === "live"], ["Paper", (o) => o.word === "paper"], ["Tested", (o) => o.word === "tested"], ["Draft", (o) => o.word === "draft"]],
    empty: ["No units yet", "Ask the copilot for one, in one line."],
  },
  {
    id: "sessions",
    name: "Sessions",
    icon: "message-square",
    kinds: ["session"],
    groups: [["Working", (o) => o.word === "working"], ["Settled", (o) => o.word !== "working"]],
    empty: ["No sessions yet", "Every chat with the copilot is kept here."],
  },
  {
    id: "runs",
    name: "Runs",
    icon: "loader",
    kinds: ["run"],
    groups: [["Waiting on you", (o) => o.tone === "needs"], ["Running", (o) => o.word === "running"], ["Failed", (o) => o.word === "failed"], ["Next", (o) => o.word === "queued"], ["Done", (o) => o.word === "done" || o.word === "passed"]],
    empty: ["Nothing has run yet", "Backtests, workflows and helpers show here, with where they run."],
  },
  {
    id: "workflows",
    name: "Workflows",
    icon: "workflow",
    kinds: ["workflow"],
    groups: [["Failed", (o) => o.word === "failed"], ["Running", (o) => o.word === "running"], ["Enabled", (o) => o.word === "passed" || o.word === "waiting"], ["Drafts", (o) => o.word === "draft"]],
    empty: ["No workflows yet", "55 templates ship with QMX."],
  },
  {
    id: "library",
    name: "Library",
    icon: "library",
    kinds: ["unit", "proposal", "session", "run", "workflow", "node"],
    groups: [["Units", (o) => o.kind === "unit"], ["Proposals", (o) => o.kind === "proposal"], ["Sessions", (o) => o.kind === "session"], ["Workflows", (o) => o.kind === "workflow"], ["Nodes", (o) => o.kind === "node"], ["Runs", (o) => o.kind === "run"]],
    empty: ["Your Library is empty", "Everything you and the copilot make lands here."],
  },
];

export const kindName: Record<Kind, string> = { unit: "Unit", proposal: "Proposal", session: "Session", run: "Run", workflow: "Workflow", node: "Trading node", app: "Mini app" };

// ------------------------------------------------- what a mini app contributes
// The unit of extension is the object: a section on a kind's page, an action
// on a kind, or a card for one of the two boards.
export type GuestSection = Section & { guest: string; kind: Kind };
export const guestSections: GuestSection[] = [
  {
    id: "g-regime",
    guest: "mis",
    kind: "unit",
    title: "Regime now",
    icon: "radar",
    body: { t: "stats", stats: [{ label: "XAUUSD", value: "Trending" }, { label: "Variance ratio", value: "1.18" }, { label: "Hurst", value: "0.58" }, { label: "Fresh", value: "2m ago" }] },
  },
  {
    id: "g-venue",
    guest: "exch",
    kind: "node",
    title: "Venue health",
    icon: "signal",
    body: { t: "rows", rows: [{ label: "cTrader", meta: "OK", state: "up" }, { label: "Dukascopy feed", meta: "Slow", state: "paper" }] },
  },
];
export const guestActions: { id: string; guest: string; kind: Kind; label: string; done: string }[] = [
  { id: "ga-regime", guest: "mis", kind: "unit", label: "Check the regime now", done: "Regime checked: trending, fresh" },
];

export const lifeOrder: Life[] = ["draft", "tested", "paper", "live"];

export const series = { morning: curve(7, 48, 0.6), a: curve(21, 48, 1), b: curve(4, 48, 0.4) };
