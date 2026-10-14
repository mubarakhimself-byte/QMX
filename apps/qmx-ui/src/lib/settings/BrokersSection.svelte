<script lang="ts">
  /**
   * Brokers and accounts (operator, 2026-10-07): CFDs through cTrader at IC
   * Markets beside crypto exchanges through CCXT, several accounts each, each
   * live, demo (paper) or watch-only and tied to the server that trades it.
   * Keys never enter QMX's own files: the daemon hands them to the operating
   * system's credential store (Windows Credential Manager here), and trading
   * keys must have withdrawals off. No prop firms.
   */
  import Plus from "@lucide/svelte/icons/plus";
  import KeyRound from "@lucide/svelte/icons/key-round";
  import { Button } from "$lib/components/ui/button";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { ACCOUNTS, NODES, VENUES, type Venue } from "$lib/portfolio/demo";
  import { usd } from "$lib/portfolio/bits";

  const GROUPS: {
    via: Venue["via"];
    title: string;
    note: string;
    more: string[];
  }[] = [
    {
      via: "cTrader",
      title: "CFD brokers (cTrader)",
      note: "FX, indices, metals and energy, traded on margin.",
      more: ["Pepperstone", "FxPro", "Fusion Markets"],
    },
    {
      via: "CCXT",
      title: "Crypto exchanges (CCXT)",
      note: "Spot crypto.",
      more: ["OKX", "Bitget", "KuCoin", "Gate.io"],
    },
  ];
  const ROLE = {
    live: "color: var(--tone-live)",
    paper: "color: var(--tone-paper)",
    watch: "color: var(--muted-foreground)",
  };
  const roleLabel = (role: "live" | "paper" | "watch", via: Venue["via"]) =>
    role === "live"
      ? "Live"
      : role === "watch"
        ? "Watch only"
        : via === "cTrader"
          ? "Demo (paper)"
          : "Paper (testnet)";
  const need = (what: string) =>
    workbench.notify(
      `${what} needs the daemon; keys go straight to the system credential store.`,
    );
</script>

<div class="flex flex-col gap-8">
  <p class="text-muted-foreground max-w-2xl">
    Add as many accounts as you like with each broker or exchange. Keys are
    never stored by QMX itself: they go to this computer's credential store, and
    trading keys must have withdrawals switched off.
  </p>
  {#each GROUPS as g (g.via)}
    <div class="flex flex-col gap-4">
      <div>
        <h3 class="text-xl font-semibold">{g.title}</h3>
        <p class="text-muted-foreground">{g.note}</p>
      </div>
      {#each VENUES.filter((v) => v.via === g.via) as v (v.id)}
        {@const accounts = ACCOUNTS.filter((a) => a.venue === v.id)}
        <section class="solid-backing rounded-2xl border p-5">
          <div class="flex flex-wrap items-center gap-x-3 gap-y-1">
            <h4 class="text-lg font-semibold">{v.name}</h4>
            <span class="text-muted-foreground">{v.market}</span>
            <Button
              size="sm"
              variant="outline"
              class="ml-auto"
              onclick={() => need(`Adding a ${v.name} account`)}
              ><Plus />Add account</Button
            >
          </div>
          <ul class="mt-3 flex flex-col">
            {#each accounts as a (a.id)}
              <li
                class="flex flex-wrap items-center gap-x-6 gap-y-1 border-t py-3"
              >
                <span class="min-w-44 font-medium">{a.name}</span>
                <span class="w-36" style={ROLE[a.role]}
                  >{roleLabel(a.role, v.via)}</span
                >
                <span class="text-muted-foreground w-40"
                  >Traded by {NODES.find((n) => n.id === a.node)?.name}</span
                >
                {#if a.margin}
                  <span class="text-muted-foreground w-52"
                    >Margin <span class="num text-foreground"
                      >{usd(a.margin.used)}</span
                    >
                    · up to 1:{a.margin.leverage}</span
                  >
                {/if}
                <span class="text-muted-foreground flex items-center gap-1.5"
                  ><KeyRound class="size-4" />Key in the credential store</span
                >
                <Button
                  size="sm"
                  variant="ghost"
                  class="ml-auto"
                  onclick={() => need(`Testing ${a.name}`)}
                  >Test connection</Button
                >
              </li>
            {/each}
          </ul>
        </section>
      {/each}
      <DropdownMenu.Root>
        <DropdownMenu.Trigger>
          {#snippet child({ props })}
            <Button {...props} variant="outline" class="w-fit"
              ><Plus />{g.via === "cTrader"
                ? "Connect another broker"
                : "Connect another exchange"}</Button
            >
          {/snippet}
        </DropdownMenu.Trigger>
        <DropdownMenu.Content class="w-56">
          {#each g.more as m (m)}
            <DropdownMenu.Item onclick={() => need(`Connecting ${m}`)}
              >{m}</DropdownMenu.Item
            >
          {/each}
        </DropdownMenu.Content>
      </DropdownMenu.Root>
    </div>
  {/each}
</div>
