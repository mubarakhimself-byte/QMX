import { expect, test } from "@playwright/test";

test("Home empty is one action and is not Copilot", async ({ page }) => {
  await page.goto("/home");
  await expect(page.getByTestId("destination-home")).toBeVisible();
  await expect(page.getByTestId("destination-home")).toHaveAttribute(
    "data-profile",
    "authoring",
  );
  await expect(page.getByTestId("destination-home")).toHaveAttribute(
    "data-is-copilot",
    "false",
  );
  await expect(page.getByTestId("home-empty")).toBeVisible();
  await expect(page.getByTestId("home-empty-action")).toContainText(
    "One action to start Copilot or Authoring",
  );
  await expect(page.getByTestId("home-start-copilot")).toBeVisible();
  await expect(page.getByTestId("destination-copilot")).toHaveCount(0);
  await expect(page.getByTestId("home-inspect-honesty")).toContainText(
    "absent",
  );
});

test("Home chat sends without an instance and invoke needs exactly one instance_id", async ({
  page,
}) => {
  await page.goto("/home");
  await page.getByTestId("home-submit-chat").click();
  await expect(page.getByTestId("home-chat-no-instance")).toBeVisible();
  await expect(page.getByTestId("home-last-issuer")).toHaveText("dispatchChat");
  await expect(page.getByTestId("home-chat")).toHaveAttribute(
    "data-mints-instance",
    "false",
  );

  await page.getByTestId("home-submit-invoke").click();
  await expect(page.getByTestId("home-invoke-refusal")).toContainText(
    "INVALID_INPUT",
  );

  await page.getByTestId("fixture-selected-refs-many").click();
  await page.getByTestId("home-submit-invoke").click();
  await expect(page.getByTestId("home-invoke-refusal")).toContainText(
    "INVALID_INPUT",
  );
});

test("Home chrome states stay distinct and observation is not cancel authority", async ({
  page,
}) => {
  await page.goto("/home?fixture=loading");
  await expect(page.getByTestId("home-attention-skeleton")).toBeVisible();
  await expect(page.getByTestId("home-attention-list")).toHaveAttribute(
    "data-state",
    "loading",
  );

  await page.goto("/home?fixture=reconnecting");
  await expect(page.getByTestId("home-reconnecting-badge")).toBeVisible();
  await expect(page.getByTestId("home-failed")).toHaveCount(0);
  await page.getByTestId("home-run-reconnect").click();
  await expect(page.getByTestId("home-mailbox-incompatibility")).toContainText(
    "query_unavailable",
  );
  await expect(page.getByTestId("home-attention-list")).toHaveAttribute(
    "data-state",
    "reconnecting",
  );

  await page.goto("/home?fixture=unknown");
  await expect(page.getByTestId("home-unknown-badge")).toHaveAttribute(
    "data-painted-as-failed",
    "false",
  );
  await expect(page.getByTestId("home-failed")).toHaveCount(0);

  await page.goto("/home?fixture=populated");
  await expect(page.getByTestId("home-observation")).toHaveAttribute(
    "data-fourth-product",
    "false",
  );
  await expect(page.getByTestId("home-observation")).toHaveAttribute(
    "data-cancel-authority",
    "false",
  );
  await expect(page.getByTestId("home-job-row").first()).toBeVisible();
  await page.getByTestId("home-resume").first().click();
  await expect(page.getByTestId("home-last-resume")).toBeVisible();
});
