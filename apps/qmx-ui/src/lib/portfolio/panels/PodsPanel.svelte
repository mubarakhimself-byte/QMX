<script lang="ts">
  /** Every pod as a card: how it sizes risk, money, room above its kill line, bots. Click to open it. */
  import Plus from "@lucide/svelte/icons/plus";
  import { cn } from "$lib/utils";
  import Sparkline from "$lib/demo/Sparkline.svelte";
  import { PODS, accountById } from "../demo";
  import { MODE_BORDER, pct, usd } from "../bits";
  import { portfolio } from "../portfolio.svelte";

  const rows = $derived(
    PODS.filter((p) => portfolio.world !== "live" || p.mode === "LIVE"),
  );
</script>

<div
  class="grid h-full content-start gap-2 overflow-auto p-2 [grid-template-columns:repeat(auto-fill,minmax(16rem,1fr))]"
>
  {#each rows as p (p.id)}
    {@const room = Math.max(0, (p.equity - p.floor) / (p.start - p.floor))}
    <button
      type="button"
      class={cn(
        "hover:bg-muted/40 flex flex-col gap-2 rounded-xl border-2 p-3 text-left transition-colors",
        portfolio.pod === p.id && "bg-muted/50",
      )}
      style="border-color: {p.mode === 'LIVE'
        ? MODE_BORDER.live
        : MODE_BORDER.paper}"
      aria-pressed={portfolio.pod === p.id}
      onclick={() => (portfolio.pod = p.id)}
    >
      <span class="flex items-center gap-2">
        <span class="text-base font-semibold">{p.name}</span>
        <span class="text-muted-foreground ml-auto text-xs">{p.mode}</span>
      </span>
      <span class="bg-muted/60 self-start rounded px-2 py-0.5 text-xs"
        >{p.method.label}</span
      >
      <span class="block h-12"
        ><Sparkline values={p.curve} class="block h-full w-full" /></span
      >
      <span class="flex items-baseline gap-2">
        <span class="num text-xl font-semibold">{usd(p.equity)}</span>
        <span
          class={cn(
            "num text-sm",
            p.today >= 0 ? "text-success" : "text-destructive",
          )}>{pct(p.today)}</span
        >
      </span>
      <span class="flex items-center gap-2 text-xs">
        <span class="text-muted-foreground w-24 shrink-0">Above kill line</span>
        <span class="bg-muted h-2 flex-1 overflow-hidden rounded-full"
          ><span
            class={cn(
              "block h-full",
              room < 0.25 ? "bg-destructive" : "bg-success",
            )}
            style="width:{Math.min(1, room) * 100}%"
          ></span></span
        >
      </span>
      <span class="flex items-center gap-3 text-xs">
        <span class="flex items-center gap-1"
          ><span
            class="size-1.5 rounded-full"
            style="background: var(--tone-live)"
          ></span>{p.mode === "LIVE" ? usd(p.equity) : "not live yet"}</span
        >
        <span class="flex items-center gap-1"
          ><span
            class="size-1.5 rounded-full"
            style="background: var(--tone-paper)"
          ></span>{usd(p.paper.equity)}</span
        >
      </span>
      <span class="text-muted-foreground text-xs"
        >{accountById(p.account)?.name} · {p.bots.length} bot{p.bots.length ===
        1
          ? ""
          : "s"}</span
      >
    </button>
  {/each}
  <button
    type="button"
    class="hover:border-ring text-muted-foreground hover:text-foreground flex min-h-44 flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed text-sm"
    onclick={() => (portfolio.templatesOpen = true)}
    ><Plus class="size-5" />New pod from a template</button
  >
</div>
