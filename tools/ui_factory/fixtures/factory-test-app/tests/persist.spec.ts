import { expect, test } from "@playwright/test";

test("save persists after reload", async ({ page }) => {
  await page.goto("/");
  await page.getByTestId("note").fill("hello");
  await page.getByTestId("save").click();
  await expect(page.getByTestId("saved")).toHaveText("hello");
  await page.reload();
  await expect(page.getByTestId("saved")).toHaveText("hello");
});

test("dead control does not persist", async ({ page }) => {
  await page.goto("/");
  await page.getByTestId("note").fill("nope");
  await page.getByTestId("dead").click();
  await page.reload();
  await expect(page.getByTestId("saved")).toHaveText("");
});
