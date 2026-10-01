import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import http from "node:http";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

const script = new URL("./reticle-check.mjs", import.meta.url);

async function run(env, entry = script) {
  const child = spawn(
    process.execPath,
    [entry.pathname.replace(/^\/(.:)/, "$1")],
    {
      env: { ...process.env, ...env },
      stdio: ["ignore", "pipe", "pipe"],
    },
  );
  let output = "";
  child.stdout.on("data", (data) => (output += data));
  child.stderr.on("data", (data) => (output += data));
  const timer = setTimeout(() => child.kill("SIGKILL"), 4000);
  const code = await new Promise((resolve) => child.on("exit", resolve));
  clearTimeout(timer);
  return { code, output };
}

test("a handwritten yes cannot bypass a live Reticle check", async () => {
  const dir = await mkdtemp(join(tmpdir(), "qmx-reticle-"));
  try {
    const sidecar = join(dir, "forged.json");
    await writeFile(
      sidecar,
      JSON.stringify({ verdict: "yes", tool: "reticle_assert" }),
    );
    const result = await run({
      RETICLE_EVIDENCE_FILE: sidecar,
      RETICLE_DAEMON_URL: "http://127.0.0.1:1",
      RETICLE_RESULT_FILE: join(dir, "result.json"),
      RETICLE_TOTAL_TIMEOUT_MS: "500",
    });
    assert.notEqual(result.code, 0, result.output);
  } finally {
    await rm(dir, { recursive: true });
  }
});

async function fakeReticle(scenario, check) {
  const dir = await mkdtemp(join(tmpdir(), "qmx-reticle-"));
  let stream;
  let released = false;
  const server = http.createServer(async (req, res) => {
    if (req.url === "/status") {
      res.end(JSON.stringify({ running: true, version: "2.14.0" }));
    } else if (req.url === "/mcp/sse") {
      stream = res;
      res.writeHead(200, { "Content-Type": "text/event-stream" });
      res.write("event: endpoint\ndata: /mcp/message?sessionId=test\n\n");
    } else if (req.url.startsWith("/mcp/message")) {
      let body = "";
      for await (const chunk of req) body += chunk;
      const message = JSON.parse(body);
      res.writeHead(202).end();
      if (!message.id || scenario === "silent-reply") return;
      let value = {};
      if (message.method === "tools/call") {
        const { name, arguments: args } = message.params;
        if (name === "reticle_run" && args.args.action === "acquire") {
          value = { sessionId: "lease-test", ready: true };
        } else if (name === "reticle_run") {
          released = true;
          value = { released: true };
        } else if (name === "reticle_sessions") {
          value = {
            sessions: [
              {
                sessionId: "lease-test",
                projectId: scenario === "wrong-project" ? "other" : "qmx-ui",
                url: base,
              },
            ],
          };
        } else {
          value = {
            verified:
              scenario === "unknown"
                ? "unknown"
                : scenario === "no"
                  ? "no"
                  : "yes",
          };
        }
        value = { structuredContent: value };
      }
      stream.write(
        `event: message\ndata: ${JSON.stringify({ jsonrpc: "2.0", id: message.id, result: value })}\n\n`,
      );
    } else {
      res.end(
        '<meta name="qmx-candidate-sha" content="' + "a".repeat(40) + '">',
      );
    }
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const base = `http://127.0.0.1:${server.address().port}`;
  try {
    const result = await run({
      RETICLE_DAEMON_URL: base,
      RETICLE_VERIFY_URL: base,
      QMX_CANDIDATE_SHA: "a".repeat(40),
      RETICLE_RESULT_FILE: join(dir, "result.json"),
      RETICLE_TOTAL_TIMEOUT_MS: "1500",
      RETICLE_CALL_TIMEOUT_MS: "200",
    });
    const receipt = JSON.parse(
      await readFile(join(dir, "result.json"), "utf8"),
    );
    await check(result, receipt, released);
  } finally {
    server.closeAllConnections();
    await new Promise((resolve) => server.close(resolve));
    await rm(dir, { recursive: true });
  }
}

test("an acknowledged MCP POST with no SSE reply is bounded", async () => {
  await fakeReticle("silent-reply", (result, receipt) => {
    assert.equal(result.code, 2, result.output);
    assert.match(receipt.reason, /response timeout/);
    assert.ok(receipt.duration_ms < 1200);
  });
});

for (const verdict of ["unknown", "no"]) {
  test(`Reticle ${verdict} fails and releases the owned lease`, async () => {
    await fakeReticle(verdict, (result, receipt, released) => {
      assert.equal(result.code, verdict === "no" ? 1 : 2, result.output);
      assert.equal(receipt.verified, verdict);
      assert.equal(receipt.cleanup, "released");
      assert.equal(released, true);
    });
  });
}

test("a lease for another project cannot pass and is released", async () => {
  await fakeReticle("wrong-project", (result, receipt, released) => {
    assert.equal(result.code, 2, result.output);
    assert.match(receipt.reason, /not the candidate app/);
    assert.equal(released, true);
  });
});

test("the process cutoff kills a worker whose event loop is stuck", async () => {
  const dir = await mkdtemp(join(tmpdir(), "qmx-reticle-"));
  try {
    await mkdir(join(dir, "scripts"));
    await writeFile(
      join(dir, "scripts/reticle-check.mjs"),
      await readFile(script),
    );
    await writeFile(
      join(dir, "scripts/reticle-worker.mjs"),
      "while (true) {}\n",
    );
    const result = await run(
      {
        RETICLE_TOTAL_TIMEOUT_MS: "100",
        RETICLE_RESULT_FILE: join(dir, "result.json"),
      },
      new URL(
        `file:///${join(dir, "scripts/reticle-check.mjs").replaceAll("\\", "/")}`,
      ),
    );
    assert.equal(result.code, 2, result.output);
    const receipt = JSON.parse(
      await readFile(join(dir, "result.json"), "utf8"),
    );
    assert.match(receipt.reason, /process deadline/);
    assert.equal(receipt.verified, "unknown");
  } finally {
    await rm(dir, { recursive: true });
  }
});

test("an MCP server that never announces its endpoint times out with retained evidence", async () => {
  const dir = await mkdtemp(join(tmpdir(), "qmx-reticle-"));
  const server = http.createServer((req, res) => {
    if (req.url === "/status") {
      res.end(JSON.stringify({ running: true, version: "2.14.0" }));
    } else if (req.url === "/mcp/sse") {
      res.writeHead(200, { "Content-Type": "text/event-stream" });
      res.flushHeaders(); // deliberately never responds
    } else {
      res.end(
        '<meta name="qmx-candidate-sha" content="' + "a".repeat(40) + '">',
      );
    }
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const url = `http://127.0.0.1:${server.address().port}`;
  const start = Date.now();
  try {
    const result = await run({
      RETICLE_DAEMON_URL: url,
      RETICLE_VERIFY_URL: url,
      QMX_CANDIDATE_SHA: "a".repeat(40),
      RETICLE_RESULT_FILE: join(dir, "result.json"),
      RETICLE_TOTAL_TIMEOUT_MS: "800",
      RETICLE_CALL_TIMEOUT_MS: "200",
    });
    assert.equal(result.code, 2, result.output);
    assert.ok(Date.now() - start < 2500);
    const receipt = JSON.parse(
      await readFile(join(dir, "result.json"), "utf8"),
    );
    assert.equal(receipt.verified, "unknown");
    assert.match(receipt.reason, /timeout|deadline/i);
  } finally {
    server.closeAllConnections();
    await new Promise((resolve) => server.close(resolve));
    await rm(dir, { recursive: true });
  }
});
