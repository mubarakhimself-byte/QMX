<script lang="ts">
  import Plus from "@lucide/svelte/icons/plus";
  import Search from "@lucide/svelte/icons/search";
  import MessagesSquare from "@lucide/svelte/icons/messages-square";
  import Globe from "@lucide/svelte/icons/globe";
  import SquareTerminal from "@lucide/svelte/icons/square-terminal";
  import FileDiff from "@lucide/svelte/icons/file-diff";
  import AppWindow from "@lucide/svelte/icons/app-window";
  import * as Resizable from "$lib/components/ui/resizable";
  import * as Tabs from "$lib/components/ui/tabs";
  import { Button } from "$lib/components/ui/button";
  import { Input } from "$lib/components/ui/input";
  import PageHeader from "$lib/workbench/PageHeader.svelte";
  import EmptyState from "$lib/workbench/EmptyState.svelte";
  import Composer from "$lib/workbench/Composer.svelte";

  // Work-area tabs are client-local preview hosts; opening one implies no grant.
  const WORK_TABS = [
    {
      id: "browser",
      label: "Browser",
      icon: Globe,
      title: "No page open",
      text: "Pages the copilot opens, or that you open, show here.",
    },
    {
      id: "terminal",
      label: "Terminal",
      icon: SquareTerminal,
      title: "No job output",
      text: "A read-only view of a job's output. It is not a shell on this machine.",
    },
    {
      id: "diff",
      label: "Diff",
      icon: FileDiff,
      title: "Nothing to compare",
      text: "Compare two versions of a draft, strategy or file.",
    },
    {
      id: "app",
      label: "App preview",
      icon: AppWindow,
      title: "No app previewed",
      text: "Preview a mini app, widget or workflow. Previewing does not install or grant it.",
    },
  ] as const;
  let workTab = $state<string>("browser");
</script>

<div class="flex h-full flex-col">
  <PageHeader title="Copilot" subtitle="Conversation workspace" />

  <Resizable.PaneGroup direction="horizontal" class="min-h-0 flex-1">
    <Resizable.Pane defaultSize={20} minSize={14} maxSize={32}>
      <aside
        aria-label="Sessions"
        class="bg-panel flex h-full flex-col gap-2 p-2"
      >
        <Button variant="outline" size="sm" class="justify-start" disabled>
          <Plus /> New session
        </Button>
        <div class="relative">
          <Search
            class="text-muted-foreground pointer-events-none absolute top-1/2 left-2.5 size-3.5 -translate-y-1/2"
          />
          <Input
            placeholder="Search sessions"
            aria-label="Search sessions"
            class="h-8 pl-8"
            disabled
          />
        </div>
        <EmptyState
          class="flex-1"
          title="No sessions"
          description="Sessions are kept by the daemon. Connect to see your history."
        />
      </aside>
    </Resizable.Pane>
    <Resizable.Handle />

    <Resizable.Pane defaultSize={44} minSize={30}>
      <section aria-label="Conversation" class="flex h-full flex-col">
        <div class="min-h-0 flex-1 overflow-auto">
          <EmptyState
            class="h-full"
            icon={MessagesSquare}
            title="Start a conversation"
            description="Ask the copilot to research, build a workflow, or explain a result. It can reference apps, widgets and Library items."
          />
        </div>
        <div class="p-3"><Composer /></div>
      </section>
    </Resizable.Pane>
    <Resizable.Handle />

    <Resizable.Pane defaultSize={36} minSize={20}>
      <Tabs.Root bind:value={workTab} class="flex h-full flex-col gap-0">
        <div class="flex h-10 shrink-0 items-center border-b px-2">
          <Tabs.List variant="line" aria-label="Work area">
            {#each WORK_TABS as t (t.id)}
              <Tabs.Trigger value={t.id}><t.icon />{t.label}</Tabs.Trigger>
            {/each}
          </Tabs.List>
        </div>
        {#each WORK_TABS as t (t.id)}
          <Tabs.Content value={t.id} class="min-h-0 flex-1">
            <EmptyState
              class="h-full"
              icon={t.icon}
              title={t.title}
              description={t.text}
            />
          </Tabs.Content>
        {/each}
      </Tabs.Root>
    </Resizable.Pane>
  </Resizable.PaneGroup>
</div>
