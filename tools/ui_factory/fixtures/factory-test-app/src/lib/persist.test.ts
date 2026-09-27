import { describe, expect, it } from "vitest";
import { readNote, writeNote } from "./persist";

describe("FACTORY-TEST persist helper", () => {
  it("trims saved notes", () => {
    expect(writeNote("  hello  ")).toBe("hello");
  });

  it("reads empty as blank", () => {
    expect(readNote(null)).toBe("");
  });
});
