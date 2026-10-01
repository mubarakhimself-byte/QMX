<script lang="ts">
  import Plus from "@lucide/svelte/icons/plus";
  import Search from "@lucide/svelte/icons/search";
  import MessagesSquare from "@lucide/svelte/icons/messages-square";
  import Globe from "@lucide/svelte/icons/globe";
  import SquareTerminal from "@lucide/svelte/icons/square-terminal";
  import FileDiff from "@lucide/svelte/icons/file-diff";
  import AppWindow from "@lucide/svelte/icons/app-window";
  import Copy from "@lucide/svelte/icons/copy";
  import Check from "@lucide/svelte/icons/check";
  import Maximize2 from "@lucide/svelte/icons/maximize-2";
  import LibraryBig from "@lucide/svelte/icons/library-big";
  import Wrench from "@lucide/svelte/icons/wrench";
  import FlaskConical from "@lucide/svelte/icons/flask-conical";
  import * as Resizable from "$lib/components/ui/resizable";
  import * as Tabs from "$lib/components/ui/tabs";
  import * as Tooltip from "$lib/components/ui/tooltip";
  import { Button } from "$lib/components/ui/button";
  import { Badge } from "$lib/components/ui/badge";
  import { Input } from "$lib/components/ui/input";
  import PageHeader from "$lib/workbench/PageHeader.svelte";
  import EmptyState from "$lib/workbench/EmptyState.svelte";
  import Composer from "$lib/workbench/Composer.svelte";
  import WidgetFrame from "$lib/workbench/WidgetFrame.svelte";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import CandleChart from "$lib/demo/CandleChart.svelte";
  import { demoCandles } from "$lib/demo/data";
  import { cn } from "$lib/utils";
  import EntityCard from "$lib/qmx/EntityCard.svelte";
  import { DEMO_ENTITIES } from "$lib/demo/assets";

  // DEMO: a card before and after a chat edit; changed measures are highlighted.
  const before = DEMO_ENTITIES.find((e) => e.id === "eurusd-h1-gbm")!;
  const after = {
    ...before,
    version: "v8 draft",
    measures: before.measures.map((m) =>
      m.key === "sharpe"
        ? { ...m, value: "1.31" }
        : m.key === "dd"
          ? { ...m, value: "−5.1%" }
          : m.key === "win"
            ? { ...m, value: "47%" }
            : m,
    ),
  };
  import { page } from "$app/state";
  import { resolve } from "$app/paths";
  import Minimize2 from "@lucide/svelte/icons/minimize-2";
  import ExternalLink from "@lucide/svelte/icons/external-link";

  /** Focus hides sessions and preview; ?focus=1 opens straight into it. */
  let focus = $state(page.url.searchParams.get("focus") === "1");
  function popOut() {
    window.open(
      resolve("/copilot") + "?focus=1",
      "qmx-copilot",
      "popup,width=1280,height=900",
    );
  }

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

  // DEMO conversation: sample session, tool calls and results for design review.
  const demo = workbench.demoMode;
  const SESSIONS = [
    { id: "s1", title: "EURUSD H1 model backtest", when: "Today" },
    { id: "s2", title: "News sentiment features", when: "Yesterday" },
    { id: "s3", title: "Gold mean-reversion idea", when: "Sep 28" },
  ];
  let activeSession = $state(demo ? "s1" : null);
  const TOOLS = [
    { name: "get_candles", args: "EURUSD · H1 · 2024–2026", ms: 420 },
    {
      name: "run_backtest",
      args: "workflow eurusd-h1-gbm · draft demo",
      ms: 8100,
    },
    { name: "compare_benchmark", args: "buy-and-hold", ms: 260 },
  ];
  const RESULT = [
    ["Net return", "+18.4%", "+3.1%"],
    ["Sharpe", "1.42", "0.21"],
    ["Max drawdown", "−6.8%", "−11.9%"],
    ["Trades", "187", "1"],
    ["Win rate", "54.1%", "—"],
  ];
  let copied = $state(false);
  let previewing = $state(false);
  const candles = demoCandles(120, 1.07, 11);

  async function copyTable() {
    const tsv = [["Metric", "Strategy", "Buy & hold"], ...RESULT]
      .map((r) => r.join("\t"))
      .join("\n");
    try {
      await navigator.clipboard.writeText(tsv);
      copied = true;
      setTimeout(() => (copied = false), 1500);
    } catch {
      copied = false;
    }
  }
  function expandResult() {
    previewing = true;
    workTab = "app";
  }
</script>

