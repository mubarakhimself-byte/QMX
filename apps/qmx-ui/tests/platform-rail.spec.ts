import { expect, test } from "@playwright/test";

test("PlatformRail shows four product destinations above the divider", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.getByTestId("platform-rail")).toBeVisible();
  const products = page.getByTestId("rail-product-destinations");
  await expect(products).toHaveAttribute("data-count", "4");
  await expect(products.getByTestId("rail-home")).toBeVisible();
  await expect(products.getByTestId("rail-copilot")).toBeVisible();
  await expect(products.getByTestId("rail-library")).toBeVisible();
  await expect(products.getByTestId("rail-authoring")).toBeVisible();
  await expect(products.getByTestId("rail-settings")).toHaveCount(0);
  await expect(page.getByTestId("rail-settings")).toBeVisible();
  await expect(page.getByTestId("rail-settings")).toHaveAttribute(
    "data-kind",
    "chrome",
  );
  await expect(page.getByTestId("rail-opened-apps")).toHaveAttribute(
    "data-count",
    "0",
  );
  await expect(page.getByTestId("inspect-honesty")).toContainText("absent");
});

test("Home, Copilot, Library, and Authoring are independently reachable with zero apps", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByTestId("rail-home").click();
  await expect(page.getByTestId("destination-home")).toBeVisible();
  await expect(page.getByTestId("destination-home")).toHaveAttribute(
    "data-profile",
    "authoring",
  );
  await expect(page.getByTestId("home-purpose")).toContainText(
    "Independent of Copilot",
  );

  await page.getByTestId("rail-copilot").click();
  await expect(page.getByTestId("destination-copilot")).toBeVisible();
  await expect(page.getByTestId("copilot-purpose")).toContainText(
    "Independent of Home",
  );
  await expect(page.getByTestId("destination-home")).toHaveCount(0);

  await page.getByTestId("rail-library").click();
  await expect(page.getByTestId("destination-library")).toBeVisible();
  await expect(page.getByTestId("library-kind-knowledge")).toBeVisible();
  await expect(page.getByTestId("library-kind-artifact")).toBeVisible();
  await expect(page.getByTestId("library-kind-contribution")).toBeVisible();

  await page.getByTestId("rail-authoring").click();
  await expect(page.getByTestId("destination-authoring")).toBeVisible();
  await expect(page.getByTestId("authoring-purpose")).toContainText(
    "zero apps",
  );
  await expect(page.getByTestId("authoring-expand-copy")).toContainText(
    "not a fifth rail destination",
  );
  await expect(page.getByTestId("rail-opened-apps")).toHaveAttribute(
    "data-count",
    "0",
  );
});

test("Settings is chrome and keyboard can move among product destinations", async ({
  page,
}) => {
  await page.goto("/settings");
  await expect(page.getByTestId("chrome-settings")).toBeVisible();
  await expect(page.getByTestId("settings-purpose")).toContainText(
    "not a fifth product destination",
  );
  await page.getByTestId("rail-home").focus();
  await page.keyboard.press("ArrowDown");
  await expect(page.getByTestId("rail-copilot")).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.getByTestId("destination-copilot")).toBeVisible();
});

test("FACTORY-TEST close_app is wire.detach and headless packs get no icon", async ({
  page,
}) => {
  await page.goto("/home");
  await page.getByTestId("fixture-opened-visual").click();
  await expect(page.getByTestId("rail-opened-apps")).toHaveAttribute(
    "data-count",
    "1",
  );
  await expect(page.getByTestId("rail-job-badge")).toHaveAttribute(
    "data-cancel-authority",
    "false",
  );
  await page.getByTestId("rail-close-app").click();
  await expect(page.getByTestId("chrome-last-event")).toContainText(
    "close_app",
  );
  await expect(page.getByTestId("chrome-last-event")).toContainText(
    "wire.detach",
  );
  await expect(page.getByTestId("chrome-last-event")).toContainText(
    "cancelledJobHandles=false",
  );
  await expect(page.getByTestId("rail-opened-apps")).toHaveAttribute(
    "data-count",
    "0",
  );

  await page.getByTestId("fixture-opened-headless").click();
  await expect(page.getByTestId("rail-opened-apps")).toHaveAttribute(
    "data-count",
    "0",
  );
  await expect(page.getByTestId("headless-first-class")).toContainText(
    "No navigation pane",
  );
  await expect(page.getByTestId("rail-opened-app")).toHaveCount(0);
  await page.getByTestId("rail-library").click();
  await expect(page.getByTestId("destination-library")).toBeVisible();
  await page.getByTestId("rail-authoring").click();
  await expect(page.getByTestId("destination-authoring")).toBeVisible();
});

test("FACTORY-TEST expand/return is not a fifth product destination", async ({
  page,
}) => {
  await page.goto("/factory-test");
  await expect(page.getByTestId("rail-product-destinations")).toHaveAttribute(
    "data-count",
    "4",
  );
  await page.getByTestId("widget-expand").click();
  await expect(page.getByTestId("rail-product-destinations")).toHaveAttribute(
    "data-count",
    "4",
  );
  await expect(page.getByTestId("widget-viewport")).toContainText("zoom=1");
  await page.getByTestId("widget-return").click();
  await expect(page.getByTestId("widget-viewport")).toContainText("zoom=0.85");
});
