<script lang="ts">
  import { tone, wordTone, isNumber, numberTone } from "./state";

  let { cols, rows }: { cols: string[]; rows: string[][] } = $props();

  // A narrow table drops columns, but never the name and never the state
  // (live, paper, running, passed…): those say what the row is. Other middle columns
  // go first, then the last one.
  const isState = (i: number) => i > 0 && (/^(state|verdict)$/i.test(cols[i] ?? "") || rows.some((r) => !!wordTone[(r[i] ?? "").toLowerCase()]));
  const keep = $derived(cols.map((_, i) => i === 0 || isState(i)));
  const cls = (i: number) => (keep[i] ? "keep" : i === cols.length - 1 ? "last" : "mid");
</script>

<div class="dt h-full overflow-auto">
  <table class="w-full border-separate border-spacing-0">
    <thead>
      <tr>
        {#each cols as c, i (c)}
          <th
            class="{cls(i)} text-muted-foreground bg-panel border-border sticky top-0 border-b px-2.5 py-2 text-sm font-medium whitespace-nowrap {i ===
            0
              ? 'text-left'
              : 'text-right'}"
          >
            {c}
          </th>
        {/each}
      </tr>
    </thead>
    <tbody>
      {#each rows as row, ri (ri)}
        <tr class="hover:bg-accent/50 transition-colors duration-150">
          {#each row as cell, i (i)}
            {@const word = wordTone[cell.toLowerCase()]}
            <td
              class="{cls(i)} border-border/60 border-b px-2.5 py-2 {i === 0
                ? 'max-w-[13rem] min-w-[7rem] text-left font-medium'
                : 'text-right whitespace-nowrap'}"
            >
              {#if i === 0}
                <span class="block truncate" title={cell}>{cell}</span>
              {:else if word}
                <span class="inline-flex items-center gap-1.5 {tone[word]}">
                  <span class="dot size-1.5"></span>
                  <span class="text-foreground">{cell}</span>
                </span>
              {:else if isNumber(cell)}
                <span class="num {numberTone(cell)}">{cell}</span>
              {:else if cell === ""}
                <span class="text-idle" title="Not set">·</span>
              {:else}
                <span class="text-muted-foreground inline-block max-w-[14rem] truncate align-bottom" title={cell}
                  >{cell}</span
                >
              {/if}
            </td>
          {/each}
        </tr>
      {/each}
    </tbody>
  </table>
</div>

<style>
  .dt {
    container-type: inline-size;
  }
  /* The name and the state stay, whatever a board's own rules hide. */
  .dt :global(.keep) {
    display: table-cell !important;
  }
  @container (max-width: 26rem) {
    .mid {
      display: none;
    }
  }
  @container (max-width: 18rem) {
    .last {
      display: none;
    }
  }
</style>
