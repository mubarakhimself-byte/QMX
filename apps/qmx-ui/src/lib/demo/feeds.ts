/**
 * DEMO FEEDS ONLY. Source definitions are real places; feed items are
 * labelled samples, not real papers or headlines. The daemon fetches and
 * stores feeds (RSS, APIs) once that scope is ruled; the browser never does.
 */

export type Source = {
  id: string;
  name: string;
  kind: "Papers" | "Articles" | "News" | "Calendar";
  /** Opening it as a web app gives the site its own window (Omarchy-style). */
  url: string;
  how: string;
  status: "ruled" | "proposed";
};

export const SOURCES: Source[] = [
  {
    id: "arxiv",
    name: "arXiv · q-fin",
    kind: "Papers",
    url: "https://arxiv.org/list/q-fin/new",
    how: "RSS of new quantitative finance papers",
    status: "proposed",
  },
  {
    id: "alphaxiv",
    name: "alphaXiv",
    kind: "Papers",
    url: "https://www.alphaxiv.org",
    how: "Discussion and summaries on arXiv papers",
    status: "proposed",
  },
  {
    id: "ssrn",
    name: "SSRN · Financial Economics",
    kind: "Papers",
    url: "https://www.ssrn.com",
    how: "Working papers by topic",
    status: "proposed",
  },
  {
    id: "mql5",
    name: "MQL5 articles",
    kind: "Articles",
    url: "https://www.mql5.com/en/articles",
    how: "Local catalog, 3,057 articles",
    status: "proposed",
  },
  {
    id: "ff",
    name: "Forex Factory calendar",
    kind: "Calendar",
    url: "https://www.forexfactory.com/calendar",
    how: "Free weekly file; opens news windows on the node",
    status: "ruled",
  },
  {
    id: "news",
    name: "Market news",
    kind: "News",
    url: "https://www.forexfactory.com/news",
    how: "Free headline feeds",
    status: "proposed",
  },
];

export type FeedItem = {
  id: string;
  source: string;
  kind: Source["kind"];
  title: string;
  age: string;
  tags: string[];
};

export const FEED: FeedItem[] = [
  {
    id: "f1",
    source: "arXiv · q-fin",
    kind: "Papers",
    title: "Sample paper: regime-switching volatility forecasts for FX",
    age: "2h",
    tags: ["volatility", "regimes"],
  },
  {
    id: "f2",
    source: "alphaXiv",
    kind: "Papers",
    title: "Sample discussion: is momentum crowded in index futures?",
    age: "3h",
    tags: ["momentum"],
  },
  {
    id: "f3",
    source: "SSRN · Financial Economics",
    kind: "Papers",
    title: "Sample working paper: transaction costs and short-horizon reversal",
    age: "5h",
    tags: ["costs", "reversal"],
  },
  {
    id: "f4",
    source: "MQL5 articles",
    kind: "Articles",
    title: "Markov Chain Monte Carlo Sampling Methods: The HMC Algorithm",
    age: "Sep 4",
    tags: ["statistics"],
  },
  {
    id: "f5",
    source: "Forex Factory calendar",
    kind: "Calendar",
    title: "USD · ISM manufacturing PMI · high impact · 16:00",
    age: "in 1h",
    tags: ["USD"],
  },
  {
    id: "f6",
    source: "arXiv · q-fin",
    kind: "Papers",
    title: "Sample paper: purged cross-validation for financial ML",
    age: "1d",
    tags: ["ml", "validation"],
  },
];

export type Headline = {
  time: string;
  source: string;
  title: string;
  symbols: string[];
  impact: "high" | "medium" | "low";
  tone: "positive" | "negative" | "neutral";
};

export const HEADLINES: Headline[] = [
  {
    time: "14:31",
    source: "Sample Wire",
    title: "Sample: US jobless claims come in below forecast",
    symbols: ["USD", "US500"],
    impact: "medium",
    tone: "positive",
  },
  {
    time: "14:12",
    source: "Desk note",
    title: "Sample: euro slips as German inflation cools",
    symbols: ["EURUSD"],
    impact: "high",
    tone: "negative",
  },
  {
    time: "13:58",
    source: "Sample Wire",
    title: "Sample: gold steady near range highs ahead of PMI",
    symbols: ["XAUUSD"],
    impact: "low",
    tone: "neutral",
  },
  {
    time: "13:40",
    source: "Sample Wire",
    title: "Sample: bitcoin climbs past a round number on ETF flows",
    symbols: ["BTCUSD"],
    impact: "medium",
    tone: "positive",
  },
  {
    time: "13:05",
    source: "Desk note",
    title: "Sample: yen weakens after central bank minutes",
    symbols: ["USDJPY"],
    impact: "medium",
    tone: "negative",
  },
  {
    time: "12:44",
    source: "Sample Wire",
    title: "Sample: oil falls on inventory build",
    symbols: ["WTI"],
    impact: "low",
    tone: "negative",
  },
];

/** Where news is consumed in QMX (design, for the backend ruling). */
export const NEWS_CONSUMERS = [
  {
    name: "News widget",
    what: "Any mini app can show headlines filtered to its symbols.",
  },
  {
    name: "Trading node news windows",
    what: "High-impact calendar events block new entries around the release (ruled).",
  },
  {
    name: "Workflow trigger",
    what: "Start a workflow when a headline matches a topic or symbol.",
  },
  {
    name: "Copilot context",
    what: "The copilot can cite headlines and papers with their source and time.",
  },
];
