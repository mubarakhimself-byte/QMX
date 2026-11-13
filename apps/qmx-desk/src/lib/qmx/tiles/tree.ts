/**
 * A board layout is a tree of splits whose leaves are widgets, ported from the
 * October UI's tiling (workbench/tiles/tiles.ts). Pure functions, so every edit
 * (resize, minimise, move, swap, add, remove) is predictable.
 * Minimised widgets stay in the tree, so restoring puts them back where they
 * were; while docked they are left out of the drawn tree and their neighbours
 * take the space.
 */

export type Pane = { kind: "pane"; /** Widget reference: `place/panel`. */ id: string };
export type Split = {
  kind: "split";
  /** row = side by side, col = stacked. */
  dir: "row" | "col";
  children: Node[];
  /** Shares in percent, one per child. */
  sizes: number[];
};
export type Node = Pane | Split;
export type Layout = { root: Node | null; docked: string[] };
export type Side = "left" | "right" | "top" | "bottom";

export const pane = (id: string): Pane => ({ kind: "pane", id });

export const split = (dir: "row" | "col", parts: [Node, number][]): Split => ({
  kind: "split",
  dir,
  children: parts.map(([n]) => n),
  sizes: normalise(parts.map(([, s]) => s)),
});

export function normalise(sizes: number[]): number[] {
  const total = sizes.reduce((a, b) => a + b, 0) || 1;
  return sizes.map((s) => (s / total) * 100);
}

export function panes(node: Node | null): string[] {
  if (!node) return [];
  return node.kind === "pane" ? [node.id] : node.children.flatMap(panes);
}

export const keyOf = (n: Node): string =>
  n.kind === "pane" ? n.id : `${n.dir}(${n.children.map(keyOf).join(",")})`;

/** Rebuild a split from kept children: drop empties, collapse single children. */
function rebuild(dir: "row" | "col", kept: [Node, number][]): Node | null {
  if (kept.length === 0) return null;
  if (kept.length === 1) return kept[0][0];
  // A child split running the same way folds into its parent.
  const flat: [Node, number][] = [];
  for (const [n, s] of kept) {
    if (n.kind === "split" && n.dir === dir) n.children.forEach((c, i) => flat.push([c, (s * n.sizes[i]) / 100]));
    else flat.push([n, s]);
  }
  return split(dir, flat);
}

/** The tree as drawn: hidden widgets left out, their space given to neighbours. */
export function visibleTree(node: Node | null, hidden: readonly string[]): Node | null {
  if (!node) return null;
  if (node.kind === "pane") return hidden.includes(node.id) ? null : node;
  const kept: [Node, number][] = [];
  node.children.forEach((c, i) => {
    const v = visibleTree(c, hidden);
    if (v) kept.push([v, node.sizes[i] ?? 1]);
  });
  if (kept.length === 0) return null;
  if (kept.length === 1) return kept[0][0];
  return { kind: "split", dir: node.dir, children: kept.map(([n]) => n), sizes: normalise(kept.map(([, s]) => s)) };
}

/** Take a widget off the board for good. */
export function removePane(node: Node | null, id: string): Node | null {
  if (!node) return null;
  if (node.kind === "pane") return node.id === id ? null : node;
  const kept: [Node, number][] = [];
  node.children.forEach((c, i) => {
    const v = removePane(c, id);
    if (v) kept.push([v, node.sizes[i] ?? 1]);
  });
  return rebuild(node.dir, kept);
}

/** Swap two widgets; each takes the other's place and size. */
export function swapPanes(node: Node | null, a: string, b: string): Node | null {
  if (!node || a === b) return node;
  const walk = (n: Node): Node =>
    n.kind === "split" ? { ...n, children: n.children.map(walk) } : n.id === a ? pane(b) : n.id === b ? pane(a) : n;
  return walk(node);
}

const axis = (s: Side): "row" | "col" => (s === "left" || s === "right" ? "row" : "col");
const first = (s: Side) => s === "left" || s === "top";

/**
 * Put a widget beside `target` on `side`, splitting the target's space in
 * half. With no target it goes along that whole edge of the board: a full
 * row or a full column.
 */
