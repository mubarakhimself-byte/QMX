import { execFileSync } from "node:child_process";
import { mkdirSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { ReticleMcp, payload } from "./reticle-mcp.mjs";

const root = process.cwd();
const number = (value, fallback, max) => {
  const n = Number(value);
  return Number.isFinite(n) && n >= 100
    ? Math.min(Math.floor(n), max)
    : fallback;
};
const totalMs = number(process.env.RETICLE_TOTAL_TIMEOUT_MS, 60000, 60000);
const callMs = number(process.env.RETICLE_CALL_TIMEOUT_MS, 15000, 20000);
const assertMs = Math.min(5000, callMs - 50);
const started = Date.now();
const receipt = {
  verified: "unknown",
  tool: "",
  checks: [],
  cleanup: "not-needed",
};
let client;
let sessionId;
let stage = "configuration";
const watchdog = setTimeout(() => {
  receipt.reason = `Reticle total deadline exceeded during ${stage} (${totalMs}ms)`;
  receipt.cleanup = sessionId
    ? "lease release not confirmed; daemon TTL must reclaim"
    : "not-needed";
  finish(2);
}, totalMs);

function finish(code) {
  clearTimeout(watchdog);
  receipt.duration_ms = Date.now() - started;
  receipt.created_at = new Date().toISOString();
  const file = process.env.RETICLE_RESULT_FILE;
  mkdirSync(dirname(file), { recursive: true });
  writeFileSync(file, JSON.stringify(receipt, null, 2) + "\n");
  console.log(`QMX_RETICLE_RESULT ${JSON.stringify(receipt)}`);
  client?.close();
  process.exit(code);
}
function localUrl(raw) {
  const url = new URL(raw);
  if (
    url.protocol !== "http:" ||
    !["localhost", "127.0.0.1", "[::1]"].includes(url.hostname) ||
    url.username ||
    url.password
  )
    throw new Error("Reticle factory URLs must be local HTTP");
  return url;
}
async function get(url) {
  const response = await fetch(url, {
    signal: AbortSignal.timeout(Math.min(callMs, 5000)),
  });
  if (!response.ok) throw new Error(`${stage}: HTTP ${response.status}`);
  const body = await response.text();
  if (body.length > 2 * 1024 * 1024)
    throw new Error(`${stage}: response too large`);
  return body;
}
async function tool(name, args) {
  const result = await client.call("tools/call", { name, arguments: args });
  receipt.checks.push({ tool: name, arguments: args, result });
  return payload(result);
}
function consequence(expect) {
  if (expect?.kind) return expect;
  if (expect?.element)
    return { kind: "element", query: expect.element, state: "visible" };
  throw new Error(
    "Every saved flow step needs an explicit consequence predicate",
  );
}
try {
  const config = JSON.parse(
    readFileSync(resolve(root, ".reticle.json"), "utf8"),
  );
  if (!config.projectId)
    throw new Error(".reticle.json has no stable projectId");
  const pkg = JSON.parse(readFileSync(resolve(root, "package.json"), "utf8"));
  const expectedVersion = pkg.devDependencies["@reticlehq/browser"];
  const daemon = localUrl(
    process.env.RETICLE_DAEMON_URL || `http://127.0.0.1:${config.port || 4400}`,
  );
  const app = localUrl(
    process.env.RETICLE_VERIFY_URL || "http://127.0.0.1:5173/",
  );
  const sha =
    process.env.QMX_CANDIDATE_SHA ||
    execFileSync("git", ["rev-parse", "HEAD"], {
      cwd: root,
      encoding: "utf8",
      timeout: 2000,
      windowsHide: true,
    }).trim();
  if (!/^[0-9a-f]{40}$/.test(sha))
    throw new Error("Full candidate SHA required");
  receipt.candidate_sha = sha;
  receipt.projectId = config.projectId;
  receipt.app_url = app.toString();
  stage = "daemon preflight";
  const status = JSON.parse(await get(new URL("/status", daemon)));
  if (!status.running || status.version !== expectedVersion) {
    throw new Error(
      `Reticle version mismatch: daemon=${status.version}, SDK=${expectedVersion}`,
    );
  }
  receipt.reticle_version = status.version;
  stage = "app preflight";
  const html = await get(app);
  const servedSha =
    /<meta\s+name="qmx-candidate-sha"\s+content="([0-9a-f]{40})"\s*\/?>/.exec(
      html,
    )?.[1];
  if (servedSha !== sha)
    throw new Error("Running app does not serve the candidate SHA");
  const files = readdirSync(resolve(root, ".reticle/flows"))
    .filter((f) => f.endsWith(".json"))
    .sort();
  if (!files.length)
    throw new Error(
      "No committed Reticle flows; verifying nothing cannot pass",
    );
  const flows = files.map((file) =>
    JSON.parse(readFileSync(resolve(root, ".reticle/flows", file), "utf8")),
  );
  if (
    flows.some(
      (f) => f.projectId !== config.projectId || !f.intent || !f.steps?.length,
    )
  ) {
    throw new Error("Saved flow has wrong project identity or no intent/steps");
  }
  stage = "MCP connection";
  client = new ReticleMcp(daemon, callMs);
  await client.connect();
  stage = "lease acquisition";
  const lease = await tool("reticle_run", {
    tool: "reticle_lease",
    args: {
      action: "acquire",
      url: app.toString(),
      projectId: config.projectId,
    },
  });
  sessionId = lease.sessionId;
  if (!sessionId || lease.ready !== true)
    throw new Error("Reticle lease did not connect to the app");
  receipt.sessionId = sessionId;
  stage = "session identity";
  const sessions = await tool("reticle_sessions", {});
  const connected = sessions.sessions?.find((s) => s.sessionId === sessionId);
  if (
    !connected ||
    connected.projectId !== config.projectId ||
    new URL(connected.url).origin !== app.origin
  ) {
    throw new Error("Reticle session is not the candidate app");
  }
  stage = "app readiness";
  const ready = await tool("reticle_assert", {
    sessionId,
    intent:
      "The candidate app has rendered its first flow control and exposes runtime identity",
    timeout_ms: assertMs,
    predicate: {
      kind: "allOf",
      predicates: [
        {
          kind: "element",
          query: { testid: flows[0].steps[0].anchor.value },
          state: "visible",
        },
        {
          kind: "state",
          store: "qmx-bootstrap",
          path: "candidateSha",
          equals: sha,
        },
        flows[0].precondition || {
          kind: "element",
          query: { testid: flows[0].steps[0].anchor.value },
          state: "visible",
        },
      ],
    },
  });
  if (ready.verified !== "yes") {
    receipt.verified = ready.verified === "no" ? "no" : "unknown";
    throw new Error(`App readiness verified=${ready.verified || "unknown"}`);
  }
  for (const flow of flows) {
    if (flow.startPath && flow.startPath !== "/")
      throw new Error("Flow startPath must be / for this host");
    for (const step of flow.steps) {
      stage = `flow ${flow.name}`;
      if (!step.anchor || step.anchor.kind !== "testid")
        throw new Error("Unsupported flow anchor; record a testid anchor");
      if (
        !["click", "fill", "check", "uncheck", "select", "press"].includes(
          step.action,
        )
      ) {
        throw new Error("Unsupported recorded action");
      }
      const result = await tool("reticle_act_and_wait", {
        sessionId,
        target: { testid: step.anchor.value },
        action: step.action,
        args: step.args || {},
        intent: flow.intent,
        timeout_ms: assertMs,
        refuseWhenThrottled: true,
        until: consequence(step.expect),
      });
      if (result.verified !== "yes") {
        receipt.verified = result.verified === "no" ? "no" : "unknown";
        throw new Error(
          `Flow ${flow.name}: Reticle verified=${result.verified || "unknown"}`,
        );
      }
    }
  }
  stage = "final assertion";
  const lastFlow = flows.at(-1);
  const result = await tool("reticle_assert", {
    sessionId,
    intent: lastFlow.intent,
    timeout_ms: assertMs,
    predicate: {
      kind: "allOf",
      predicates: [
        consequence(lastFlow.steps.at(-1).expect),
        {
          kind: "state",
          store: "qmx-bootstrap",
          path: "candidateSha",
          equals: sha,
        },
        { kind: "console", level: "error", absent: true },
      ],
    },
  });
  receipt.verified =
    result.verified === "yes"
      ? "yes"
      : result.verified === "no"
        ? "no"
        : "unknown";
  receipt.tool = "reticle_assert";
  receipt.journey = flows.map((f) => f.intent).join("; ");
  receipt.reason =
    receipt.verified === "yes"
      ? "Saved flow consequences verified on the candidate app"
      : "Final assertion did not pass";
} catch (error) {
  receipt.reason = `${stage}: ${error.message}`;
} finally {
  if (sessionId && client) {
    stage = "lease release";
    client.timeoutMs = Math.min(3000, callMs);
    try {
      const released = await tool("reticle_run", {
        tool: "reticle_lease",
        args: { action: "release", sessionId },
      });
      receipt.cleanup =
        released.released === true ? "released" : "release-not-confirmed";
    } catch {
      receipt.cleanup = "release-not-confirmed";
    }
    if (receipt.cleanup !== "released") {
      receipt.verified = "unknown";
      receipt.reason += "; lease release unconfirmed";
    }
  }
}
finish(receipt.verified === "yes" ? 0 : receipt.verified === "no" ? 1 : 2);
