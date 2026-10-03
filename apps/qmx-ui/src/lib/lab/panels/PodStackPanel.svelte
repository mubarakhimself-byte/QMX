<script lang="ts">
  /**
   * A pod as a stack: seven slots in a fixed order, each holding blocks.
   * Add, remove and pick blocks; nothing to wire. The kill line is
   * required. Edits make a draft; saving mints a new version; "Send to
   * paper" runs the checklist and hands the wiring to the copilot to draft
   * for your signature.
   */
  import Plus from "@lucide/svelte/icons/plus";
  import X from "@lucide/svelte/icons/x";
  import Workflow from "@lucide/svelte/icons/workflow";
  import Code from "@lucide/svelte/icons/code";
  import BrainCircuit from "@lucide/svelte/icons/brain-circuit";
  import Send from "@lucide/svelte/icons/send";
  import Undo2 from "@lucide/svelte/icons/undo-2";
  import { Button } from "$lib/components/ui/button";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu";
  import { cn } from "$lib/utils";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { BLOCKS, LAB_PODS, SLOTS, blockById, type SlotId } from "../pods";
  import { lab } from "../lab.svelte";

  let drafts = $state<Record<string, Record<SlotId, string[]>>>({});
  const pod = $derived(
    LAB_PODS.find((p) => p.id === lab.labPod) ?? LAB_PODS[0],
  );
  const stack = $derived(drafts[pod.id] ?? pod.stack);
  const dirty = $derived(!!drafts[pod.id]);
  const next = $derived(pod.version.replace(/\d+/, (n) => String(+n + 1)));
  const KIND_ICON = {
    form: null,
    graph: Workflow,
    code: Code,
    model: BrainCircuit,
  };

  function edit(slot: SlotId, list: string[]) {
    drafts[pod.id] = { ...stack, [slot]: list };
  }
  const CHECKS = [
    "Full rerun done",
    "Monte Carlo done",
    "Stress battery done",
    "No blank settings",
    "Kill line set",
  ];
</script>

