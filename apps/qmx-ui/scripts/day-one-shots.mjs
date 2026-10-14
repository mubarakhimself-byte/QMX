// Screenshots every main screen and tab with demo mode off (day one), plus
// Home with demo on. Usage: node scripts/day-one-shots.mjs <baseUrl> <outDir>
import { chromium } from "@playwright/test";
import { mkdirSync } from "node:fs";
import { join } from "node:path";

const [base = "http://127.0.0.1:4175", out = "day-one-shots"] =
  process.argv.slice(2);
mkdirSync(out, { recursive: true });

const SIZES = [
  [1600, 900],
  [1280, 800],
];
const SHELVES = [
  "everything",
  "bots",
  "models",
  "pods",
  "blocks",
  "workflows",
  "apps",
  "templates",
  "reports",
  "paper",
  "scenarios",
  "setups",
  "datasets",
  "files",
  "articles",
  "sources",
];
const SETTINGS = [
  "general",
  "appearance",
  "brokers",
  "tools",
  "servers",
  "copilots",
  "apps",
  "safety",
  "developer",
];

/** Each shot: a name, a path, and an optional step run after load. */
const tabs = (nav) => async (page, i) =>
  page.locator(`nav[aria-label="${nav}"] > button`).nth(i).click();

const shots = [
  ...[0, 1, 2].map((i) => ({
    name: `home-${i}`,
    path: "/home",
    step: (p) => tabs("Tabs")(p, i),
  })),
  { name: "copilot", path: "/copilot" },
  ...SHELVES.map((s) => ({
    name: `library-${s}`,
    path: `/library?shelf=${s}`,
  })),
  ...[
    "build",
    "test",
    "train",
    "compare",
    "pod-design",
    "pod-test",
    "pod-paper",
  ].map((l) => ({
    name: `lab-${l}`,
    path: `/lab?layout=${l}`,
  })),
  ...[0, 1, 2, 3, 4, 5].map((i) => ({
    name: `portfolio-${i}`,
    path: "/portfolio",
    step: (p) => tabs("Layouts")(p, i),
  })),
  { name: "apps-mine", path: "/apps" },
  { name: "apps-discover", path: "/apps?view=discover" },
  ...SETTINGS.map((t) => ({
    name: `settings-${t}`,
    path: `/settings?tab=${t}`,
  })),
];

const browser = await chromium.launch();
const problems = [];
for (const [w, h] of SIZES) {
  const ctx = await browser.newContext({ viewport: { width: w, height: h } });
  const page = await ctx.newPage();
  let current = "";
  page.on(
    "console",
    (m) =>
      m.type() === "error" && problems.push(`${current} console: ${m.text()}`),
  );
  page.on("pageerror", (e) =>
    problems.push(`${current} pageerror: ${e.message}`),
  );
  await page.goto(`${base}/home?demo=on`);
  await page.waitForTimeout(600);
  await page.screenshot({ path: join(out, `home-demo-on-${w}x${h}.png`) });
  await page.goto(`${base}/home?demo=off`);
  await page.waitForTimeout(300);
  for (const s of shots) {
    current = s.name;
    await page.goto(`${base}${s.path}`);
    await page.waitForTimeout(400);
    if (s.step) {
      const ok = await s.step(page).then(
        () => true,
        () => false,
      );
      if (!ok) continue;
      await page.waitForTimeout(300);
    }
    const text = await page.locator("body").innerText();
    if (/\bNaN\b|undefined|Infinity/.test(text))
      problems.push(`${s.name}: NaN/undefined in text`);
    await page.screenshot({ path: join(out, `${s.name}-${w}x${h}.png`) });
  }
  await ctx.close();
}
await browser.close();
console.log(
  problems.length ? problems.join("\n") : "no console errors, no NaN",
);
