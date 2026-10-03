<script lang="ts">
  /**
   * Thin strips under the Lab header: connecting to a machine (with each
   * check), why a connection failed, and the copilot's guided walk through
   * the layouts (it switches layouts as it goes).
   */
  import Check from "@lucide/svelte/icons/check";
  import Loader from "@lucide/svelte/icons/loader-circle";
  import TriangleAlert from "@lucide/svelte/icons/triangle-alert";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import X from "@lucide/svelte/icons/x";
  import { Button } from "$lib/components/ui/button";
  import { envById } from "./demo";
  import { lab } from "./lab.svelte";

  const CHECKS = ["Reachable", "Signed in", "Healthy"];
</script>

{#if lab.connection}
  {@const c = lab.connection}
  {@const env = envById(c.target)}
  <div
    class="flex h-9 shrink-0 items-center gap-4 border-b px-3 text-xs {c.failed
      ? 'bg-destructive/10'
      : 'bg-info/8'}"
    role="status"
  >
    {#if c.failed}
      <TriangleAlert class="text-destructive size-4" />
      <span>{c.failed}</span>
      <Button
        variant="ghost"
        size="sm"
        class="ml-auto h-7"
        onclick={() => (lab.connection = null)}>Dismiss</Button
      >
    {:else}
      <span class="font-medium">Connecting to {env?.name}</span>
      {#each CHECKS as label, i (label)}
        <span class="flex items-center gap-1.5">
          {#if i < c.step}<Check
              class="text-success size-3.5"
            />{:else if i === c.step}<Loader
              class="text-info size-3.5 animate-spin motion-reduce:animate-none"
            />{:else}<span
              class="border-muted-foreground/40 size-3 rounded-full border"
            ></span>{/if}
          <span class={i <= c.step ? "" : "text-muted-foreground"}>{label}</span
          >
        </span>
      {/each}
      <button
        type="button"
        class="text-muted-foreground hover:text-foreground ml-auto"
        onclick={() => (lab.connection = null)}>Cancel</button
      >
    {/if}
  </div>
{/if}

{#if lab.guide}
  {@const g = lab.guide}
  <div
    class="bg-primary/8 flex min-h-11 shrink-0 items-center gap-3 border-b px-3 py-1.5 text-sm"
    role="status"
    aria-label="Copilot guide"
  >
    <Sparkles class="text-primary size-4 shrink-0" />
    <span class="text-muted-foreground shrink-0 text-xs"
      >{g.title} · step {g.at + 1} of {g.steps.length}</span
    >
    <span class="min-w-0 flex-1">{g.steps[g.at].text}</span>
    <Button
      variant="ghost"
      size="sm"
      class="h-7"
      disabled={g.at === 0}
      onclick={() => lab.guideStep(-1)}>Back</Button
    >
    <Button size="sm" class="h-7" onclick={() => lab.guideStep(1)}
      >{g.at === g.steps.length - 1 ? "Finish" : "Next"}</Button
    >
    <button
      type="button"
      class="text-muted-foreground hover:text-foreground"
      aria-label="End the guide"
      onclick={() => (lab.guide = null)}><X class="size-4" /></button
    >
  </div>
{/if}
