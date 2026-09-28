#!/usr/bin/env node
// A process deadline surrounds startup, verification and cleanup.
import { spawnSync } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const requested = Number(process.env.RETICLE_TOTAL_TIMEOUT_MS);
const budget =
  Number.isFinite(requested) && requested >= 100
    ? Math.min(Math.floor(requested), 60000)
    : 60000;
const resultFile = resolve(
  process.env.RETICLE_RESULT_FILE ||
    resolve(root, ".reticle/latest-result.json"),
);
const failure = (reason) => {
  mkdirSync(dirname(resultFile), { recursive: true });
  writeFileSync(
    resultFile,
    JSON.stringify(
      {
        verified: "unknown",
        reason,
        tool: "",
        created_at: new Date().toISOString(),
      },
      null,
      2,
    ) + "\n",
  );
};
// An earlier success is erased before startup can fail.
failure("Reticle run not completed");
const result = spawnSync(
  process.execPath,
  [fileURLToPath(new URL("./reticle-worker.mjs", import.meta.url))],
  {
    cwd: root,
    env: {
      ...process.env,
      RETICLE_RESULT_FILE: resultFile,
      RETICLE_TOTAL_TIMEOUT_MS: String(budget),
    },
    encoding: "utf8",
    timeout: budget + 1500,
    killSignal: "SIGKILL",
    maxBuffer: 2 * 1024 * 1024,
    windowsHide: true,
  },
);
if (result.stdout) process.stdout.write(result.stdout);
if (result.stderr) process.stderr.write(result.stderr);
if (result.error || result.signal || result.status === null) {
  const reason =
    result.error?.code === "ETIMEDOUT"
      ? `Reticle process deadline exceeded (${budget + 1500}ms)`
      : `Reticle worker failed: ${result.error?.code || result.signal || "no exit status"}`;
  failure(reason);
  console.error(reason);
  process.exit(2);
}
process.exit(result.status);
