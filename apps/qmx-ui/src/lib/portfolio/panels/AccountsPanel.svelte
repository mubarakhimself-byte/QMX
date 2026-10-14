<script lang="ts">
  /** Brokers and exchanges → accounts → pods, with the server each trades from and its kill-switch level. CFD accounts show the margin in use. */
  import Plus from "@lucide/svelte/icons/plus";
  import { cn } from "$lib/utils";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { ACCOUNTS, PODS, VENUES, nodeById } from "../demo";
  import { KSA_TONE, pct, usd } from "../bits";
  import { portfolio } from "../portfolio.svelte";

  const shown = (role: string) =>
    portfolio.world === "all" ||
    (portfolio.world === "live" ? role === "live" : role === "paper");
</script>

<div class="flex h-full flex-col">
  <div class="min-h-0 flex-1 overflow-auto py-1">
    {#each VENUES as v (v.id)}
      {@const accts = ACCOUNTS.filter(
        (a) => a.venue === v.id && (shown(a.role) || a.role === "watch"),
      )}
      {#if accts.length}
        <section class="pb-1">
          <p class="flex items-baseline gap-1.5 px-3 pt-2 pb-1 text-xs">
            <span class="font-medium">{v.name}</span><span
              class="text-muted-foreground truncate"
              title={`${v.via} · ${v.market}`}>{v.via} · {v.market}</span
            >
          </p>
          {#each accts as a (a.id)}
            <div class="px-3 pb-1.5">
              <div class="flex items-center gap-2 text-sm">
                <span
                  class={cn("size-2 shrink-0 rounded-full", KSA_TONE[a.ksa])}
                  title={`Kill switch ${a.ksa}`}
                ></span>
                <span class="truncate">{a.name}</span>
                <span class="text-muted-foreground ml-auto text-xs"
                  >{a.role}</span
                >
              </div>
              <div
                class="text-muted-foreground flex items-center gap-2 pl-4 text-xs"
              >
                <span class="num text-foreground">{usd(a.equity)}</span>
                {#if a.margin}<span
                    class="num"
                    title={`Margin in use, leverage up to 1:${a.margin.leverage}`}
                    >margin {usd(a.margin.used)}</span
                  >{/if}
                <span
                  class={cn(
                    "num",
                    a.today >= 0 ? "text-success" : "text-destructive",
                  )}>{pct(a.today)}</span
                >
                <span class="ml-auto">{a.quote} · {nodeById(a.node)?.name}</span
                >
              </div>
              <ul class="mt-1 pl-3">
                {#each PODS.filter((p) => p.account === a.id) as p (p.id)}
                  <li>
                    <button
                      type="button"
                      class={cn(
                        "hover:bg-muted flex w-full items-center gap-2 rounded px-1.5 py-1 text-left text-xs",
                        portfolio.pod === p.id && "bg-primary/12",
                      )}
                      onclick={() => (portfolio.pod = p.id)}
                    >
                      <span
                        class="h-3 w-0.5 rounded-full"
                        style="background: var(--tone-{p.mode === 'LIVE'
                          ? 'live'
                          : 'paper'})"
                      ></span>
                      {p.name}
                    </button>
                  </li>
                {:else}
                  {#if a.role === "watch"}<li
                      class="text-muted-foreground px-1.5 text-xs"
                    >
                      Watching only
                    </li>{/if}
                {/each}
              </ul>
            </div>
          {/each}
        </section>
      {/if}
    {/each}
  </div>
  <button
    type="button"
    class="text-muted-foreground hover:text-foreground flex h-9 shrink-0 items-center gap-1.5 border-t px-3 text-xs"
    onclick={() =>
      workbench.notify(
        "Connecting a broker or exchange needs the daemon. Keys stay in your credential store; trade-only keys, never withdrawal.",
      )}><Plus class="size-3.5" />Connect a broker or exchange</button
  >
</div>
