#!/usr/bin/env node
/**
 * Unattended Reticle gate. Wiring is not a pass.
 *
 * Official CI path (docs.reticle.sh/cli/verify): no model, no MCP.
 *   npx @reticlehq/server verify <url>
 * Replays git-checked .reticle/flows/. Empty flows refuse with exit 1.
 *
 * Uses RETICLE_PORT=4410 so this CLI engine does not fight the agent MCP
 * daemon on 4400. SPA origin is 127.0.0.1:5173 (never daemon 8765).
 */
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const vite = readFileSync(join(root, "vite.config.ts"), "utf8");
const hook = readFileSync(join(root, "src/hooks.client.ts"), "utf8");
const layout = readFileSync(join(root, "src/routes/+layout.ts"), "utf8");

if (!vite.includes("@reticlehq/vite-plugin")) {
  console.error("reticle: vite plugin missing");
  process.exit(1);
}
if (vite.includes("port: 8765") || vite.includes("port:8765")) {
  console.error("reticle: SPA origin must not bind 8765");
  process.exit(1);
}
if (!hook.includes("/@reticle-connect")) {
  console.error("reticle: client hook must load /@reticle-connect in DEV");
  process.exit(1);
}
if (!layout.includes("export const ssr = false")) {
  console.error("reticle: ssr must be false");
  process.exit(1);
}

const flowsDir = join(root, ".reticle", "flows");
if (!existsSync(flowsDir)) {
  console.error(
    "reticle: no .reticle/flows — refusing to pass. Record a flow with reticle_record then reticle_flow_save.",
  );
  process.exit(1);
}
const flows = readdirSync(flowsDir).filter((name) => name.endsWith(".json"));
if (flows.length === 0) {
  console.error(
    "reticle: .reticle/flows is empty — verifying nothing is never a pass",
  );
  process.exit(1);
}

const url = process.env.RETICLE_VERIFY_URL || "http://127.0.0.1:5173/";
const sidecar = process.env.RETICLE_EVIDENCE_FILE || "";
if (sidecar && existsSync(sidecar)) {
  const raw = JSON.parse(readFileSync(sidecar, "utf8"));
  const verdict = String(raw.verdict || raw.verified || "").toLowerCase();
  const tool = String(raw.tool || "");
  if (
    verdict === "yes" &&
    (tool === "reticle_act_and_wait" || tool === "reticle_assert")
  ) {
    console.log(
      `reticle: ${flows.length} passed (MCP ${tool} verified=yes; sidecar ${sidecar})`,
    );
    process.exit(0);
  }
  console.error(
    `reticle: sidecar ${sidecar} is not a pass (verdict=${verdict} tool=${tool})`,
  );
  process.exit(1);
}

const env = { ...process.env };
const result = spawnSync(
  process.platform === "win32" ? "npx.cmd" : "npx",
  ["--yes", "@reticlehq/server", "verify", url, "--timeout", "60000"],
  { cwd: root, env, encoding: "utf8" },
);

const stdout = result.stdout || "";
const stderr = result.stderr || "";
if (stdout) process.stdout.write(stdout);
if (stderr) process.stderr.write(stderr);
const combined = `${stdout}\n${stderr}`;

if (combined.includes("a Reticle daemon is already listening")) {
  console.error(
    "reticle: official `verify` cannot bind while the agent MCP daemon owns port 4400.",
  );
  console.error(
    'reticle: replay saved flows via MCP reticle_verify { action: "flows" } or pass RETICLE_EVIDENCE_FILE with act_and_wait/assert verified=yes.',
  );
  console.error(
    "reticle: CI (no MCP daemon) runs `npx @reticlehq/server verify <url>` unchanged. Reticle is not skipped.",
  );
  process.exit(1);
}

if (result.status !== 0) {
  console.error(
    "reticle: verify failed. Wiring is present; saved flows did not pass on the running app.",
  );
  process.exit(result.status === null ? 1 : result.status);
}

console.log(`reticle: ${flows.length} passed`);
process.exit(0);
