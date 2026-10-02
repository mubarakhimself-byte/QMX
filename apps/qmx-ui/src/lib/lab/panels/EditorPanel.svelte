<script lang="ts">
  /**
   * Build the subject three ways: a node graph (a Graph Template: a workflow
   * of steps), plain code (first-class, DEC-0433), or import work made
   * elsewhere (Claude Code, Codex, notebooks, ONNX). Drafts never run; only
   * published versions do.
   */
  import "@xyflow/svelte/dist/style.css";
  import {
    SvelteFlow,
    Background,
    Controls,
    MiniMap,
    MarkerType,
    type Node,
    type Edge,
  } from "@xyflow/svelte";
  import Map from "@lucide/svelte/icons/map";
  import FileCode from "@lucide/svelte/icons/file-code";
  import Box from "@lucide/svelte/icons/box";
  import NotebookPen from "@lucide/svelte/icons/notebook-pen";
  import GitBranch from "@lucide/svelte/icons/git-branch";
  import CodeEditor from "$lib/qmx/CodeEditor.svelte";
  import StepNode from "$lib/demo/StepNode.svelte";
  import { DEMO_STEPS, demoEdges, demoNodes } from "$lib/demo/workflow";
  import { cn } from "$lib/utils";
  import type { LinkGroup } from "$lib/workbench/tiles/tiles";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { lab } from "../lab.svelte";

  let { link }: { link?: LinkGroup } = $props();

  const MODES = ["Graph", "Code", "Import"] as const;
  let mode = $state<(typeof MODES)[number]>("Graph");
  let showMap = $state(false);
  let nodes = $state.raw<Node[]>(demoNodes());
  let edges = $state.raw<Edge[]>(demoEdges());
  const nodeTypes = { step: StepNode };

  const source = DEMO_STEPS.map(
    (s) => `# ${s.label}: ${s.detail}\n${s.code}`,
  ).join("\n\n");
  const IMPORTS = [
    {
      icon: Box,
      title: "Model file",
      note: "ONNX, pickle or joblib. Shipped inside the bot so it never fetches at run time.",
    },
    {
      icon: GitBranch,
      title: "Code from a repo",
      note: "A folder Claude Code or Codex wrote. Becomes the bot's logic.",
    },
    {
      icon: NotebookPen,
      title: "Notebook",
      note: "Turn cells into steps; each step keeps its code.",
    },
    {
      icon: FileCode,
      title: "Python file",
      note: "A single script, wrapped as one step or a whole bot.",
    },
  ];
</script>

<div class="flex h-full flex-col">
  <div class="flex h-9 shrink-0 items-center gap-1 border-b px-2">
    <div
      class="flex items-center gap-0.5"
      role="radiogroup"
      aria-label="Build mode"
    >
      {#each MODES as m (m)}
        <button
          type="button"
          role="radio"
          aria-checked={mode === m}
          class={cn(
            "h-6 rounded-md px-2.5 text-xs",
            mode === m
              ? "bg-muted text-foreground"
              : "text-muted-foreground hover:text-foreground",
          )}
          onclick={() => (mode = m)}>{m}</button
        >
      {/each}
    </div>
    <span class="text-muted-foreground ml-2 text-xs"
      >Breakout research · draft v7 · published v6</span
    >
    {#if mode === "Graph"}
      <button
        type="button"
        class={cn(
          "ml-auto flex h-6 items-center gap-1 rounded-md px-2 text-xs",
          showMap ? "bg-muted" : "text-muted-foreground hover:text-foreground",
        )}
        aria-pressed={showMap}
        onclick={() => (showMap = !showMap)}><Map class="size-3.5" />Map</button
      >
    {/if}
  </div>
  <div class="relative min-h-0 flex-1">
    {#if mode === "Graph"}
      <SvelteFlow
        bind:nodes
        bind:edges
        {nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.08, maxZoom: 1.6 }}
        defaultEdgeOptions={{
          markerEnd: { type: MarkerType.ArrowClosed, width: 16, height: 16 },
        }}
        onnodeclick={({ node }) => lab.select(link, node.id)}
        colorMode={workbench.theme === "paper" ? "light" : "dark"}
        proOptions={{ hideAttribution: true }}
      >
        <Background gap={22} />
        <Controls position="bottom-left" showLock={false} />
        {#if showMap}
          <MiniMap
            width={150}
            height={92}
            bgColor="var(--panel)"
            nodeColor="var(--muted-foreground)"
            position="bottom-right"
            pannable
            zoomable
            ariaLabel="Workflow overview"
          />
        {/if}
      </SvelteFlow>
    {:else if mode === "Code"}
      <CodeEditor value={source} label="Bot logic (Python)" />
    {:else}
      <div
        class="grid h-full content-start gap-3 overflow-auto p-4 [grid-template-columns:repeat(auto-fill,minmax(15rem,1fr))]"
      >
        {#each IMPORTS as im (im.title)}
          <button
            type="button"
            class="hover:border-ring flex flex-col gap-2 rounded-lg border border-dashed p-4 text-left"
            onclick={() =>
              workbench.notify(
                `${im.title}: choose a file. Upload needs the daemon.`,
              )}
          >
            <im.icon class="text-muted-foreground size-5" />
            <span class="text-sm font-medium">{im.title}</span>
            <span class="text-muted-foreground text-xs">{im.note}</span>
          </button>
        {/each}
      </div>
    {/if}
  </div>
</div>

<style>
  :global(.svelte-flow) {
    --xy-background-color: transparent;
    --xy-background-pattern-color: color-mix(
      in oklab,
      var(--muted-foreground) 28%,
      transparent
    );
    --xy-controls-button-background-color: var(--card);
    --xy-controls-button-color: var(--foreground);
    --xy-controls-button-border-color: var(--border);
    --xy-edge-stroke: color-mix(in oklab, var(--foreground) 50%, transparent);
    --xy-edge-stroke-selected: var(--primary);
    --xy-edge-stroke-width: 1.6;
    --xy-handle-background-color: var(--primary);
    --xy-handle-border-color: var(--background);
    --xy-minimap-background-color: var(--panel);
    --xy-minimap-mask-background-color: color-mix(
      in oklab,
      var(--background) 60%,
      transparent
    );
  }
  :global(.svelte-flow__node-step) {
    background: transparent;
    border: 0;
    padding: 0;
  }
</style>