<div class="flex h-full flex-col">
  <div class="flex h-10 shrink-0 items-center gap-1 border-b px-2">
    {#each LAB_PODS as p (p.id)}
      <button
        type="button"
        class={cn(
          "flex h-7 items-center gap-1.5 rounded-md px-2.5 text-sm",
          lab.labPod === p.id
            ? "bg-muted font-medium"
            : "text-muted-foreground hover:text-foreground",
        )}
        aria-pressed={lab.labPod === p.id}
        onclick={() => (lab.labPod = p.id)}
        ><span class="size-2 rounded-full" style="background:{p.color}"
        ></span>{p.name}</button
      >
    {/each}
    <span class="text-muted-foreground ml-auto text-xs"
      >{pod.version} · from {pod.template}</span
    >
  </div>
  <ol class="min-h-0 flex-1 overflow-auto p-2">
    {#each SLOTS as s, i (s.id)}
      <li class="flex items-start gap-3 rounded-lg px-2 py-2 hover:bg-muted/30">
        <span class="text-muted-foreground num mt-1 w-4 text-xs">{i + 1}</span>
        <div class="w-28 shrink-0">
          <p class="text-sm font-medium">{s.label}</p>
          <p class="text-muted-foreground text-[11px] leading-tight">
            {s.note}
          </p>
        </div>
        <div class="flex min-w-0 flex-1 flex-wrap items-center gap-1.5">
          {#each stack[s.id] as id (id)}
            {@const b = blockById(id)}
            {#if b}
              {@const Icon = KIND_ICON[b.kind]}
              <span
                class={cn(
                  "group flex items-center rounded-lg border text-sm",
                  lab.block === id
                    ? "border-primary bg-primary/12"
                    : "bg-background/40 hover:border-ring/60",
                )}
              >
                <button
                  type="button"
                  class="flex items-center gap-1.5 py-1 pr-1 pl-2.5 text-left"
                  onclick={() => (lab.block = id)}
                >
                  {#if Icon}<Icon class="text-info size-3.5" />{/if}
                  <span>{b.name}</span>
                  <span class="text-muted-foreground num text-xs"
                    >{b.setting}</span
                  >
                </button>
                {#if !b.required}
                  <button
                    type="button"
                    class="text-muted-foreground hover:text-destructive px-1.5 py-1"
                    aria-label={`Remove ${b.name}`}
                    onclick={() =>
                      edit(
                        s.id,
                        stack[s.id].filter((x) => x !== id),
                      )}><X class="size-3.5" /></button
                  >
                {:else}
                  <span class="text-muted-foreground px-1.5 text-[10px]"
                    >required</span
                  >
                {/if}
              </span>
            {/if}
          {:else}
            <span class="text-muted-foreground text-xs italic"
              >{s.id === "allocator"
                ? "Single bot: not needed"
                : "Nothing yet"}</span
            >
          {/each}
          <DropdownMenu.Root>
            <DropdownMenu.Trigger
              class="text-muted-foreground hover:text-foreground hover:bg-muted flex size-7 items-center justify-center rounded-md border border-dashed"
              aria-label={`Add to ${s.label}`}
            >
              <Plus class="size-3.5" />
            </DropdownMenu.Trigger>
            <DropdownMenu.Content class="w-72">
              <DropdownMenu.Label>{s.label}</DropdownMenu.Label>
              {#each BLOCKS.filter((b) => b.slot === s.id && !stack[s.id].includes(b.id)) as b (b.id)}
                <DropdownMenu.Item
                  onclick={() => {
                    edit(s.id, [...stack[s.id], b.id]);
                    lab.block = b.id;
                  }}
                >
                  <span class="flex flex-col"
                    ><span>{b.name}</span><span
                      class="text-muted-foreground text-xs">{b.what}</span
                    ></span
                  >
                </DropdownMenu.Item>
              {/each}
              <DropdownMenu.Separator />
              <DropdownMenu.Item
                onclick={() =>
                  workbench.notify(
                    "A new graph block opens in the editor with this slot's inputs and outputs placed. Agent and approval steps aren't allowed in money blocks.",
                  )}><Workflow />New block as a graph</DropdownMenu.Item
              >
              <DropdownMenu.Item
                onclick={() =>
                  workbench.notify(
                    "A Python stub with this slot's signature opens in the code editor.",
                  )}><Code />New block as code</DropdownMenu.Item
              >
              <DropdownMenu.Item
                onclick={() =>
                  workbench.notify(
                    "Pick or import a model; it plugs into this slot under a rule ceiling.",
                  )}><BrainCircuit />Use a model</DropdownMenu.Item
              >
            </DropdownMenu.Content>
          </DropdownMenu.Root>
        </div>
      </li>
    {/each}
    <li class="flex items-center gap-3 px-2 py-2 opacity-70">
      <span class="num text-muted-foreground w-4 text-xs">8</span>
      <div class="w-28 shrink-0">
        <p class="text-sm font-medium">Venue fit</p>
        <p class="text-muted-foreground text-[11px]">Always last</p>
      </div>
      <span class="text-muted-foreground text-xs"
        >Rounds to the exchange's lot size and minimum order, adds fees, refuses
        dust.</span
      >
    </li>
  </ol>
  <div class="flex shrink-0 flex-wrap items-center gap-2 border-t px-3 py-2">
    {#if dirty}
      <span class="text-sm font-medium">Draft {next}</span>
      <Button size="sm" variant="ghost" onclick={() => delete drafts[pod.id]}
        ><Undo2 />Discard</Button
      >
      <Button
        size="sm"
        variant="outline"
        onclick={() => {
          delete drafts[pod.id];
          workbench.notify(
            `${pod.name} ${next} saved. Test it before sending to paper.`,
          );
        }}>Save {next}</Button
      >
    {/if}
    <DropdownMenu.Root>
      <DropdownMenu.Trigger>
        {#snippet child({ props })}
          <Button {...props} size="sm" class="ml-auto"
            ><Send />Send to paper</Button
          >
        {/snippet}
      </DropdownMenu.Trigger>
      <DropdownMenu.Content align="end" class="w-72">
        <DropdownMenu.Label>Before it goes to paper</DropdownMenu.Label>
        {#each CHECKS as c, i (c)}
          <DropdownMenu.Item disabled class="opacity-100"
            ><span
              class={cn(
                "size-2 rounded-full",
                i < 3 ? "bg-success" : "bg-success",
              )}
            ></span>{c}</DropdownMenu.Item
          >
        {/each}
        <DropdownMenu.Separator />
        <DropdownMenu.Item
          onclick={() =>
            workbench.notify(
              `The copilot drafts ${pod.name}'s wiring (bots, exchange sub-account, capital) for your signature; then it soaks on paper for 7 days.`,
            )}><Send />Draft the wiring for my signature</DropdownMenu.Item
        >
      </DropdownMenu.Content>
    </DropdownMenu.Root>
  </div>
</div>
