/**
 * Tiling layouts: a tree of splits whose leaves are panels. Pure functions so
 * every edit (minimise, close, swap, add, resize) is predictable and tested.
 * Minimised panels leave the tree's visible view and sit in a dock; their
 * neighbours take the space (Bloomberg-style reflow).
 */

export type LinkGroup = "violet" | "amber" | "teal";
export const LINK_GROUPS: LinkGroup[] = ["violet", "amber", "teal"];

export type TilePane = {
  kind: "pane";
  /** Stable id of this tile within the layout. */
  id: string;
  /** Catalog id of the panel shown in the tile. */
  panel: string;
  /** Tiles in the same group follow one selection. */
  link?: LinkGroup;
};

export type TileSplit = {
  kind: "split";
  /** row = side by side, col = stacked. */
  dir: "row" | "col";
  children: TileNode[];
  /** Percentages, one per child. */
  sizes: number[];
};

export type TileNode = TilePane | TileSplit;

export type TileLayout = {
  id: string;
  name: string;
  root: TileNode;
  /** Ids of minimised tiles. */
  docked: string[];
};

export const pane = (
  id: string,
  panel: string,
  link?: LinkGroup,
): TilePane => ({
  kind: "pane",
  id,
  panel,
  ...(link ? { link } : {}),
});

export const split = (
  dir: "row" | "col",
  parts: [TileNode, number][],
): TileSplit => ({
  kind: "split",
  dir,
  children: parts.map(([n]) => n),
  sizes: parts.map(([, s]) => s),
});

export function panes(node: TileNode): TilePane[] {
  return node.kind === "pane" ? [node] : node.children.flatMap(panes);
}

function normalise(sizes: number[]): number[] {
  const total = sizes.reduce((a, b) => a + b, 0) || 1;
  return sizes.map((s) => (s / total) * 100);
}

/**
 * The tree as drawn: docked tiles removed, empty splits dropped, single-child
 * splits collapsed, remaining sizes scaled back to 100%.
 */
export function visibleTree(
  node: TileNode,
  docked: readonly string[],
): TileNode | null {
  if (node.kind === "pane") return docked.includes(node.id) ? null : node;
  const kept: [TileNode, number][] = [];
  node.children.forEach((c, i) => {
    const v = visibleTree(c, docked);
    if (v) kept.push([v, node.sizes[i] ?? 1]);
  });
  if (kept.length === 0) return null;
  if (kept.length === 1) return kept[0][0];
  return {
    kind: "split",
    dir: node.dir,
    children: kept.map(([n]) => n),
    sizes: normalise(kept.map(([, s]) => s)),
  };
}

/** Remove a tile for good (closing it in edit mode). */
export function removePane(node: TileNode, id: string): TileNode | null {
  if (node.kind === "pane") return node.id === id ? null : node;
  const kept: [TileNode, number][] = [];
  node.children.forEach((c, i) => {
    const v = removePane(c, id);
    if (v) kept.push([v, node.sizes[i] ?? 1]);
  });
  if (kept.length === 0) return null;
  if (kept.length === 1) return kept[0][0];
  return split(
    node.dir,
    kept.map(([n], i) => [n, normalise(kept.map(([, s]) => s))[i]]),
  );
}

/** Swap the panels (and link groups) of two tiles; tile ids keep their places. */
export function swapPanels(node: TileNode, a: string, b: string): TileNode {
  const all = panes(node);
  const pa = all.find((p) => p.id === a);
  const pb = all.find((p) => p.id === b);
  if (!pa || !pb || a === b) return node;
  const walk = (n: TileNode): TileNode => {
    if (n.kind === "split") return { ...n, children: n.children.map(walk) };
    if (n.id === a) return { ...n, panel: pb.panel, link: pb.link };
    if (n.id === b) return { ...n, panel: pa.panel, link: pa.link };
    return n;
  };
  return walk(node);
}

/**
 * Add a panel beside an existing tile (splitting it), or at the right edge of
 * the layout when no tile is given.
 */
