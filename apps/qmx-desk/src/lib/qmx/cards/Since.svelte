<script lang="ts">
  import Icon from "../Icon.svelte";
  import { shell } from "$lib/shell/state.svelte";
  import { things } from "$lib/shell/things.svelte";
  import { earlier } from "$lib/shell/desk";
  import { tone } from "../state";
  import { panelSize } from "../tiles/panel-size";
  import Fit from "../Fit.svelte";

  // What happened while he was away, newest last as it happened. Compact:
  // one line each. Regular and expanded add where it ran. Older events fill
  // the rest of the widget.
  const size = panelSize();
  const since = [
    { id: "w-nightly", text: "Nightly evidence failed on step 4", when: "02:41" },
    { id: "p-gold", text: "It wrote 2 proposals before failing", when: "02:38" },
    { id: "w-brief", text: "Morning brief is ready", when: "07:00" },
    { id: "w-topup", text: "Data top-up ran 8 times", when: "since 01:00" },
    { id: "u-gold", text: "Gold breakout entered long on XAUUSD", when: "08:02" },
  ];
</script>

<div class="flex h-full min-h-0 flex-col">
  <ul class="min-h-0 flex-[0_1_auto] overflow-x-hidden overflow-y-auto">
    {#each since as s (s.text)}
      {@const o = things.get(s.id)}
      <li>
        <button class="pick flex w-full min-w-0 items-start gap-3 rounded-md px-2.5 {size.mode === 'compact' ? 'py-1.5' : 'py-2'} text-left" onclick={() => o && shell.open({ id: o.id })}>
          <span class="dot mt-[0.5em] {o ? tone[o.tone] : 'text-idle'}"></span>
          <span class="min-w-0 flex-1">
            <span class="text-foreground block {size.mode === 'compact' ? 'truncate' : 'line-clamp-2'}" title={s.text}>{s.text}</span>
            {#if size.mode !== "compact" && o?.where}
              <span class="text-muted-foreground mt-0.5 flex min-w-0 items-center gap-1.5 text-sm">
                <Icon name={o.where === "This PC" ? "laptop" : "server"} class="size-3.5 shrink-0" /><span class="truncate" title={o.where}>{o.where}</span>
              </span>
            {/if}
          </span>
          <span class="num text-muted-foreground shrink-0 text-sm">{s.when}</span>
        </button>
      </li>
    {/each}
  </ul>
  <Fit items={earlier} title="Before that" key={(d) => d.id}>
    {#snippet row(d)}
      <div class="flex min-w-0 items-start gap-3 px-2.5 py-1.5 text-sm">
        <span class="dot mt-[0.45em] {tone[d.tone]}"></span>
        <span class="text-muted-foreground min-w-0 flex-1 truncate" title={d.text}>{d.text}</span>
        <span class="num text-muted-foreground shrink-0">{d.when}</span>
      </div>
    {/snippet}
  </Fit>
</div>
