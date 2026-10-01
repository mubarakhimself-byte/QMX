import { reticle } from "@reticlehq/vite-plugin";
import { sveltekit } from "@sveltejs/kit/vite";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vitest/config";

const DAEMON_PORT = 8765;
const SPA_DEV_PORT = 5173;
const SPA_PREVIEW_PORT = 4173;

function assertNotDaemonPort(port: number, label: string): void {
  if (port === DAEMON_PORT) {
    throw new Error(`${label} must not bind daemon port ${DAEMON_PORT}`);
  }
}

assertNotDaemonPort(SPA_DEV_PORT, "vite server");
assertNotDaemonPort(SPA_PREVIEW_PORT, "vite preview");

export default defineConfig({
  plugins: [
    tailwindcss(),
    reticle({ inject: true, projectId: "qmx-ui" }),
    sveltekit(),
  ],
  server: {
    host: "127.0.0.1",
    port: SPA_DEV_PORT,
    strictPort: true,
  },
  preview: {
    host: "127.0.0.1",
    port: SPA_PREVIEW_PORT,
    strictPort: true,
  },
  test: {
    include: ["src/**/*.test.ts"],
  },
});
