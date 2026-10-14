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
  ["/home", "Four steps to your first test on paper"],
  ["/copilot", "A new errand"],
  ["/library?shelf=bots", "Nothing on this shelf yet"],
  ["/library?shelf=templates", "Paper starter"],
  ["/lab?layout=build", "Build and test a strategy"],
  ["/lab?layout=pod-design", "Build a pod"],
  ["/portfolio", "Connect a broker to see accounts and trades"],
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
  await expect(page.getByText("Nothing needs you")).toBeVisible();
});

test("empty-state actions land on the right screen", async ({ page }) => {
  await fresh(page);
  const cases: [string, string, RegExp][] = [
    ["/home", "Connect a broker", /\/settings\?tab=brokers/],
    ["/lab?layout=pod-design", "New pod", /\/copilot\?ask=/],
    ["/lab?layout=build", "Ask the copilot", /\/copilot$/],
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
  await expect(page.getByRole("region", { name: "Get started" })).toBeVisible();
  await expect(page.getByText("BTC & ETH core")).toHaveCount(0);
  expect(errors).toEqual([]);
});

const tiles = (page: Page) => page.locator("section.tile");

test("empty boards collapse to one welcome per screen", async ({ page }) => {
  const errors = await fresh(page);
  const boards: [string, string][] = [
    ["/home", "Get started"],
    ["/lab?layout=build", "Build and test a strategy"],
    ["/lab?layout=pod-design", "Build a pod"],
    ["/portfolio", "Your portfolio"],
  ];
  for (const [path, welcome] of boards) {
    await page.goto(path);
    await expect(page.getByRole("region", { name: welcome })).toBeVisible();
    await expect(tiles(page), path).toHaveCount(0);
  }
  expect(errors).toEqual([]);
});

test("demo on keeps the full board", async ({ page }) => {
  await page.goto("/home?demo=on");
  await expect(page.getByText("BTC & ETH core").first()).toBeVisible();
  await expect(page.locator("[data-board-welcome]")).toHaveCount(0);
  await expect(tiles(page)).toHaveCount(6);
});

test("edit layout and + Panel show the empty tiles again", async ({ page }) => {
  await fresh(page);
  await page.goto("/lab?layout=build");
  await expect(tiles(page)).toHaveCount(0);
  await page.getByRole("button", { name: "Edit layout" }).click();
  await expect(tiles(page).first()).toBeVisible();
  await expect(page.getByText("Your toolbox is empty").first()).toBeVisible();
  await page.getByRole("button", { name: "Done" }).click();
  await expect(tiles(page)).toHaveCount(0);

  await page.goto("/home");
  await page.getByRole("button", { name: "Hide these steps" }).click();
  const before = await tiles(page).count();
  await page.getByTitle("Add a panel").click();
  await page
    .getByRole("menuitem", { name: /Markets/ })
    .first()
    .click();
  await expect(tiles(page)).toHaveCount(before + 1);
});

test("a template card opens it in the Library", async ({ page }) => {
  await fresh(page);
  await page.goto("/lab?layout=pod-design");
  await page.getByRole("button", { name: /Paper starter/ }).click();
  await expect(page).toHaveURL(/\/library\?item=tpl-pod-/);
  await expect(
    page.getByRole("link", { name: "Use this template" }),
  ).toBeVisible();
});

test("an app made from widgets collapses too", async ({ page }) => {
  await fresh(page);
  await page.addInitScript(() =>
    localStorage.setItem(
      "qmx.apps.v1",
      JSON.stringify([
        {
          id: "my-desk",
          name: "My desk",
          summary: "Made from 2 widgets you picked.",
          icon: "layout-grid",
          group: "helpers",
          kind: "screens",
          risk: "show",
          stage: 0,
          stageNote: "Draft",
          evidence: [],
          health: "idle",
          builtBy: "you, from widgets",
          runsOn: "This laptop",
          budget: "Light",
          budgetUsed: 0,
          network: "None",
          breaker: "None",
          provides: [],
          ops: [],
          log: [],
          panels: ["accounts", "markets"],
          on: true,
        },
      ]),
    ),
  );
  await page.goto("/apps/my-desk");
  await expect(
    page.getByRole("region", { name: "Nothing to show yet" }),
  ).toBeVisible();
  await expect(tiles(page)).toHaveCount(0);
});

test("day-one leftovers: laptop, copilot model, starters", async ({ page }) => {
  await fresh(page);
  await page.goto("/settings?tab=servers");
  await expect(page.getByText("Dell Precision")).toHaveCount(0);
  await expect(page.getByText("Quadro")).toHaveCount(0);
  await page.goto("/settings?tab=copilots");
  await expect(page.getByText("No model yet").first()).toBeVisible();
  await page.getByRole("link", { name: "Pick a provider" }).click();
  await expect(page).toHaveURL(/tab=tools/);
  await expect(page.getByText("None signed in").first()).toBeVisible();
  await page.goto("/lab?layout=build");
  await page.getByRole("button", { name: "Toggle Lab copilot" }).click();
  await expect(
    page.getByRole("button", { name: "Explain how pods work" }),
  ).toBeVisible();
  await expect(page.getByText(/USOIL M15/)).toHaveCount(0);
});
