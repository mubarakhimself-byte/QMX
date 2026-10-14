import { expect, test, type Page } from "@playwright/test";

/** Day one: demo mode off, a fresh install with nothing connected. */
async function fresh(page: Page) {
  const errors: string[] = [];
  page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
  page.on("pageerror", (e) => errors.push(e.message));
  await page.addInitScript(() => localStorage.setItem("qmx.demo", "0"));
  return errors;
}

const ROUTES: [string, string][] = [
  ["/home", "Nothing needs you"],
  ["/copilot", "A new errand"],
  ["/library?shelf=bots", "Nothing on this shelf yet"],
  ["/library?shelf=templates", "Paper starter"],
  ["/lab?layout=build", "Your toolbox is empty"],
  ["/lab?layout=pod-design", "No pods yet"],
  ["/portfolio", "No accounts yet"],
  ["/apps", "No apps yet"],
  ["/settings?tab=brokers", "No broker connected"],
  ["/settings?tab=tools", "None signed in"],
  ["/settings?tab=servers", "No sources yet"],
];

for (const [path, line] of ROUTES)
  test(`demo off: ${path} shows its day-one state`, async ({ page }) => {
    const errors = await fresh(page);
    await page.goto(path);
    await expect(page.getByText(line).first()).toBeVisible();
    const text = await page.locator("body").innerText();
    expect(text).not.toMatch(/\bNaN\b|undefined/);
    await expect(page.getByRole("button", { name: /Demo data/ })).toHaveCount(
      0,
    );
    expect(errors).toEqual([]);
  });

test("demo off: sample data is gone", async ({ page }) => {
  await fresh(page);
  await page.goto("/copilot");
  await expect(page.getByText("Weekend-safe pod")).toHaveCount(0);
  await page.goto("/home");
  await expect(page.getByText("BTC & ETH core")).toHaveCount(0);
});

test("get started steps land on the right screen and tick off", async ({
  page,
}) => {
  await fresh(page);
  const steps: [string, RegExp, string][] = [
    ["Connect a broker", /\/settings\?tab=brokers/, "Brokers and accounts"],
    ["Pick a model provider", /\/settings\?tab=tools/, "Models and tools"],
    ["Add a data source", /\/library\?shelf=sources/, "Add a source"],
    ["Start a strategy or pod", /\/library\?shelf=templates/, "Templates"],
  ];
  for (const [i, [label, url, landed]] of steps.entries()) {
    await page.goto("/home");
    const band = page.getByRole("region", { name: "Get started" });
    await expect(band.getByText(`${i} of 4`)).toBeVisible();
    await band.getByRole("button", { name: label }).click();
    await expect(page).toHaveURL(url);
    await expect(page.getByText(landed).first()).toBeVisible();
  }
  await page.goto("/home");
  await expect(page.getByRole("region", { name: "Get started" })).toHaveCount(
    0,
  );
});

test("empty-state actions land on the right screen", async ({ page }) => {
  await fresh(page);
  const cases: [string, string, RegExp][] = [
    ["/home", "Connect a broker", /\/settings\?tab=brokers/],
    ["/home", "Add a source", /\/library\?shelf=sources/],
    ["/home", "New pod", /\/copilot\?ask=/],
    [
      "/lab?layout=build",
      "Start from a template",
      /\/library\?shelf=templates/,
    ],
    ["/portfolio", "Connect a broker", /\/settings\?tab=brokers/],
    ["/apps", "Start from a template", /\/apps\?view=discover/],
    ["/library?shelf=bots", "Start from a template", /shelf=templates/],
  ];
  for (const [from, action, to] of cases) {
    await page.goto(from);
    await page.getByRole("link", { name: action }).first().click();
    await expect(page, `${from} → ${action}`).toHaveURL(to);
  }
  await expect(page.getByText("Paper starter").first()).toBeVisible();
});

test("switching demo on and off needs no reload", async ({ page }) => {
  const errors = await fresh(page);
  await page.goto("/settings?tab=developer");
  const toggle = page.getByRole("switch", { name: "Show demo content" });
  await expect(toggle).toHaveAttribute("aria-checked", "false");
  await toggle.click();
  await page.getByRole("link", { name: "Home" }).first().click();
  await expect(page.getByText("BTC & ETH core").first()).toBeVisible();
  await page.getByRole("button", { name: /Demo data/ }).click();
  await page.getByRole("link", { name: "Turn demo off" }).click();
  await page.getByRole("switch", { name: "Show demo content" }).click();
  await page.getByRole("link", { name: "Home" }).first().click();
  await expect(page.getByText("Nothing needs you")).toBeVisible();
  await expect(page.getByText("BTC & ETH core")).toHaveCount(0);
  expect(errors).toEqual([]);
});