export function insertPane(root: Node | null, id: string, target: string | null, side: Side): Node {
  const p = pane(id);
  if (!root) return p;
  const dir = axis(side);
  if (target === null) {
    if (root.kind === "split" && root.dir === dir) {
      const share = 100 / (root.children.length + 1);
      const rest = root.sizes.map((s) => s * (1 - share / 100));
      return first(side)
        ? { ...root, children: [p, ...root.children], sizes: [share, ...rest] }
        : { ...root, children: [...root.children, p], sizes: [...rest, share] };
    }
    const share = dir === "row" ? 28 : 34;
    return first(side) ? split(dir, [[p, share], [root, 100 - share]]) : split(dir, [[root, 100 - share], [p, share]]);
  }
  const walk = (n: Node): Node => {
    if (n.kind === "pane") {
      if (n.id !== target) return n;
      return first(side) ? split(dir, [[p, 50], [n, 50]]) : split(dir, [[n, 50], [p, 50]]);
    }
    const i = n.children.findIndex((c) => c.kind === "pane" && c.id === target);
    if (i >= 0 && n.dir === dir) {
      // Same direction as the parent: become a sibling, sharing the target's space.
      const half = n.sizes[i] / 2;
      const at = first(side) ? i : i + 1;
      const children = [...n.children];
      children.splice(at, 0, p);
      const sizes = [...n.sizes];
      sizes.splice(i, 1, half, half);
      return { ...n, children, sizes };
    }
    return { ...n, children: n.children.map(walk) };
  };
  return walk(root);
}

/** Move a widget next to another one (or along a board edge when target is null). */
export function movePane(root: Node | null, id: string, target: string | null, side: Side): Node | null {
  if (id === target) return root;
  return insertPane(removePane(root, id), id, target, side);
}

/**
 * Apply sizes for a drawn split back onto the stored tree. `path` indexes the
 * drawn (visible) tree; hidden children keep their own share.
 */
export function setSizes(node: Node | null, path: number[], sizes: number[], hidden: readonly string[]): Node | null {
  if (!node || node.kind === "pane") return node;
  const visible = node.children.map((c, i) => (visibleTree(c, hidden) ? i : -1)).filter((i) => i >= 0);
  if (path.length === 0) {
    if (visible.length !== sizes.length) return node;
    const hiddenTotal = node.sizes.filter((_, i) => !visible.includes(i)).reduce((a, b) => a + b, 0);
    const scale = (100 - hiddenTotal) / 100;
    const next = [...node.sizes];
    visible.forEach((ci, k) => (next[ci] = sizes[k] * scale));
    return { ...node, sizes: next };
  }
  const target = visible[path[0]];
  if (target === undefined) return node;
  return {
    ...node,
    children: node.children.map((c, i) => (i === target ? (setSizes(c, path.slice(1), sizes, hidden) ?? c) : c)),
  };
}

/** The smallest a node may get, in rem, along an axis: room for a header and a few lines. */
export const MIN = { w: 14, h: 6.5 };
export function minSize(n: Node, along: "w" | "h", gap: number): number {
  if (n.kind === "pane") return MIN[along];
  const parts = n.children.map((c) => minSize(c, along, gap));
  const stacked = (n.dir === "row") === (along === "w");
  return stacked ? parts.reduce((a, b) => a + b, 0) + gap * (parts.length - 1) : Math.max(...parts);
}

/** Validate a stored layout; anything malformed gives null, never throws. */
export function parseLayout(raw: unknown): Layout | null {
  const node = (n: unknown, depth: number): Node | null => {
    if (!n || typeof n !== "object" || depth > 10) return null;
    const o = n as Record<string, unknown>;
    if (o.kind === "pane") return typeof o.id === "string" ? pane(o.id) : null;
    if (o.kind === "split" && (o.dir === "row" || o.dir === "col") && Array.isArray(o.children)) {
      const kids = o.children.map((c) => node(c, depth + 1)).filter((c): c is Node => !!c);
      const sizes =
        Array.isArray(o.sizes) && o.sizes.length === kids.length
          ? o.sizes.map((s) => (typeof s === "number" && s > 0 ? s : 1))
          : kids.map(() => 1);
      return rebuild(o.dir, kids.map((k, i) => [k, sizes[i]]));
    }
    return null;
  };
  if (!raw || typeof raw !== "object") return null;
  const o = raw as Record<string, unknown>;
  const root = o.root === null ? null : node(o.root, 0);
  const ids = panes(root);
  const docked = Array.isArray(o.docked) ? o.docked.filter((d): d is string => typeof d === "string" && ids.includes(d)) : [];
  return { root, docked };
}
