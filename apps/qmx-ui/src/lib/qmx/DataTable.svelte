<script lang="ts" module>
  export type Column = {
    key: string;
    label: string;
    /** number: right-aligned mono; change: signed, coloured, with arrow. */
    kind?: "text" | "number" | "change";
    digits?: number;
  };
  export type Row = Record<string, string | number | null>;
</script>

<script lang="ts">
  /** The one table every widget uses, so density and numbers stay consistent. */
  import { cn } from "$lib/utils";

  let {
    columns,
    rows,
    dense = false,
    caption,
  }: {
    columns: Column[];
    rows: Row[];
    dense?: boolean;
    caption?: string;
  } = $props();

  function fmt(v: Row[string], c: Column): string {
    if (v === null || v === undefined || v === "") return "—";
    if (typeof v !== "number") return String(v);
    const n = Math.abs(v).toFixed(c.digits ?? 2);
    if (c.kind === "change") return `${v >= 0 ? "▲ +" : "▼ −"}${n}%`;
    return v.toLocaleString(undefined, {
      minimumFractionDigits: c.digits ?? 0,
      maximumFractionDigits: c.digits ?? 2,
    });
  }
</script>

<table class="w-full text-sm">
  {#if caption}<caption class="sr-only">{caption}</caption>{/if}
  <thead>
    <tr class="text-muted-foreground text-left text-xs">
      {#each columns as c (c.key)}
        <th
          class={cn(
            "pb-1.5 font-medium",
            c.kind && c.kind !== "text" && "text-right",
          )}>{c.label}</th
        >
      {/each}
    </tr>
  </thead>
  <tbody>
    {#each rows as r, i (i)}
      <tr class="border-t">
        {#each columns as c, j (c.key)}
          {@const v = r[c.key]}
          <td
            class={cn(
              dense ? "py-1" : "py-2",
              j === 0 && "font-medium",
              c.kind && c.kind !== "text" && "num text-right whitespace-nowrap",
              c.kind === "change" &&
                typeof v === "number" &&
                (v >= 0 ? "text-success" : "text-destructive"),
            )}>{fmt(v, c)}</td
          >
        {/each}
      </tr>
    {/each}
  </tbody>
</table>
