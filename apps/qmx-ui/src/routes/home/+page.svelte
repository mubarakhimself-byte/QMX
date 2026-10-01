<script lang="ts">
  import BellDot from "@lucide/svelte/icons/bell-dot";
  import Loader from "@lucide/svelte/icons/loader";
  import History from "@lucide/svelte/icons/history";
  import AppWindow from "@lucide/svelte/icons/app-window";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import * as Resizable from "$lib/components/ui/resizable";
  import { Button } from "$lib/components/ui/button";
  import PageHeader from "$lib/workbench/PageHeader.svelte";
  import EmptyState from "$lib/workbench/EmptyState.svelte";
  import WidgetFrame from "$lib/workbench/WidgetFrame.svelte";
  import StatTile from "$lib/workbench/StatTile.svelte";
  import CopilotColumn from "$lib/workbench/CopilotColumn.svelte";

  let copilotOpen = $state(true);
</script>

<div class="flex h-full flex-col">
  <PageHeader title="Home" subtitle="Everything running, waiting and recent">
    {#snippet actions()}
      {#if !copilotOpen}
        <Button variant="ghost" size="sm" onclick={() => (copilotOpen = true)}>
          <Sparkles /> Copilot
        </Button>
      {/if}
    {/snippet}
  </PageHeader>

  <Resizable.PaneGroup direction="horizontal" class="min-h-0 flex-1">
    <Resizable.Pane defaultSize={72} minSize={45}>
      <div class="flex h-full flex-col gap-2 overflow-auto p-2">
        <div class="grid grid-cols-2 gap-2 lg:grid-cols-4">
          <StatTile label="Running jobs" hint="Not connected" />
          <StatTile label="Needs attention" hint="Not connected" />
          <StatTile label="Opened apps" hint="Not connected" />
          <StatTile label="Copilot sessions" hint="Not connected" />
        </div>

        <div class="grid auto-rows-[13rem] gap-2 lg:grid-cols-2">
          <WidgetFrame title="Needs attention">
            <EmptyState
              class="h-full"
              icon={BellDot}
              title="Nothing needs attention"
              description="Failed and unknown jobs land here."
            />
          </WidgetFrame>
          <WidgetFrame title="Running">
            <EmptyState
              class="h-full"
              icon={Loader}
              title="No jobs running"
              description="Backtests, research runs and workflows in progress."
            />
          </WidgetFrame>
          <WidgetFrame title="Recent sessions">
            <EmptyState
              class="h-full"
              icon={History}
              title="No recent sessions"
              description="Resume a Copilot or Authoring session from here."
            />
          </WidgetFrame>
          <WidgetFrame title="Apps">
            <EmptyState
              class="h-full"
              icon={AppWindow}
              title="No apps installed"
              description="Installed mini apps and workflows open from here."
            />
          </WidgetFrame>
        </div>
      </div>
    </Resizable.Pane>
    {#if copilotOpen}
      <Resizable.Handle />
      <Resizable.Pane defaultSize={28} minSize={20} maxSize={40}>
        <CopilotColumn
          title="Home copilot"
          hint="Ask about your running work. Separate from Copilot sessions and not tied to any app."
          placeholder="Ask about your work…"
          onclose={() => (copilotOpen = false)}
        />
      </Resizable.Pane>
    {/if}
  </Resizable.PaneGroup>
</div>
