<script lang="ts">
  /**
   * Exchanges and accounts (spot crypto only). Several accounts per
   * exchange, each live, paper (testnet) or watch-only, each tied to the
   * server that trades it. Keys never enter QMX's own files: the daemon
   * hands them to the operating system's credential store (Windows
   * Credential Manager here), and trading keys must have withdrawals off.
   */
  import Plus from "@lucide/svelte/icons/plus";
  import KeyRound from "@lucide/svelte/icons/key-round";
  import { Button } from "$lib/components/ui/button";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { ACCOUNTS, NODES, VENUES } from "$lib/portfolio/demo";

  const MORE = ["OKX", "Bitget", "KuCoin", "Gate.io"];
  const ROLE = {
    live: "color: var(--tone-live)",
    paper: "color: var(--tone-paper)",
    watch: "color: var(--muted-foreground)",
  };
  const ROLE_LABEL = {
    live: "Live",
    paper: "Paper (testnet)",
    watch: "Watch only",
  };
  const need = (what: string) =>
    workbench.notify(
      `${what} needs the daemon; keys go straight to the system credential store.`,
    );
</script>

<div class="flex flex-col gap-6">
  <p class="text-muted-foreground max-w-2xl">
    Spot crypto only. Add as many accounts as you like on each exchange. Keys
    are never stored by QMX itself: they go to this computer's credential store,
    and trading keys must have withdrawals switched off.
  </p>
  {#each VENUES as v (v.id)}
    {@const accounts = ACCOUNTS.filter((a) => a.venue === v.id)}
    <section class="solid-backing rounded-2xl border p-5">
      <div class="flex items-center gap-3">
        <h3 class="text-lg font-semibold">{v.name}</h3>
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
          <li class="flex flex-wrap items-center gap-x-6 gap-y-1 border-t py-3">
            <span class="min-w-48 font-medium">{a.name}</span>
            <span class="w-36" style={ROLE[a.role]}>{ROLE_LABEL[a.role]}</span>
            <span class="text-muted-foreground w-44"
              >Traded by {NODES.find((n) => n.id === a.node)?.name}</span
            >
            <span class="text-muted-foreground flex items-center gap-1.5"
              ><KeyRound class="size-4" />Key in the credential store</span
            >
            <Button
              size="sm"
              variant="ghost"
              class="ml-auto"
              onclick={() => need(`Testing ${a.name}`)}>Test connection</Button
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
          ><Plus />Connect another exchange</Button
        >
      {/snippet}
    </DropdownMenu.Trigger>
    <DropdownMenu.Content class="w-56">
      {#each MORE as m (m)}
        <DropdownMenu.Item onclick={() => need(`Connecting ${m}`)}
          >{m}</DropdownMenu.Item
        >
      {/each}
    </DropdownMenu.Content>
  </DropdownMenu.Root>
</div>
