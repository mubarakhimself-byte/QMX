/**
 * Where articles come from. MQL5 is the local demo catalogue; the others
 * show how more sources sit beside it (operator, 2026-10-03: "what if I had
 * articles from other sources"). Fetching is the daemon's job: Obsidian
 * clippings from a folder, arXiv by feed, and web pages through a scraper
 * such as Firecrawl (paid; nothing here calls it).
 */
export type Article = {
  id: number;
  title: string;
  summary: string;
  published: string;
  section: string;
  series: string | null;
  part: number | null;
  url: string;
  /** Which source it came from; MQL5 when absent. */
  source?: string;
};

export const ARTICLE_SOURCES = [
  { id: "mql5", name: "MQL5 articles", note: "Local catalogue" },
  { id: "clips", name: "Your clippings", note: "Obsidian web clipper folder" },
  { id: "arxiv", name: "arXiv · q-fin", note: "Feed, needs the daemon" },
  {
    id: "web",
    name: "Web pages (Firecrawl)",
    note: "Scraped by the daemon; paid service, not connected",
  },
] as const;

/** Sample items from sources other than MQL5 (summaries in our own words). */
export const OTHER_ARTICLES: Article[] = [
  {
    id: -1,
    source: "clips",
    title: "Understanding what language models give back (Karpathy, on X)",
    summary:
      "Ask a model to answer in a strict plain-English style, or better, as a diagram, an interactive web page, or a short explainer video. More of our work becomes checking and understanding what models made.",
    published: "2026-10-02",
    section: "Clipping",
    series: null,
    part: null,
    url: "https://x.com/karpathy/status/2105819303471976479",
  },
];

/** Ways the copilot can explain a paper back to you (from that post). */
export const EXPLAIN_AS = [
  {
    id: "plain",
    label: "Plain words",
    ask: "Explain this article in short, plain sentences (controlled English, like ASD-STE100), then list the claims I could test.",
  },
  {
    id: "diagram",
    label: "Diagram",
    ask: "Draw this article's method as a diagram I can follow step by step.",
  },
  {
    id: "page",
    label: "Interactive page",
    ask: "Turn this article into an interactive page with the key idea I can play with, and save it to the Library.",
  },
  {
    id: "video",
    label: "Explainer video",
    ask: "Make a short 3Blue1Brown-style explainer video of this article using local tools (Manim and a local voice), and save it to the Library.",
  },
] as const;
