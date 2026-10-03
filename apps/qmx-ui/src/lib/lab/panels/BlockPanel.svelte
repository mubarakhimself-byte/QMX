<script lang="ts">
  /** The selected block: what it does, its settings with live values, where it stands in the docs, and how it's built. */
  import Workflow from "@lucide/svelte/icons/workflow";
  import { Button } from "$lib/components/ui/button";
  import { Slider } from "$lib/components/ui/slider";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { SLOTS, blockById } from "../pods";
  import { lab } from "../lab.svelte";

  const b = $derived(blockById(lab.block));
  let strength = $state(50);
  const DOCS = {
    yes: "In the docs",
    partial: "Partly in the docs",
    new: "New scope",
  };
</script>

{#if b}
  <div class="flex h-full flex-col gap-4 overflow-auto p-4">
    <div>
      <p class="text-muted-foreground text-xs">
        {SLOTS.find((s) => s.id === b.slot)?.label} · {b.kind === "form"
          ? "built-in"
          : b.kind}
      </p>
      <h3 class="text-xl font-semibold">{b.name}</h3>
      <p class="text-muted-foreground text-sm">{b.what}</p>
    </div>
    <div class="rounded-xl border p-3">
      <div class="flex items-baseline justify-between">
        <span class="text-sm">Setting</span>
        <span class="num text-xl font-semibold">{b.setting}</span>
      </div>
      <Slider
        class="mt-3"
        type="single"
        min={0}
        max={100}
        step={5}
        value={strength}
        onValueChange={(v: number) => (strength = v)}
        aria-label={`${b.name} setting`}
      />
      <p class="text-muted-foreground mt-2 text-xs">
        Live input now: 30-day volatility 41% · drawdown −3.1%
      </p>
    </div>
    <div class="flex items-center gap-2 text-xs">
      <span class="rounded-md border px-2 py-0.5">{DOCS[b.docs]}</span>
      {#if b.required}<span class="text-muted-foreground"
          >Every pod needs this block.</span
        >{/if}
    </div>
    {#if b.kind === "graph" || b.kind === "code"}
      <Button
        size="sm"
        variant="outline"
        onclick={() =>
          workbench.notify(`${b.name} opens in the editor (Build layout).`)}
        ><Workflow />Open in the editor</Button
      >
    {/if}
    <p class="text-muted-foreground mt-auto text-xs">
      Blocks are pure: same inputs, same answer, no network or clock. That's
      what makes replays exact.
    </p>
  </div>
{/if}
