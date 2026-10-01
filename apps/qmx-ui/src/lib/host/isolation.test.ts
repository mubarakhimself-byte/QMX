import { existsSync, readdirSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import {
  CALLER_KIND_CAPABILITY_AT_INSPECT,
  DISPATCH_CANCEL_AT_INSPECT,
  DISPATCH_CHAT_AT_INSPECT,
  DISPATCH_INVOKE_AT_INSPECT,
  INSPECT_SHA,
  UNIQUE_ISSUERS_AT_INSPECT,
  HOME_CHROME_AT_INSPECT,
} from "../inspect";
import { listMailbox } from "./listMailbox";
import { createHostRuntime } from "./runtime";

const here = dirname(fileURLToPath(import.meta.url));
const srcRoot = join(here, "..", "..");

function walk(dir: string): string[] {
  const out: string[] = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (entry.name === "node_modules" || entry.name.startsWith(".")) continue;
    const full = join(dir, entry.name);
    if (entry.isDirectory()) out.push(...walk(full));
    else out.push(full);
  }
  return out;
}

describe("unique issuer isolation", () => {
  it("proves the three issuers after this story and absent at inspect", () => {
    expect(INSPECT_SHA).toBe("34c148be404a375cbfd79fd4ce6997452e4f1d20");
    expect(UNIQUE_ISSUERS_AT_INSPECT).toBe(false);
    expect(DISPATCH_INVOKE_AT_INSPECT).toBe(false);
    expect(DISPATCH_CHAT_AT_INSPECT).toBe(false);
    expect(DISPATCH_CANCEL_AT_INSPECT).toBe(false);
    expect(CALLER_KIND_CAPABILITY_AT_INSPECT).toBe(false);
    expect(HOME_CHROME_AT_INSPECT).toBe(false);
    for (const name of [
      "dispatchInvoke.ts",
      "dispatchChat.ts",
      "dispatchCancel.ts",
      "producer.ts",
      "capabilities.ts",
      "wireClient.ts",
    ]) {
      expect(existsSync(join(here, name))).toBe(true);
    }
  });

  it("keeps the wire client inside host/ and out of widgets", () => {
    const wireImport = /from ["'][^"']*host\/wireClient["']/;
    const widget = readFileSync(
      join(srcRoot, "lib/widgets/FactoryTestWidget.svelte"),
      "utf8",
    );
    expect(widget).not.toMatch(wireImport);
    expect(widget).not.toMatch(/dispatchInvoke|dispatchChat|dispatchCancel/);
    expect(widget).toContain("request_invoke");
    for (const file of walk(srcRoot)) {
      if (!/\.(ts|svelte)$/.test(file)) continue;
      if (file.includes(`${join("lib", "host")}`)) continue;
      const text = readFileSync(file, "utf8");
      expect(text).not.toMatch(wireImport);
    }
    for (const name of [
      "GraphCanvas",
      "LibraryBrowser",
      "json-render",
      "McpFrame",
    ]) {
      const hits = walk(join(srcRoot, "lib")).filter((file) =>
        file.includes(name),
      );
      for (const file of hits) {
        expect(readFileSync(file, "utf8")).not.toMatch(wireImport);
      }
    }
  });

  it("does not add a TypeScript sqlite writer", () => {
    const writer = /better-sqlite3|sql\.js|node:sqlite|from ["']sqlite/;
    for (const file of walk(srcRoot)) {
      if (!/\.(ts|svelte|js|mjs)$/.test(file)) continue;
      if (file.endsWith(".test.ts")) continue;
      expect(readFileSync(file, "utf8")).not.toMatch(writer);
    }
  });

  it("paints missing list_mailbox as query_unavailable, not empty mailbox", () => {
    const runtime = createHostRuntime();
    const result = listMailbox({ product_session_ref: "psess:H" }, runtime);
    expect(result.ok).toBe(false);
    if (result.ok) throw new Error("expected refuse");
    expect(result.incompatibility.code).toBe("query_unavailable");
    expect(result.incompatibility.emptySuccess).toBe(false);
    expect(runtime.wire.transport.calls).toHaveLength(0);
  });
});
