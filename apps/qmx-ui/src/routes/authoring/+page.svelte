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
  import { workbench } from "$lib/workbench/workbench.svelte";
  import StepNode from "$lib/demo/StepNode.svelte";
  import { DEMO_STEPS, demoNodes, demoEdges } from "$lib/demo/workflow";
  import ArrowLeft from "@lucide/svelte/icons/arrow-left";
  import Code from "@lucide/svelte/icons/code";
  import FlaskConical from "@lucide/svelte/icons/flask-conical";

  // Graph layout is client-only; the draft itself is daemon-issued (editor_draft_id).
  // Demo mode loads a labelled sample graph; it is not a saved draft.
  const demo = workbench.demoMode;
  let nodes = $state.raw<Node[]>(demo ? demoNodes() : []);
  let edges = $state.raw<Edge[]>(demo ? demoEdges() : []);
  let side = $state<string>("inspect");
  const nodeTypes = { step: StepNode };
  let selectedId = $state<string | null>(null);
  /** Detail opens over the graph so its viewport and selection survive Return. */
  let detailOpen = $state(false);
  const selected = $derived(DEMO_STEPS.find((s) => s.id === selectedId));

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
  {#if demo}
    <div
      class="bg-warning/15 flex h-7 shrink-0 items-center gap-2 px-3 text-xs"
    >
      <FlaskConical class="text-warning size-3.5" />
      Demo workflow. A sample graph, not a saved draft; it cannot run.
    </div>
  {/if}
  <PageHeader
    title="Authoring"
    subtitle={demo
      ? "EURUSD H1 model (demo) · not saved"
      : "Untitled workflow · not saved"}
  >
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
          {nodeTypes}
          onnodeclick={({ node }) => {
            selectedId = node.id;
            side = "inspect";
          }}
          onpaneclick={() => (selectedId = null)}
          colorMode="dark"
          fitView
          proOptions={{ hideAttribution: true }}
        >
          <Background gap={20} />
          <Controls position="bottom-left" />
        </SvelteFlow>
        {#if detailOpen && selected}
          <section
            aria-label={`${selected.label} code`}
            class="bg-background absolute inset-0 z-10 flex flex-col"
          >
            <div class="flex h-9 shrink-0 items-center gap-2 border-b px-2">
              <Button
                variant="ghost"
                size="sm"
                onclick={() => (detailOpen = false)}
              >
                <ArrowLeft /> Back to graph
              </Button>
              <span class="panel-label">{selected.kind}</span>
              <span class="text-sm font-medium">{selected.label}</span>
              <Badge variant="outline" class="ml-auto h-4 px-1.5 text-[10px]"
                >draft · demo</Badge
              >
            </div>
            <pre
              class="bg-panel m-2 flex-1 overflow-auto rounded-md border p-3 font-mono text-xs leading-relaxed"><code
                >{selected.code}</code
              ></pre>
          </section>
        {/if}
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
        <Tabs.Content value="inspect" class="min-h-0 flex-1 overflow-auto">
          {#if selected}
            <div class="flex flex-col gap-3 p-3">
              <div>
                <p class="panel-label">{selected.kind}</p>
                <p class="text-sm font-medium">{selected.label}</p>
                <p class="text-muted-foreground text-xs">{selected.detail}</p>
              </div>
              <dl class="flex flex-col text-xs">
                {#each selected.settings as [k, v] (k)}
                  <div class="flex justify-between gap-3 border-b py-1.5">
                    <dt class="text-muted-foreground">{k}</dt>
                    <dd class="text-right font-medium">{v}</dd>
                  </div>
                {/each}
              </dl>
              <Button
                variant="outline"
                size="sm"
                onclick={() => (detailOpen = true)}
              >
                <Code /> Open code
              </Button>
              <p class="text-muted-foreground text-xs">
                Last results appear here after a published version runs.
              </p>
            </div>
          {:else}
            <EmptyState
              class="h-full"
              icon={MousePointerClick}
              title="Nothing selected"
              description="Select a step to see its settings, code and last results."
            />
          {/if}
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