export function addPane(
  node: TileNode | null,
  newPane: TilePane,
  besideId?: string,
): TileNode {
  if (!node) return newPane;
  if (besideId) {
    let placed = false;
    const walk = (n: TileNode): TileNode => {
      if (n.kind === "pane") {
        if (n.id !== besideId || placed) return n;
        placed = true;
        return split("col", [
          [n, 60],
          [newPane, 40],
        ]);
      }
      return { ...n, children: n.children.map(walk) };
    };
    const out = walk(node);
    if (placed) return out;
  }
  if (node.kind === "split" && node.dir === "row") {
    const share = 100 / (node.children.length + 1);
    return {
      ...node,
      children: [...node.children, newPane],
      sizes: [...node.sizes.map((s) => s * (1 - share / 100)), share],
    };
  }
  return split("row", [
    [node, 70],
    [newPane, 30],
  ]);
}

/** Apply sizes reported for a visible split back onto the stored tree. */
export function setSizes(
  node: TileNode,
  path: number[],
  sizes: number[],
  docked: readonly string[],
): TileNode {
  if (node.kind === "pane") return node;
  if (path.length === 0) {
    // Map visible sizes onto children that are still visible; hidden ones keep theirs.
    const visible = node.children
      .map((c, i) => (visibleTree(c, docked) ? i : -1))
      .filter((i) => i >= 0);
    if (visible.length !== sizes.length) return node;
    const hiddenTotal = node.sizes
      .filter((_, i) => !visible.includes(i))
      .reduce((a, b) => a + b, 0);
    const scale = (100 - hiddenTotal) / 100;
    const next = [...node.sizes];
    visible.forEach((ci, k) => (next[ci] = sizes[k] * scale));
    return { ...node, sizes: next };
  }
  const visible = node.children
    .map((c, i) => (visibleTree(c, docked) ? i : -1))
    .filter((i) => i >= 0);
  const target = visible[path[0]];
  if (target === undefined) return node;
  return {
    ...node,
    children: node.children.map((c, i) =>
      i === target ? setSizes(c, path.slice(1), sizes, docked) : c,
    ),
  };
}

/** Validate stored layouts; anything malformed is dropped, never thrown. */
export function parseLayouts(
  raw: unknown,
  known: (panel: string) => boolean,
): TileLayout[] {
  if (!Array.isArray(raw)) return [];
  const node = (n: unknown, depth: number): TileNode | null => {
    if (!n || typeof n !== "object" || depth > 8) return null;
    const o = n as Record<string, unknown>;
    if (o.kind === "pane") {
      if (typeof o.id !== "string" || typeof o.panel !== "string") return null;
      const link = LINK_GROUPS.includes(o.link as LinkGroup)
        ? (o.link as LinkGroup)
        : undefined;
      // Unknown panels are kept: the board shows them as unsupported.
      void known;
      return pane(o.id, o.panel, link);
    }
    if (o.kind === "split" && (o.dir === "row" || o.dir === "col")) {
      const kids = Array.isArray(o.children)
        ? o.children
            .map((c) => node(c, depth + 1))
            .filter((c): c is TileNode => !!c)
        : [];
      if (!kids.length) return null;
      const sizes =
        Array.isArray(o.sizes) && o.sizes.length === kids.length
          ? o.sizes.map((s) => (typeof s === "number" && s > 0 ? s : 1))
          : kids.map(() => 1);
      return {
        kind: "split",
        dir: o.dir,
        children: kids,
        sizes: normalise(sizes),
      };
    }
    return null;
  };
  return raw.flatMap((l) => {
    if (!l || typeof l !== "object") return [];
    const o = l as Record<string, unknown>;
    const root = node(o.root, 0);
    if (typeof o.id !== "string" || typeof o.name !== "string" || !root)
      return [];
    const ids = panes(root).map((p) => p.id);
    const docked = Array.isArray(o.docked)
      ? o.docked.filter(
          (d): d is string => typeof d === "string" && ids.includes(d),
        )
      : [];
    return [{ id: o.id, name: o.name.slice(0, 40), root, docked }];
  });
}
