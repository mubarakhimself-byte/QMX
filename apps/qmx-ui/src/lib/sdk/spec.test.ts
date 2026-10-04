import { describe, expect, it } from "vitest";
import { SAMPLE_PANEL, validate, type PanelSpec } from "./spec";

const tiny = (elements: PanelSpec["elements"], root = "a"): PanelSpec => ({
  title: "T",
  root,
  elements,
});

describe("panel descriptions", () => {
  it("accepts the sample the copilot builds", () => {
    expect(validate(SAMPLE_PANEL)).toEqual([]);
  });

  it("refuses types that are not in QMX's catalog", () => {
    const errors = validate(tiny({ a: { type: "Script", props: {} } }));
    expect(errors.join()).toMatch(/not in QMX's catalog/);
  });

  it("names missing props and missing children", () => {
    const errors = validate(
      tiny({
        a: { type: "Stack", children: ["b", "x"] },
        b: { type: "Metric" },
      }),
    );
    expect(errors.join()).toMatch(/needs label/);
    expect(errors.join()).toMatch(/child "x" is missing/);
  });

  it("stops loops and leaf types holding children", () => {
    expect(
      validate(tiny({ a: { type: "Stack", children: ["a"] } })).join(),
    ).toMatch(/contains itself/);
    expect(
      validate(
        tiny({ a: { type: "Text", props: { text: "x" }, children: ["a"] } }),
      ).join(),
    ).toMatch(/cannot hold children/);
  });

  it("is safe with junk", () => {
    expect(validate(null).length).toBeGreaterThan(0);
    expect(validate({ title: "x" }).length).toBeGreaterThan(0);
  });
});
