<script lang="ts">
  import "@xyflow/svelte/dist/style.css";
  import {
    SvelteFlow,
    Background,
    Controls,
    type Node,
    type Edge,
  } from "@xyflow/svelte";
  import Save from "@lucide/svelte/icons/save";
  import CircleCheck from "@lucide/svelte/icons/circle-check";
  import Upload from "@lucide/svelte/icons/upload";
  import Play from "@lucide/svelte/icons/play";
  import Plus from "@lucide/svelte/icons/plus";
  import MousePointerClick from "@lucide/svelte/icons/mouse-pointer-click";
  import * as Resizable from "$lib/components/ui/resizable";
  import * as Tabs from "$lib/components/ui/tabs";
  import * as Tooltip from "$lib/components/ui/tooltip";
  import { Button } from "$lib/components/ui/button";
  import { Badge } from "$lib/components/ui/badge";
  import PageHeader from "$lib/workbench/PageHeader.svelte";
  import EmptyState from "$lib/workbench/EmptyState.svelte";
  import Composer from "$lib/workbench/Composer.svelte";

  // Graph layout is client-only; the draft itself is daemon-issued (editor_draft_id).
  let nodes = $state.raw<Node[]>([]);
  let edges = $state.raw<Edge[]>([]);
  let side = $state<string>("inspect");

  // Lifecycle verbs in order. Each needs a daemon service (Epic 71 / 72).
  const STEPS = [
    {
      label: "Save draft",
      icon: Save,
      why: "Saving needs the daemon to issue a draft id.",
    },
    {
      label: "Validate",
      icon: CircleCheck,
      why: "Validation runs on a saved draft.",
    },
    {
      label: "Publish",
      icon: Upload,
      why: "Publishing turns a saved draft into a runnable version.",
    },
    {
      label: "Run",
      icon: Play,
      why: "Only published versions run. Drafts never run.",
    },
  ];
</script>

<div class="flex h-full flex-col">
  <PageHeader title="Authoring" subtitle="Untitled workflow · not saved">
    {#snippet actions()}
      <Badge variant="outline">Draft</Badge>
      {#each STEPS as s (s.label)}
        <Tooltip.Root>
          <Tooltip.Trigger>
            {#snippet child({ props })}
              <!-- aria-disabled keeps the reason reachable by hover and keyboard. -->
              <Button
                {...props}
                size="sm"
                variant={s.label === "Run" ? "default" : "outline"}
                aria-disabled="true"
                class="aria-disabled:pointer-events-auto aria-disabled:cursor-not-allowed aria-disabled:opacity-50"
                onclick={(e) => e.preventDefault()}
              >
                <s.icon />{s.label}
              </Button>
            {/snippet}
          </Tooltip.Trigger>
          <Tooltip.Content>{s.why}</Tooltip.Content>
        </Tooltip.Root>
      {/each}
    {/snippet}
  </PageHeader>

  <Resizable.PaneGroup direction="horizontal" class="min-h-0 flex-1">
    <Resizable.Pane defaultSize={70} minSize={40}>
      <div class="relative h-full" aria-label="Workflow graph">
        <SvelteFlow
          bind:nodes
          bind:edges
          colorMode="dark"
          fitView
          proOptions={{ hideAttribution: true }}
        >
          <Background gap={20} />
          <Controls position="bottom-left" />
        </SvelteFlow>
        {#if nodes.length === 0}
          <div
            class="pointer-events-none absolute inset-0 flex items-center justify-center"
          >
            <div class="pointer-events-auto">
              <EmptyState
                icon={Plus}
                title="Empty workflow"
                description="Adding steps needs the list of available operations from the daemon. You can also ask the copilot to draft one."
              />
            </div>
          </div>
        {/if}
      </div>
    </Resizable.Pane>
    <Resizable.Handle />
    <Resizable.Pane defaultSize={30} minSize={20}>
      <Tabs.Root bind:value={side} class="bg-panel flex h-full flex-col gap-0">
        <div class="flex h-10 shrink-0 items-center border-b px-2">
          <Tabs.List variant="line">
            <Tabs.Trigger value="inspect">Inspector</Tabs.Trigger>
            <Tabs.Trigger value="copilot">Copilot</Tabs.Trigger>
          </Tabs.List>
        </div>
        <Tabs.Content value="inspect" class="min-h-0 flex-1">
          <EmptyState
            class="h-full"
            icon={MousePointerClick}
            title="Nothing selected"
            description="Select a step to see its settings, code and last results."
          />
        </Tabs.Content>
        <Tabs.Content value="copilot" class="flex min-h-0 flex-1 flex-col">
          <div class="min-h-0 flex-1"></div>
          <div class="p-3">
            <Composer placeholder="Describe the workflow you want…" />
          </div>
        </Tabs.Content>
      </Tabs.Root>
    </Resizable.Pane>
  </Resizable.PaneGroup>
</div>

<style>
  :global(.svelte-flow) {
    --xy-background-color: var(--background);
    --xy-background-pattern-color: color-mix(
      in oklch,
      var(--muted-foreground) 35%,
      transparent
    );
    --xy-controls-button-background-color: var(--card);
    --xy-controls-button-color: var(--foreground);
    --xy-controls-button-border-color: var(--border);
  }
</style>
