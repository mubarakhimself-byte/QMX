<script lang="ts">
  /** Settings, code and last result for the step selected in a linked editor. */
  import MousePointerClick from "@lucide/svelte/icons/mouse-pointer-click";
  import { Input } from "$lib/components/ui/input";
  import CodeEditor from "$lib/qmx/CodeEditor.svelte";
  import EmptyState from "$lib/workbench/EmptyState.svelte";
  import { DEMO_STEPS } from "$lib/demo/workflow";
  import { cn } from "$lib/utils";
  import type { LinkGroup } from "$lib/workbench/tiles/tiles";
  import EnvChip from "../EnvChip.svelte";
  import { lab } from "../lab.svelte";

  let { link }: { link?: LinkGroup } = $props();
  const step = $derived(DEMO_STEPS.find((s) => s.id === lab.selectedFor(link)));
  let tab = $state<"settings" | "code">("settings");
  const env = $derived(
    step?.kind === "Model"
      ? "colab"
      : step?.kind === "Test"
        ? "vps-fsn"
        : "local",
  );
</script>

{#if step}
  <div class="flex h-full flex-col">
    <div class="shrink-0 border-b px-3 py-2">
      <p class="text-muted-foreground text-xs">{step.kind} step</p>
      <p class="text-base font-medium">{step.label}</p>
      <p class="text-muted-foreground text-xs">{step.detail}</p>
      <div class="mt-2 flex items-center gap-2">
        <span class="text-muted-foreground text-xs">Runs on</span>
        <EnvChip {env} status="done" />
      </div>
    </div>
    <div class="flex h-8 shrink-0 items-center gap-0.5 border-b px-2">
      {#each ["settings", "code"] as const as t (t)}
        <button
          type="button"
          class={cn(
            "h-6 rounded-md px-2 text-xs capitalize",
            tab === t
              ? "bg-muted"
              : "text-muted-foreground hover:text-foreground",
          )}
          aria-pressed={tab === t}
          onclick={() => (tab = t)}>{t}</button
        >
      {/each}
    </div>
    <div class="min-h-0 flex-1 overflow-auto">
      {#if tab === "settings"}
        <div class="flex flex-col gap-2.5 p-3">
          {#each step.settings as [k, v] (k)}
            <label class="flex flex-col gap-1 text-xs">
              <span class="text-muted-foreground">{k}</span>
              <Input class="h-8" value={v} />
            </label>
          {/each}
        </div>
      {:else}
        <CodeEditor value={step.code} label={`Code for ${step.label}`} />
      {/if}
    </div>
  </div>
{:else}
  <EmptyState
    class="h-full"
    icon={MousePointerClick}
    title="Select a step"
    description="Click a step in a linked editor to see its settings, code and where it runs."
  />
{/if}
