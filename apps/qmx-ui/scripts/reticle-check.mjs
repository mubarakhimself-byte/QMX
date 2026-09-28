#!/usr/bin/env node
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

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

console.log(
  "reticle: wiring present (vite plugin + hooks.client.ts). User-facing promotion still requires MCP reticle_act_and_wait or reticle_assert with verified yes from a non-8765 origin.",
);
process.exit(0);
