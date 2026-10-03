import { describe, expect, it } from "vitest";
import {
  addPane,
  pane,
  panes,
  parseLayouts,
  removePane,
  setSizes,
  split,
  swapPanels,
  visibleTree,
  type TileSplit,
} from "./tiles";

const tree = split("row", [
  [pane("a", "assets"), 20],
  [
    split("col", [
      [pane("b", "editor"), 60],
      [pane("c", "runs"), 40],
    ]),
    60,
  ],
  [pane("d", "inspector"), 20],
]);

describe("tiling layouts", () => {
  it("drops minimised tiles and gives their space to neighbours", () => {
    const v = visibleTree(tree, ["a"]) as TileSplit;
    expect(v.children).toHaveLength(2);
    expect(v.sizes[0] + v.sizes[1]).toBeCloseTo(100);
    expect(v.sizes[0]).toBeCloseTo(75);
  });

  it("collapses a split left with one visible child", () => {
    const v = visibleTree(tree, ["c"]) as TileSplit;
    expect(v.children[1]).toMatchObject({ kind: "pane", id: "b" });
  });

  it("returns nothing when every tile is minimised", () => {
    expect(visibleTree(tree, ["a", "b", "c", "d"])).toBeNull();
  });

  it("removes a tile and renormalises", () => {
    const r = removePane(tree, "d") as TileSplit;
    expect(panes(r).map((p) => p.id)).toEqual(["a", "b", "c"]);
    expect(r.sizes.reduce((x, y) => x + y)).toBeCloseTo(100);
  });

  it("swaps panels without moving tile ids", () => {
    const s = swapPanels(tree, "a", "d");
    expect(panes(s).map((p) => `${p.id}:${p.panel}`)).toEqual([
      "a:inspector",
      "b:editor",
      "c:runs",
      "d:assets",
    ]);
  });

  it("adds beside a tile, or at the right edge", () => {
    const beside = addPane(tree, pane("e", "logs"), "c");
    expect(panes(beside).map((p) => p.id)).toEqual(["a", "b", "c", "e", "d"]);
    const edge = addPane(tree, pane("e", "logs")) as TileSplit;
    expect(edge.children).toHaveLength(4);
    expect(edge.sizes.reduce((x, y) => x + y)).toBeCloseTo(100);
  });

  it("writes visible sizes back without touching hidden tiles", () => {
    const next = setSizes(tree, [], [30, 70], ["a"]) as TileSplit;
    expect(next.sizes[0]).toBe(20);
    expect(next.sizes[1] + next.sizes[2]).toBeCloseTo(80);
  });

  it("keeps good stored layouts and drops broken ones", () => {
    const out = parseLayouts(
      [
        { id: "u1", name: "Mine", root: tree, docked: ["a", "zz"] },
        { id: "u2", name: "Broken", root: { kind: "split", children: [] } },
        "junk",
      ],
      () => true,
    );
    expect(out).toHaveLength(1);
    expect(out[0].docked).toEqual(["a"]);
  });

  it("keeps the group a layout belongs to, and only a string one", () => {
    const out = parseLayouts(
      [
        { id: "p", name: "Pods mine", root: tree, docked: [], group: "pods" },
        { id: "q", name: "Odd", root: tree, docked: [], group: 7 },
      ],
      () => true,
    );
    expect(out[0].group).toBe("pods");
    expect(out[1].group).toBeUndefined();
  });
});
