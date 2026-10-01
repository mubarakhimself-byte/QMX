import { describe, expect, it } from "vitest";
import { CATALOG } from "./catalog";

describe("component catalog", () => {
  it("has unique types", () => {
    const types = CATALOG.map((c) => c.type);
    expect(new Set(types).size).toBe(types.length);
  });

  it("gives every entry an example that sets its required props", () => {
    for (const c of CATALOG) {
      for (const [name, spec] of Object.entries(c.props)) {
        if (spec.required)
          expect(c.example, `${c.type}.${name}`).toHaveProperty(name);
      }
    }
  });

  it("only uses enum options that the spec declares", () => {
    for (const c of CATALOG) {
      for (const [name, spec] of Object.entries(c.props)) {
        const v = c.example[name];
        if (spec.type === "enum" && v !== undefined)
          expect(spec.options).toContain(v);
      }
    }
  });
});
