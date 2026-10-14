<script lang="ts">
  /**
   * Start a pod from a template. Every value stays editable; the new pod
   * begins on a paper account and reaches live only through the road to
   * live. Building your own happens in the Lab.
   */
  import { goto } from "$app/navigation";
  import { resolve } from "$app/paths";
  import * as Dialog from "$lib/components/ui/dialog";
  import { Button } from "$lib/components/ui/button";
  import { cn } from "$lib/utils";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { ACCOUNTS, TEMPLATES } from "./demo";
  import { portfolio } from "./portfolio.svelte";

  let pick = $state(TEMPLATES[0].id);
  let account = $state("bn-test");
  const t = $derived(TEMPLATES.find((x) => x.id === pick)!);
</script>

<Dialog.Root bind:open={portfolio.templatesOpen}>
  <Dialog.Content class="max-h-[90vh] overflow-y-auto sm:max-w-3xl">
    <Dialog.Header>
      <Dialog.Title>New pod from a template</Dialog.Title>
      <Dialog.Description
        >Every value stays editable. It starts on paper and goes live only
        through the road to live.</Dialog.Description
      >
    </Dialog.Header>
    <div class="grid gap-2 sm:grid-cols-3">
      {#each TEMPLATES as x (x.id)}
        <button
          type="button"
          class={cn(
            "rounded-xl border p-3 text-left",
            pick === x.id
              ? "border-primary bg-primary/12"
              : "hover:border-ring/60",
          )}
          onclick={() => (pick = x.id)}
        >
          <span class="block text-sm font-semibold">{x.name}</span>
          <span class="text-muted-foreground mt-1 block text-xs">{x.note}</span>
        </button>
      {/each}
    </div>
    <label class="grid gap-1 text-sm">
      <span class="font-medium">Paper account</span>
      <select bind:value={account} class="h-9 rounded-md border px-2 text-sm">
        {#each ACCOUNTS.filter((a) => a.role === "paper") as a (a.id)}<option
            value={a.id}>{a.name}</option
          >{/each}
      </select>
    </label>
    <Dialog.Footer class="gap-2">
      <Button
        variant="ghost"
        onclick={() => {
          portfolio.templatesOpen = false;
          // eslint-disable-next-line svelte/no-navigation-without-resolve -- resolved path plus a query string
          goto(`${resolve("/copilot")}?start=workflow`);
        }}>Build my own in the Lab</Button
      >
      <Button
        onclick={() => {
          if (t.id === "t-own") {
            portfolio.templatesOpen = false;
            goto(resolve("/lab"));
            return;
          }
          portfolio.templatesOpen = false;
          workbench.notify(
            `${t.name} drafted on ${ACCOUNTS.find((a) => a.id === account)?.name}. Creating it needs the trading server.`,
          );
        }}>Create {t.name}</Button
      >
    </Dialog.Footer>
  </Dialog.Content>
</Dialog.Root>
