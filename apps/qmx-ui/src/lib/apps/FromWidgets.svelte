<script lang="ts">
  /**
   * Make an app from widgets you already have (operator 2026-10-03:
   * "combine certain functionalities from portfolio ... create a mini
   * app"). Pick widgets from Home and Portfolio, name it, and it starts on
   * the road at Build with a screen you can open and rearrange at once.
   */
  import { goto } from "$app/navigation";
  import { resolve } from "$app/paths";
  import * as Dialog from "$lib/components/ui/dialog";
  import { Button } from "$lib/components/ui/button";
  import { Input } from "$lib/components/ui/input";
  import { cn } from "$lib/utils";
  import { WIDGETS, apps } from "./apps.svelte";

  let { open = $bindable(false) }: { open?: boolean } = $props();

  let name = $state("");
  let picked = $state<string[]>([]);
  const groups = ["Portfolio", "Home"].map((from) => ({
    from,
    list: Object.entries(WIDGETS).filter(([, w]) => w.from === from),
  }));

  function flip(id: string) {
    picked = picked.includes(id)
      ? picked.filter((p) => p !== id)
      : [...picked, id];
  }
  function create() {
    const id = apps.fromWidgets(name.trim() || "My app", picked);
    open = false;
    name = "";
    picked = [];
    goto(resolve("/apps/[id]", { id }));
  }
</script>

<Dialog.Root bind:open>
  <Dialog.Content class="max-h-[88vh] overflow-auto sm:max-w-3xl">
    <Dialog.Header>
      <Dialog.Title class="text-2xl">Make an app from widgets</Dialog.Title>
      <Dialog.Description class="text-base">
        Pick what it should show. You can rearrange it as soon as it opens, and
        ask the copilot to add anything the widgets don't do.
      </Dialog.Description>
    </Dialog.Header>
    <label class="mt-2 flex flex-col gap-1.5">
      <span class="font-medium">Name</span>
      <Input
        bind:value={name}
        placeholder="My morning desk"
        class="text-base"
      />
    </label>
    {#each groups as g (g.from)}
      <section class="mt-4">
        <h3 class="mb-2 font-semibold">From {g.from}</h3>
        <ul class="grid gap-2 sm:grid-cols-2">
          {#each g.list as [id, w] (id)}
            {@const on = picked.includes(id)}
            {@const Icon = w.icon}
            <li>
              <button
                type="button"
                aria-pressed={on}
                class={cn(
                  "flex w-full items-start gap-3 rounded-xl border p-3 text-left",
                  on ? "border-primary bg-primary/10" : "hover:bg-muted/50",
                )}
                onclick={() => flip(id)}
              >
                <Icon class="text-primary mt-0.5 size-5 shrink-0" />
                <span>
                  <span class="block font-medium">{w.title}</span>
                  <span class="text-muted-foreground text-sm">{w.note}</span>
                </span>
              </button>
            </li>
          {/each}
        </ul>
      </section>
    {/each}
    <Dialog.Footer class="mt-4 items-center gap-3">
      <span class="text-muted-foreground mr-auto"
        >{picked.length} picked · it starts at Build, shows things only</span
      >
      <Button disabled={!picked.length} onclick={create}>Make it</Button>
    </Dialog.Footer>
  </Dialog.Content>
</Dialog.Root>
