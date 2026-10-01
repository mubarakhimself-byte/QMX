import { expect, test } from "@playwright/test";

test("widget emits request_invoke and cannot call the wire client", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.getByTestId("factory-test-issuers")).toBeVisible();
  await expect(page.getByTestId("factory-test-widget")).toHaveAttribute(
    "data-wire-client",
    "forbidden",
  );
  await page.getByTestId("widget-request-invoke").click();
  await expect(page.getByTestId("host-last-caller")).toHaveText(
    "request_invoke",
  );
  await expect(page.getByTestId("widget-wire-import")).toHaveText("forbidden");
  await expect(page.getByTestId("typed-incompatibility")).toContainText(
    "caller_kind_unsupported",
  );
});

test("missing-capability fixture paints typed incompatibility while the rail stays usable", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByTestId("fixture-missing-capability").click();
  await expect(page.getByTestId("typed-incompatibility")).toContainText(
    "typed incompatibility",
  );
  await expect(page.getByTestId("typed-incompatibility")).toContainText(
    "caller_kind_unsupported",
  );
  await expect(page.getByTestId("chat-still-proceeds")).toContainText(
    "send_message proceeded",
  );
  await expect(page.getByTestId("host-shell-usable")).toHaveText("true");
  await page.getByTestId("rail-home").click();
  await expect(page.getByTestId("destination-home")).toBeVisible();
  await expect(page.getByTestId("typed-incompatibility")).toBeVisible();
  await expect(page.getByTestId("rail-product-destinations")).toHaveAttribute(
    "data-count",
    "4",
  );
});

test("cancel_display is not dispatchCancel and Home chat does not need instance", async ({
  page,
}) => {
  await page.goto("/home");
  await page.getByTestId("composer-submit-chat").click();
  await expect(page.getByTestId("host-last-issuer")).toHaveText("dispatchChat");
  await expect(page.getByTestId("chat-still-proceeds")).toBeVisible();
  await page.getByTestId("conversation-cancel-display").click();
  await expect(page.getByTestId("host-last-caller")).toHaveText(
    "cancel_display",
  );
  await page.getByTestId("run-inspector-cancel").click();
  await expect(page.getByTestId("typed-incompatibility")).toContainText(
    "cancel_job",
  );
});
