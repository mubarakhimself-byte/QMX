import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import {
  DAEMON_PORT,
  SAMPLE_ORIGIN,
  SPA_DEV_PORT,
  isDaemonOrigin,
  portOfOrigin,
} from "./origin";
import {
  ENVELOPE_TYPES_AT_INSPECT,
  FIRST_PARTY_SVELTE_HOST_AT_INSPECT,
  PLATFORM_RAIL_AT_INSPECT,
  HOST_IDENTITY,
  INSPECT_SHA,
  QMA_UI_CONTRACT_AT_INSPECT,
  UNIQUE_ISSUERS_AT_INSPECT,
} from "./inspect";
import { START_LOCAL_MODE, startLocalAction } from "./spawn";
import { parseFixtureState, stateCopy } from "./bootstrap";

const root = join(dirname(fileURLToPath(import.meta.url)), "..", "..");

function read(rel: string): string {
  return readFileSync(join(root, rel), "utf8");
}

describe("isolated SPA scaffold", () => {
  it("pins the ADR-0026 stack seed exactly", () => {
    const pkg = JSON.parse(read("package.json")) as {
      engines: { node: string };
      packageManager: string;
      dependencies: Record<string, string>;
      devDependencies: Record<string, string>;
    };
    expect(pkg.engines.node).toBe(">=22.12.0 <23.0.0");
    expect(pkg.packageManager).toBe("pnpm@10.18.3");
    expect(pkg.dependencies.svelte).toBe("5.57.1");
    expect(pkg.dependencies["bits-ui"]).toBe("2.19.3");
    expect(pkg.dependencies["@xyflow/svelte"]).toBe("1.6.6");
    expect(pkg.devDependencies["@sveltejs/kit"]).toBe("2.70.3");
    expect(pkg.devDependencies["@sveltejs/adapter-static"]).toBe("3.0.10");
    expect(pkg.devDependencies["@sveltejs/vite-plugin-svelte"]).toBe("7.3.1");
    expect(pkg.devDependencies.typescript).toBe("5.9.2");
    expect(pkg.devDependencies.vite).toBe("8.3.0");
    expect(pkg.devDependencies.tailwindcss).toBe("4.3.3");
    expect(pkg.devDependencies["shadcn-svelte"]).toBe("1.7.0");
    expect(pkg.devDependencies.typescript.startsWith("7")).toBe(false);
  });

  it("is a static SPA with ssr false and 200.html fallback", () => {
    expect(read("src/routes/+layout.ts")).toContain("export const ssr = false");
    expect(read("svelte.config.js")).toContain('fallback: "200.html"');
    expect(read("static/200.html")).toContain("200.html");
  });

  it("never binds daemon port 8765", () => {
    expect(SPA_DEV_PORT).not.toBe(DAEMON_PORT);
    expect(isDaemonOrigin(SAMPLE_ORIGIN)).toBe(false);
    expect(portOfOrigin(SAMPLE_ORIGIN)).toBe("5173");
    expect(isDaemonOrigin("http://127.0.0.1:8765")).toBe(true);
    const vite = read("vite.config.ts");
    expect(vite).toContain("assertNotDaemonPort");
    expect(vite).not.toMatch(/port:\s*8765/);
  });

  it("does not spawn Python from browser chrome", () => {
    expect(startLocalAction()).toBe(START_LOCAL_MODE);
    const src = [
      read("src/lib/spawn.ts"),
      read("src/lib/screens/Bootstrap.svelte"),
      read("src/lib/shell/PlatformRail.svelte"),
      read("src/lib/shell/openedApps.ts"),
      read("src/lib/host/wireClient.ts"),
      read("src/lib/host/dispatchInvoke.ts"),
      read("src/routes/+page.svelte"),
      read("src/routes/+layout.svelte"),
    ].join("\n");
    expect(src).not.toMatch(/child_process/);
    expect(src).not.toMatch(/spawn\(/);
    expect(src).not.toMatch(/from ["']qmb/);
    expect(src).not.toMatch(/from ["']qml/);
  });

  it("is honest about inspect SHA 34c148be", () => {
    expect(INSPECT_SHA).toBe("34c148be404a375cbfd79fd4ce6997452e4f1d20");
    expect(FIRST_PARTY_SVELTE_HOST_AT_INSPECT).toBe(false);
    expect(PLATFORM_RAIL_AT_INSPECT).toBe(false);
    expect(UNIQUE_ISSUERS_AT_INSPECT).toBe(false);
    expect(QMA_UI_CONTRACT_AT_INSPECT).toBe("stub");
    expect(ENVELOPE_TYPES_AT_INSPECT).toBe("fixtures-not-e2e");
    expect(HOST_IDENTITY.compUi).toBe(false);
    expect(HOST_IDENTITY.kind).toBe("client-of-qma-wire");
  });

  it("keeps empty bootstrap as setup copy", () => {
    expect(parseFixtureState(null)).toBe("empty");
    expect(stateCopy("empty")).toMatch(/does not spawn Python/);
    expect(stateCopy("reconnecting")).toMatch(/Distinct from failed/);
  });
});