<div class="flex h-full flex-col">
  {#if demo}
    <div
      class="bg-warning/15 flex h-7 shrink-0 items-center gap-2 px-3 text-xs"
    >
      <FlaskConical class="text-warning size-3.5" />
      Demo conversation. Sample messages, tool calls and results; nothing was run.
    </div>
  {/if}
  <PageHeader title="Copilot" subtitle="Conversation workspace">
    {#snippet actions()}
      <Button
        variant={focus ? "secondary" : "ghost"}
        size="sm"
        aria-pressed={focus}
        onclick={() => (focus = !focus)}
      >
        {#if focus}<Minimize2 /> Exit focus{:else}<Maximize2 /> Focus{/if}
      </Button>
      <Button variant="ghost" size="sm" onclick={popOut}>
        <ExternalLink /> New window
      </Button>
    {/snippet}
  </PageHeader>

  <Resizable.PaneGroup direction="horizontal" class="min-h-0 flex-1">
    {#if !focus}
      <Resizable.Pane defaultSize={18} minSize={14} maxSize={30}>
        <aside
          aria-label="Sessions"
          class="bg-panel flex h-full flex-col gap-1.5 p-2"
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
          {#if demo}
            <ul class="flex flex-col gap-0.5">
              {#each SESSIONS as s (s.id)}
                <li>
                  <button
                    type="button"
                    class={cn(
                      "hover:bg-muted flex w-full flex-col rounded-sm px-2 py-1.5 text-left",
                      activeSession === s.id && "bg-muted",
                    )}
                    aria-current={activeSession === s.id ? "true" : undefined}
                    onclick={() => (activeSession = s.id)}
                  >
                    <span class="truncate text-sm">{s.title}</span>
                    <span class="text-muted-foreground text-xs">{s.when}</span>
                  </button>
                </li>
              {/each}
            </ul>
          {:else}
            <EmptyState
              class="flex-1"
              title="No sessions"
              description="Sessions are kept by the daemon. Connect to see your history."
            />
          {/if}
        </aside>
      </Resizable.Pane>
      <Resizable.Handle />
    {/if}

    <Resizable.Pane defaultSize={46} minSize={30}>
      <section aria-label="Conversation" class="bg-panel flex h-full flex-col">
        <div class="min-h-0 flex-1 overflow-auto">
          {#if demo && activeSession === "s1"}
            <div
              class="mx-auto flex max-w-4xl flex-col gap-5 px-6 py-6 text-[15px] leading-relaxed"
            >
              <div class="bg-muted ml-auto max-w-[85%] rounded-md px-3 py-2">
                Backtest the EURUSD H1 gradient-boosting workflow on 2024–2026
                and compare it with buy-and-hold.
              </div>
              <div class="flex flex-col gap-2">
                <details class="group rounded-md border">
                  <summary
                    class="text-muted-foreground flex cursor-pointer items-center gap-2 px-3 py-2 text-sm"
                  >
                    <Wrench class="size-3.5" /> Used {TOOLS.length} tools
                  </summary>
                  <ul
                    class="flex flex-col gap-1.5 border-t px-3 py-2.5 font-mono text-[13px]"
                  >
                    {#each TOOLS as t (t.name)}
                      <li class="flex items-center gap-2">
                        <Check class="text-success size-3.5" />
                        <span class="font-medium">{t.name}</span>
                        <span class="text-muted-foreground truncate"
                          >{t.args}</span
                        >
                        <span class="text-muted-foreground ml-auto"
                          >{(t.ms / 1000).toFixed(1)}s</span
                        >
                      </li>
                    {/each}
                  </ul>
                </details>
                <p>
                  The strategy beat buy-and-hold over the period with less than
                  half the drawdown. Most of the edge came from London-session
                  breakouts; the 2025 Q2 chop accounts for the largest losing
                  streak.
                </p>
                <div class="surface overflow-hidden rounded-lg">
                  <div
                    class="bg-panel flex h-8 items-center gap-1 border-b pr-1 pl-3"
                  >
                    <span class="panel-label">Backtest vs buy-and-hold</span>
                    <div class="ml-auto flex items-center">
                      <Tooltip.Root>
                        <Tooltip.Trigger>
                          {#snippet child({ props })}
                            <Button
                              {...props}
                              variant="ghost"
                              size="icon-xs"
                              aria-label="Copy table"
                              onclick={copyTable}
                            >
                              {#if copied}<Check />{:else}<Copy />{/if}
                            </Button>
                          {/snippet}
                        </Tooltip.Trigger>
                        <Tooltip.Content
                          >{copied ? "Copied" : "Copy table"}</Tooltip.Content
                        >
                      </Tooltip.Root>
                      <Tooltip.Root>
                        <Tooltip.Trigger>
                          {#snippet child({ props })}
                            <Button
                              {...props}
                              variant="ghost"
                              size="icon-xs"
                              aria-label="Open in preview"
                              onclick={expandResult}
                            >
                              <Maximize2 />
                            </Button>
                          {/snippet}
                        </Tooltip.Trigger>
                        <Tooltip.Content>Open in preview</Tooltip.Content>
                      </Tooltip.Root>
                      <Tooltip.Root>
                        <Tooltip.Trigger>
                          {#snippet child({ props })}
                            <Button
                              {...props}
                              variant="ghost"
                              size="icon-xs"
                              aria-label="Save to Library (needs daemon)"
                              aria-disabled="true"
                              class="aria-disabled:pointer-events-auto aria-disabled:opacity-50"
                              onclick={(e) => e.preventDefault()}
                            >
                              <LibraryBig />
                            </Button>
                          {/snippet}
                        </Tooltip.Trigger>
                        <Tooltip.Content
                          >Save to Library needs the daemon</Tooltip.Content
                        >
                      </Tooltip.Root>
                    </div>
                  </div>
                  <table class="w-full text-sm">
                    <thead class="text-muted-foreground text-left">
                      <tr>
                        <th class="px-4 py-2 font-medium">Metric</th>
                        <th class="px-4 text-right font-medium">Strategy</th>
                        <th class="px-3 text-right font-medium"
                          >Buy &amp; hold</th
                        >
                      </tr>
                    </thead>
                    <tbody>
                      {#each RESULT as [m, s, b] (m)}
                        <tr class="border-t">
                          <td class="px-4 py-2.5">{m}</td>
                          <td class="num px-4 text-right font-medium">{s}</td>
                          <td class="text-muted-foreground px-3 text-right"
                            >{b}</td
                          >
                        </tr>
                      {/each}
                    </tbody>
                  </table>
                </div>
                <div class="flex gap-1.5">
                  <Badge variant="outline" class="text-[10px]"
                    >sample result</Badge
                  >
                  <Badge variant="outline" class="text-[10px]"
                    >draft · not run</Badge
                  >
                </div>
              </div>
              <div class="bg-muted ml-auto max-w-[85%] rounded-md px-3 py-2">
                Tighten the stop to 0.8 ATR and show me what changes.
              </div>
              <div class="flex flex-col gap-3">
                <p>
                  With a 0.8 ATR stop the drawdown falls but more trades get
                  stopped out early. This is a draft edit; it becomes evidence
                  only after you publish and re-run it.
                </p>
                <div class="grid gap-3 sm:grid-cols-2">
                  <div>
                    <p class="panel-label mb-1.5">Before · v7</p>
                    <EntityCard entity={before} compact />
                  </div>
                  <div>
                    <p class="panel-label mb-1.5">Draft edit · not run</p>
                    <EntityCard
                      entity={after}
                      compact
                      changed={["sharpe", "dd", "win"]}
                    />
                  </div>
                </div>
              </div>
            </div>
          {:else}
            <EmptyState
              class="h-full"
              icon={MessagesSquare}
              title={demo
                ? "No sample messages in this session"
                : "Start a conversation"}
              description="Ask the copilot to research, build a workflow, or explain a result. It can reference apps, widgets and Library items."
            />
          {/if}
        </div>
        <div class="mx-auto w-full max-w-4xl px-6 pb-5">
          <Composer
            size={focus ? "lg" : "md"}
            refs={workbench.copilotRefs}
            onremoveref={(r) => workbench.removeRef(r)}
          />
        </div>
      </section>
    </Resizable.Pane>
    {#if !focus}
      <Resizable.Handle />

      <Resizable.Pane defaultSize={36} minSize={20}>
        <Tabs.Root
          bind:value={workTab}
          class="bg-panel flex h-full flex-col gap-0"
        >
          <div class="flex h-9 shrink-0 items-center border-b px-2">
            <Tabs.List variant="line" aria-label="Work area">
              {#each WORK_TABS as t (t.id)}
                <Tabs.Trigger value={t.id}><t.icon />{t.label}</Tabs.Trigger>
              {/each}
            </Tabs.List>
          </div>
          {#each WORK_TABS as t (t.id)}
            <Tabs.Content value={t.id} class="min-h-0 flex-1">
              {#if t.id === "app" && previewing}
                <div class="flex h-full flex-col p-2">
                  <WidgetFrame
                    title="EURUSD · strategy period (demo)"
                    class="flex-1"
                    onclose={() => (previewing = false)}
                  >
                    <CandleChart {candles} />
                  </WidgetFrame>
                </div>
              {:else}
                <EmptyState
                  class="h-full"
                  icon={t.icon}
                  title={t.title}
                  description={t.text}
                />
              {/if}
            </Tabs.Content>
          {/each}
        </Tabs.Root>
      </Resizable.Pane>
    {/if}
  </Resizable.PaneGroup>
</div>
