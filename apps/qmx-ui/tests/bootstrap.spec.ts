import { expect, test } from "@playwright/test";

test("static shell loads from a non-8765 origin with setup copy", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.getByTestId("bootstrap-shell")).toBeVisible();
  await expect(page.getByTestId("spa-origin")).toContainText(
    "http://127.0.0.1:4173",
  );
  await expect(page.getByTestId("spa-origin")).not.toContainText("8765");
  await expect(page.getByTestId("daemon-port-forbidden")).toContainText("8765");
  await expect(page.getByTestId("bootstrap-copy")).toContainText(
    "does not spawn Python",
  );
  await expect(page.getByTestId("inspect-honesty")).toContainText("absent");
  await expect(page.getByTestId("pairing-record")).toContainText(
    "never Authorization",
  );
});

test("Start local is setup copy, not a spawn", async ({ page }) => {
  await page.goto("/");
  await page.getByTestId("start-local").click();
  await expect(page.getByTestId("start-local-result")).toContainText(
    "setup copy",
  );
  await expect(page.getByTestId("start-local-result")).toContainText(
    "does not spawn Python",
  );
  expect(page.url()).not.toContain("8765");
});

test("FACTORY-TEST fixtures paint readable states", async ({ page }) => {
  await page.goto("/");
  await page.getByTestId("fixture-loading").click();
  await expect(page.getByTestId("bootstrap-skeleton")).toBeVisible();
  await page.getByTestId("fixture-error").click();
  await expect(page.getByTestId("bootstrap-copy")).toContainText(
    "Origin-only issuance refused",
  );
  await page.getByTestId("fixture-reconnecting").click();
  await expect(page.getByTestId("reconnecting-badge")).toHaveText(
    "reconnecting",
  );
  await page.getByTestId("fixture-denied").click();
  await expect(page.getByTestId("denied-badge")).toHaveText("denied");
});

test("FACTORY-TEST storyboard keeps copilot and application interiors distinct", async ({
  page,
}) => {
  await page.goto("/factory-test");
  await expect(page.getByTestId("factory-test-label")).toHaveText(
    "FACTORY-TEST",
  );
  await expect(page.getByTestId("main-copilot")).toBeVisible();
  await expect(page.getByTestId("application-interior")).toBeVisible();
  await expect(page.getByTestId("app-copilot")).toHaveCount(0);
  await page.getByTestId("toggle-app-copilot").click();
  await expect(page.getByTestId("app-copilot")).toBeVisible();
  await expect(page.getByTestId("main-copilot-history")).not.toHaveText(
    /app-copilot: inspect board/,
  );
  await page.getByTestId("widget-expand").click();
  await expect(page.getByTestId("widget-viewport")).toContainText("zoom=1");
  await page.getByTestId("widget-return").click();
  await expect(page.getByTestId("widget-viewport")).toContainText("zoom=0.85");
});
