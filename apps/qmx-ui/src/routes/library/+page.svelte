<script lang="ts">
  import Search from "@lucide/svelte/icons/search";
  import Package from "@lucide/svelte/icons/package";
  import BookOpen from "@lucide/svelte/icons/book-open";
  import Blocks from "@lucide/svelte/icons/blocks";
  import * as Tabs from "$lib/components/ui/tabs";
  import { Input } from "$lib/components/ui/input";
  import PageHeader from "$lib/workbench/PageHeader.svelte";
  import EmptyState from "$lib/workbench/EmptyState.svelte";

  // Hit kinds stay separate; each keeps its own actions (UI LIBRARY §5).
  const KINDS = [
    {
      id: "artifact",
      label: "Artifacts",
      icon: Package,
      text: "Datasets, models, reports and files produced or stored by QMX.",
    },
    {
      id: "knowledge",
      label: "Knowledge",
      icon: BookOpen,
      text: "Articles, notes and research you can cite in a conversation.",
    },
    {
      id: "contribution",
      label: "Apps & workflows",
      icon: Blocks,
      text: "Installed packs: mini apps, workflows and headless operations.",
    },
  ] as const;
  let kind = $state<string>("artifact");
</script>

<div class="flex h-full flex-col">
  <PageHeader title="Library" subtitle="Everything QMX knows and has made" />

  <div class="mx-auto flex w-full max-w-5xl min-h-0 flex-1 flex-col gap-3 p-4">
    <div class="relative">
      <Search
        class="text-muted-foreground pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2"
      />
      <Input
        class="h-10 pl-9"
        placeholder="Search the Library"
        aria-label="Search the Library"
        disabled
      />
    </div>
    <p class="text-muted-foreground text-xs">
      Search needs a connection to the QMX daemon.
    </p>

    <Tabs.Root bind:value={kind} class="min-h-0 flex-1">
      <Tabs.List>
        {#each KINDS as k (k.id)}
          <Tabs.Trigger value={k.id}><k.icon />{k.label}</Tabs.Trigger>
        {/each}
      </Tabs.List>
      {#each KINDS as k (k.id)}
        <Tabs.Content value={k.id}>
          <EmptyState
            icon={k.icon}
            title={`No ${k.label.toLowerCase()}`}
            description={k.text}
          />
        </Tabs.Content>
      {/each}
    </Tabs.Root>
  </div>
</div>
