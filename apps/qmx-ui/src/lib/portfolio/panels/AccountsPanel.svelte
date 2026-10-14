<script lang="ts">
  /**
   * Brokers and exchanges → accounts → pods, with each account's kill-switch
   * level. Compact (a narrow rail) shows names and pods; regular adds money
   * and the server each trades from; expanded adds CFD margin.
   */
  import Plus from "@lucide/svelte/icons/plus";
  import { cn } from "$lib/utils";
  import InfoTip from "$lib/workbench/InfoTip.svelte";
  import { panelSize } from "$lib/workbench/tiles/panel-size";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { ACCOUNTS, PODS, VENUES, nodeById } from "../demo";
  import { KSA_TONE, pct, usd } from "../bits";
  import { portfolio } from "../portfolio.svelte";
  import { podSim } from "../pod-sim.svelte";

  const size = panelSize();
  const shown = (role: string) =>
    portfolio.world === "all" ||
    (portfolio.world === "live" ? role === "live" : role === "paper");
  const accounts = $derived(
    ACCOUNTS.filter((a) => shown(a.role) || a.role === "watch"),
  );
  const total = $derived(accounts.reduce((n, a) => n + a.equity, 0));
</script>

<div class="flex h-full flex-col">
  <div class="px-panel flex h-11 shrink-0 items-center gap-2">
    <span class="min-w-0">
      <span class="num block truncate text-base font-semibold"
        >{usd(total)}</span
      >
    </span>
    {#if size.mode !== "compact"}<span
        class="text-muted-foreground shrink-0 text-xs"
        >{accounts.length} accounts</span
      >{/if}
    <InfoTip
      class="ml-auto"
      label="Explain accounts"
      text="Every broker and exchange, its accounts and the pods trading in each. The dot is the account's kill-switch level. Click a pod to steer it in the Pod panel."
    />
  </div>
  <div class="px-panel min-h-0 flex-1 overflow-auto">
    {#each VENUES as v (v.id)}
      {@const accts = accounts.filter((a) => a.venue === v.id)}
      {#if accts.length}
        <section class="pb-row">
          <p
            class="text-muted-foreground pt-row truncate text-xs"
            title={v.market}
          >
            <span class="text-foreground font-medium">{v.name}</span>
            {v.via}
          </p>
          {#each accts as a (a.id)}
            <div class="py-row">
              <div class="flex items-center gap-2 text-sm">
                <span
                  class={cn("size-2 shrink-0 rounded-full", KSA_TONE[a.ksa])}
                  title={`Kill switch ${a.ksa}`}
                ></span>
                <span class="min-w-0 flex-1 truncate">{a.name}</span>
                {#if size.mode !== "compact"}
                  <span class="num shrink-0 text-xs">{usd(a.equity)}</span>
                  <span
                    class={cn(
                      "num w-12 shrink-0 text-right text-xs",
                      a.today >= 0 ? "text-success" : "text-destructive",
                    )}>{pct(a.today)}</span
                  >
                {/if}
              </div>
              {#if size.mode === "expanded"}
                <p class="text-muted-foreground truncate pl-4 text-xs">
                  {a.role} · {nodeById(a.node)?.name}{#if a.margin}
                    · margin {usd(a.margin.used)} · up to 1:{a.margin
                      .leverage}{/if}
                </p>
              {/if}
              <ul class="pl-3">
                {#each PODS.filter((p) => p.account === a.id) as p (p.id)}
                  <li>
                    <button
                      type="button"
                      class={cn(
                        "hover:bg-muted flex w-full items-center gap-2 rounded px-1.5 py-0.5 text-left text-xs",
                        portfolio.pod === p.id && "bg-primary/12",
                      )}
                      onclick={() => (portfolio.pod = p.id)}
                    >
                      <span
                        class="h-3 w-0.5 shrink-0 rounded-full"
                        style="background: var(--tone-{p.mode === 'LIVE'
                          ? 'live'
                          : 'paper'})"
                      ></span>
                      <span class="truncate">{p.name}</span>
                      {#if podSim.view(p.id).paused}<span
                          class="text-warning ml-auto">Paused</span
                        >{/if}
                    </button>
                  </li>
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
    class="text-muted-foreground hover:text-foreground px-panel flex h-9 shrink-0 items-center gap-1.5 border-t text-xs"
    onclick={() =>
      workbench.notify(
        "Connecting a broker or exchange needs the daemon. Keys stay in your credential store; trade-only keys, never withdrawal.",
      )}><Plus class="size-3.5" />Connect</button
  >
</div>
