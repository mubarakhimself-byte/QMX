import { reticle } from "@reticlehq/vite-plugin";
import { sveltekit } from "@sveltejs/kit/vite";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vitest/config";
import type { Connect, Plugin } from "vite";
import { readFile } from "node:fs";
import { join } from "node:path";

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

/**
 * DEMO ONLY: serve full MQL5 article markdown from the operator's local
 * catalog so the Library reader can be reviewed before the daemon's Library
 * exists. Off unless QMX_DEMO_MQL5_DIR is set; numeric ids only; never
 * bundled into the build.
 */
function demoLocalLibrary(): Plugin {
  const dir = process.env.QMX_DEMO_MQL5_DIR;
  const handler: Connect.NextHandleFunction = (req, res, next) => {
    const m = req.url?.match(/^\/__demo\/mql5\/(\d{1,8})$/);
    if (!m) return next();
    if (!dir) {
      res.statusCode = 404;
      res.end();
      return;
    }
    readFile(join(dir, `${m[1]}.md`), "utf8", (err, text) => {
      if (err) {
        res.statusCode = 404;
        res.end();
        return;
      }
      res.setHeader("content-type", "text/markdown; charset=utf-8");
      res.end(text);
    });
  };
  return {
    name: "qmx-demo-local-library",
    configureServer: (server) => void server.middlewares.use(handler),
    configurePreviewServer: (server) => void server.middlewares.use(handler),
  };
}

export default defineConfig({
  plugins: [
    tailwindcss(),
    reticle({ inject: true, projectId: "qmx-ui" }),
    sveltekit(),
    demoLocalLibrary(),
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
