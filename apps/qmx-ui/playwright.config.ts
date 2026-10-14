import { defineConfig } from "@playwright/test";

// QMX_UI_URL points the suite at an already running preview on another port.
const url = process.env.QMX_UI_URL ?? "http://127.0.0.1:4173";

export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  use: { baseURL: url },
  webServer: {
    command: "pnpm run build && pnpm run preview",
    url,
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
});
