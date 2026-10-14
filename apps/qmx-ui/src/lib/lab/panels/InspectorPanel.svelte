<script lang="ts">
  /** Settings, code and last result for the step selected in a linked editor. */
  import MousePointerClick from "@lucide/svelte/icons/mouse-pointer-click";
  import { Input } from "$lib/components/ui/input";
  import CodeEditor from "$lib/qmx/CodeEditor.svelte";
  import EmptyState from "$lib/workbench/EmptyState.svelte";
  import { DEMO_STEPS } from "$lib/demo/workflow";
  import { cn } from "$lib/utils";
  import type { LinkGroup } from "$lib/workbench/tiles/tiles";
  import { panelSize } from "$lib/workbench/tiles/panel-size";
  import EnvChip from "../EnvChip.svelte";
  import { lab } from "../lab.svelte";

  let { link }: { link?: LinkGroup } = $props();
  const step = $derived(DEMO_STEPS.find((s) => s.id === lab.selectedFor(link)));
  const size = panelSize();
  let tab = $state<"settings" | "code">("settings");
  const env = $derived(
    step?.kind === "Model"
      ? "colab"
      : step?.kind === "Test"
        ? "vps-fsn"
        : "local",
  );
</script>

{#if !step}
  <EmptyState class="h-full" icon={MousePointerClick} title="Select a step" />
{:else if size.mode === "compact"}
  <div class="p-panel gap-row flex h-full flex-col">
    <p class="text-muted-foreground text-xs">{step.kind} step</p>
    <p class="truncate text-base font-medium">{step.label}</p>
    <EnvChip {env} status="done" />
    <dl class="gap-row mt-group flex flex-col text-sm">
      {#each step.settings as [k, v] (k)}
        <div class="flex min-w-0 flex-col">
          <dt class="text-muted-foreground truncate text-xs">{k}</dt>
          <dd class="truncate">{v}</dd>
        </div>
      {/each}
    </dl>
  </div>
{:else}
  <div class="flex h-full flex-col">
    <div class="px-panel pt-panel pb-row shrink-0">
      <div class="flex items-center gap-2">
        <p class="min-w-0 truncate text-base font-medium">{step.label}</p>
        <span class="ml-auto shrink-0"><EnvChip {env} status="done" /></span>
      </div>
      <p class="text-muted-foreground truncate text-xs">
        {step.kind} · {step.detail}
      </p>
    </div>
    <div class="px-panel flex h-9 shrink-0 items-center">
      <div
        class="bg-muted flex rounded-md p-0.5 text-xs"
        role="radiogroup"
        aria-label="Show"
      >
        {#each ["settings", "code"] as const as t (t)}
          <button
            type="button"
            role="radio"
            aria-checked={tab === t}
            class={cn(
              "h-6 rounded px-2.5 capitalize",
              tab === t
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground",
            )}
            onclick={() => (tab = t)}>{t}</button
          >
        {/each}
      </div>
    </div>
    <div class="min-h-0 flex-1 overflow-auto">
      {#if tab === "settings"}
        <div class="gap-row p-panel flex flex-col">
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
{/if}
