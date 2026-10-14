// Day one v2: collapsed boards with demo off (Home, both Lab benches,
// Portfolio, an app made from widgets, Settings Copilots), plus Home with
// demo on. Usage: node scripts/day-one-boards-shots.mjs <baseUrl> <outDir>
import { chromium } from "@playwright/test";
import { mkdirSync } from "node:fs";
import { join } from "node:path";

const [base = "http://127.0.0.1:4175", out = "day-one-boards"] =
  process.argv.slice(2);
mkdirSync(out, { recursive: true });

export const MY_APP = {
  id: "my-desk",
  name: "My desk",
  summary: "Made from 3 widgets you picked.",
  icon: "layout-grid",
  group: "helpers",
  kind: "screens",
  risk: "show",
  stage: 0,
  stageNote: "Draft ready to open.",
  evidence: [],
  health: "idle",
  builtBy: "you, from widgets",
  runsOn: "This laptop",
  budget: "Light; runs when open",
  budgetUsed: 0,
  network: "Whatever its widgets already use",
  breaker: "Inherits each widget's own limits",
  provides: ["Its own screen, opened from Apps"],
  ops: [],
  log: ["Created from widgets"],
  panels: ["accounts", "markets", "events"],
  on: true,
};

const shots = [
  ["home", "/home"],
  ["lab-strategies", "/lab?layout=build"],
  ["lab-pods", "/lab?layout=pod-design"],
  ["portfolio", "/portfolio"],
  ["app-my-desk", "/apps/my-desk"],
  ["settings-copilots", "/settings?tab=copilots"],
];

const browser = await chromium.launch();
const problems = [];
for (const [w, h] of [
  [1600, 900],
  [1280, 800],
]) {
  const ctx = await browser.newContext({ viewport: { width: w, height: h } });
  await ctx.addInitScript((app) => {
    if (!localStorage.getItem("qmx.apps.v1"))
      localStorage.setItem("qmx.apps.v1", JSON.stringify([app]));
  }, MY_APP);
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
  current = "home-demo-on";
  await page.goto(`${base}/home?demo=on`);
  await page.waitForTimeout(600);
  await page.screenshot({ path: join(out, `home-demo-on-${w}x${h}.png`) });
  await page.goto(`${base}/home?demo=off`);
  await page.waitForTimeout(500);
  for (const [name, path] of shots) {
    current = name;
    await page.goto(`${base}${path}`);
    await page.waitForTimeout(500);
    const text = await page.locator("body").innerText();
    if (/\bNaN\b|undefined|Infinity/.test(text))
      problems.push(`${name}: NaN/undefined in text`);
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth > window.innerWidth,
    );
    if (overflow) problems.push(`${name} ${w}: page scrolls sideways`);
    await page.screenshot({ path: join(out, `${name}-${w}x${h}.png`) });
  }
  await ctx.close();
}
await browser.close();
console.log(
  problems.length ? problems.join("\n") : "no console errors, no NaN",
);
