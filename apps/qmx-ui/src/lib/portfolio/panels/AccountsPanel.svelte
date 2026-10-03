<script lang="ts">
  /**
   * Venues → accounts → Books, with the node each account trades from and its
   * kill-switch level. Click a Book to select it everywhere linked.
   */
  import ChevronRight from "@lucide/svelte/icons/chevron-right";
  import Plus from "@lucide/svelte/icons/plus";
  import { cn } from "$lib/utils";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { ACCOUNTS, BOOKS, VENUES, nodeById } from "../demo";
  import { KSA_TONE, pct, usd } from "../bits";
  import { portfolio } from "../portfolio.svelte";

  let closed = $state<string[]>([]);
  const shown = (role: string) =>
    portfolio.world === "all" ||
    (portfolio.world === "live"
      ? role === "live" || role === "prop-firm"
      : role === "demo");
</script>

<div class="flex h-full flex-col">
  <div class="min-h-0 flex-1 overflow-auto py-1">
    {#each VENUES as v (v.id)}
      {@const accts = ACCOUNTS.filter((a) => a.venue === v.id && shown(a.role))}
      {#if accts.length}
        <section>
          <button
            type="button"
            class="flex h-8 w-full items-center gap-1 px-2 text-left text-xs"
            aria-expanded={!closed.includes(v.id)}
            onclick={() =>
              (closed = closed.includes(v.id)
                ? closed.filter((c) => c !== v.id)
                : [...closed, v.id])}
          >
            <ChevronRight
              class={cn(
                "text-muted-foreground size-3.5 transition-transform",
                !closed.includes(v.id) && "rotate-90",
              )}
            />
            <span class="font-medium">{v.name}</span>
            <span class="text-muted-foreground">{v.platform}</span>
          </button>
          {#if !closed.includes(v.id)}
            {#each accts as a (a.id)}
              <div class="pr-2 pl-6">
                <div class="flex items-center gap-2 py-1 text-sm">
                  <span
                    class={cn("size-2 shrink-0 rounded-full", KSA_TONE[a.ksa])}
                    title={`Kill switch ${a.ksa}`}
                  ></span>
                  <span class="truncate">{a.name}</span>
                  <span class="text-muted-foreground ml-auto shrink-0 text-xs"
                    >{a.role}</span
                  >
                </div>
                <div
                  class="text-muted-foreground flex items-center gap-2 pb-1 pl-4 text-xs"
                >
                  <span class="num">{usd(a.equity)}</span>
                  <span
                    class={cn(
                      "num",
                      a.today >= 0 ? "text-success" : "text-destructive",
                    )}>{pct(a.today)}</span
                  >
                  <span class="ml-auto truncate">{nodeById(a.node)?.name}</span>
                </div>
                {#if a.settles !== "USD"}
                  <p class="text-warning pb-1 pl-4 text-[11px]">
                    Settles in {a.settles}: needs a ruling (docs require USD)
                  </p>
                {/if}
                <ul class="pb-1 pl-4">
                  {#each BOOKS.filter((b) => b.account === a.id) as b (b.id)}
                    <li>
                      <button
                        type="button"
                        class={cn(
                          "hover:bg-muted flex w-full items-center gap-2 rounded px-1.5 py-1 text-left text-xs",
                          portfolio.book === b.id && "bg-primary/12",
                        )}
                        onclick={() => (portfolio.book = b.id)}
                      >
                        <span
                          class={cn(
                            "h-3 w-0.5 rounded-full",
                            b.mode === "LIVE"
                              ? "bg-[var(--tone-live)]"
                              : "bg-[var(--tone-paper)]",
                          )}
                        ></span>
                        {b.name}
                        <span class="text-muted-foreground ml-auto"
                          >{b.binding}</span
                        >
                      </button>
                    </li>
                  {:else}
                    {#if a.role === "sensing-only"}<li
                        class="text-muted-foreground px-1.5 text-xs"
                      >
                        Watch only: no Book trades here
                      </li>{/if}
                  {/each}
                </ul>
              </div>
            {/each}
          {/if}
        </section>
      {/if}
    {/each}
  </div>
  <button
    type="button"
    class="text-muted-foreground hover:text-foreground flex h-9 shrink-0 items-center gap-1.5 border-t px-3 text-xs"
    onclick={() =>
      workbench.notify(
        "Connecting an exchange or broker needs the daemon. Keys stay in your credential store.",
      )}><Plus class="size-3.5" />Connect an exchange or broker</button
  >
</div>
