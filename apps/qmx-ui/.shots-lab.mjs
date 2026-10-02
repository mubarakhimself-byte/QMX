// Temporary drive of the Lab; deleted after use.
import { chromium } from "@playwright/test";

const OUT = "C:/Users/Mubarak/Desktop/QMX/workroom/ui-review-2026-10-01/v12";
const BASE = "http://localhost:4173";
const width = Number(process.argv[2] ?? 1920);
const height = width >= 2560 ? 1440 : width >= 1920 ? 1080 : 800;
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width, height } });
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
page.on("console", (m) => m.type() === "error" && errors.push(m.text()));

await page.goto(`${BASE}/lab`);
await page.waitForTimeout(800);
for (const name of ["Build", "Test", "Train", "Compare"]) {
  await page.getByRole("navigation", { name: "Layouts" }).getByRole("button", { name, exact: true }).click();
  await page.waitForTimeout(500);
  await page.screenshot({ path: `${OUT}/lab-${name.toLowerCase()}-${width}.png` });
}
const result = { errors };
if (width === 1920) {
  // Journey: Test layout, minimise the sweep grid, check the runs tile grew.
  await page.getByRole("navigation", { name: "Layouts" }).getByRole("button", { name: "Test", exact: true }).click();
  const runs = page.getByRole("region", { name: "Runs" });
  const before = (await runs.boundingBox())?.height ?? 0;
  await page.getByRole("button", { name: "Minimise Sweep grid" }).click();
  await page.waitForTimeout(300);
  const after = (await runs.boundingBox())?.height ?? 0;
  result.minimise = { before: Math.round(before), after: Math.round(after) };
  await page.screenshot({ path: `${OUT}/lab-test-minimised.png` });
  await page.getByRole("button", { name: "Restore Sweep grid" }).click();
  // Click a cell in the grid: the equity tile follows.
  await page.getByRole("button", { name: /GBPUSD H1/ }).click();
  await page.waitForTimeout(200);
  result.equityFollows = await page.getByRole("region", { name: "Equity" }).getByText("GBPUSD H1").count();
  // Redirect from the old Backtest lab URL.
  await page.goto(`${BASE}/apps/demo-lab`);
  await page.waitForURL(/\/lab\?layout=test/, { timeout: 5000 }).catch(() => {});
  result.redirect = page.url();
}
console.log(JSON.stringify(result));
await browser.close();
