<script lang="ts">
  /**
   * The copilot's right side: Activity (every agent and background job,
   * what each is doing now, where it runs), Artifacts it made, an in-app
   * Browser, a Terminal on job output, and a Preview for apps and reports.
   * Jobs run on servers, so they carry on when this window or laptop closes.
   */
  import { onMount } from "svelte";
  import Activity from "@lucide/svelte/icons/activity";
  import FileText from "@lucide/svelte/icons/file-text";
  import Globe from "@lucide/svelte/icons/globe";
  import SquareTerminal from "@lucide/svelte/icons/square-terminal";
  import AppWindow from "@lucide/svelte/icons/app-window";
  import Square from "@lucide/svelte/icons/square";
  import Clock from "@lucide/svelte/icons/clock";
  import { Button } from "$lib/components/ui/button";
  import EmptyState from "$lib/workbench/EmptyState.svelte";
  import { cn } from "$lib/utils";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { ARTIFACTS, SESSIONS, TASKS, THREADS } from "./demo";

  let {
    tab = $bindable("activity"),
    artifact = $bindable<string | null>(null),
    session,
  }: {
    tab?: string;
    artifact?: string | null;
    session: string | null;
  } = $props();

  const TABS = [
    { id: "activity", label: "Activity", icon: Activity },
    { id: "artifacts", label: "Artifacts", icon: FileText },
    { id: "browser", label: "Browser", icon: Globe },
    { id: "terminal", label: "Terminal", icon: SquareTerminal },
    { id: "preview", label: "Preview", icon: AppWindow },
  ];

  // Agents across sessions, from each session's latest agents block.
  const AGENTS = SESSIONS.flatMap((s) =>
    (THREADS[s.id] ?? []).flatMap((b) =>
      b.kind === "agents"
        ? b.agents.map((a) => ({ ...a, session: s.id, sessionTitle: s.title }))
        : [],
    ),
  );
  // Demo: running things creep forward so the tab feels alive.
  let tick = $state(0);
  onMount(() => {
    const t = setInterval(() => tick++, 2500);
    return () => clearInterval(t);
  });
  const grow = (p: number | undefined) =>
    Math.min(99, (p ?? 0) + Math.floor(tick / 2));
  let scope = $state<"this" | "all">("all");
  const agents = $derived(
    AGENTS.filter((a) => scope === "all" || a.session === session),
  );
  const tasks = $derived(
    TASKS.filter((t) => scope === "all" || t.session === session),
  );
  let termTask = $state(TASKS[0].id);
  const term = $derived(TASKS.find((t) => t.id === termTask)!);
  const art = $derived(ARTIFACTS.find((a) => a.id === artifact));
</script>

<div class="bg-panel @container flex h-full flex-col">
  <div
    class="flex h-9 shrink-0 items-center gap-0.5 overflow-x-auto border-b px-1.5"
    role="tablist"
    aria-label="Work area"
  >
    {#each TABS as t (t.id)}
      <button
        type="button"
        role="tab"
        aria-selected={tab === t.id}
        title={t.label}
        class={cn(
          "flex h-7 shrink-0 items-center gap-1.5 rounded-md px-2 text-xs",
          tab === t.id
            ? "bg-muted text-foreground"
            : "text-muted-foreground hover:text-foreground",
        )}
        onclick={() => (tab = t.id)}
        ><t.icon class="size-3.5" /><span class="hidden @[24rem]:inline"
          >{t.label}</span
        ></button
      >
    {/each}
  </div>

  <div class="min-h-0 flex-1 overflow-auto">
    {#if tab === "activity"}
      <div class="flex items-center gap-2 px-3 pt-3">
        <div class="bg-muted flex rounded-md p-0.5 text-xs" role="radiogroup">
          {#each [["all", "Everything"], ["this", "This session"]] as const as [v, label] (v)}
            <button
              type="button"
              role="radio"
              aria-checked={scope === v}
              class={cn(
                "h-6 rounded px-2",
                scope === v
                  ? "bg-background text-foreground shadow-sm"
                  : "text-muted-foreground",
              )}
              onclick={() => (scope = v)}>{label}</button
            >
          {/each}
        </div>
        <span class="text-muted-foreground ml-auto text-xs"
          >Runs on servers; closing QMX doesn't stop it</span
        >
      </div>
      <section class="px-3 pt-3">
        <h3 class="text-muted-foreground mb-1.5 text-xs font-semibold">
          Agents
        </h3>
        <ul class="flex flex-col gap-1.5">
          {#each agents as a (a.session + a.id)}
            <li class="rounded-lg border p-2.5">
              <div class="flex items-center gap-2">
                <span
                  class={cn(
                    "size-2 shrink-0 rounded-full",
                    a.state === "running"
                      ? "bg-info remote-pulse"
                      : "bg-success",
                  )}
                ></span>
                <span class="text-sm font-medium">{a.name}</span>
                <span class="text-muted-foreground truncate text-xs"
                  >{a.sessionTitle}</span
                >
                <span class="text-muted-foreground ml-auto shrink-0 text-[11px]"
                  >{a.where}</span
                >
              </div>
              <p class="mt-1 truncate text-xs">
                {a.state === "running" && a.progress !== undefined
                  ? `${a.last.replace(/\d+ of 1,000/, `${Math.round((grow(a.progress) / 100) * 1000)} of 1,000`)}`
                  : a.last}
              </p>
              {#if a.state === "running"}
                <div class="mt-1.5 flex items-center gap-2">
                  <div class="bg-muted h-1 flex-1 overflow-hidden rounded-full">
                    <span
                      class="bg-info block h-full transition-all duration-700"
                      style="width:{grow(a.progress)}%"
                    ></span>
                  </div>
                  <Button
                    size="icon-xs"
                    variant="ghost"
                    aria-label={`Stop ${a.name}`}
                    title="Stop this agent"
                    onclick={() =>
                      workbench.notify(
                        `Stopping ${a.name} needs the daemon; its work so far is kept.`,
                      )}><Square /></Button
                  >
                </div>
              {/if}
            </li>
          {:else}
            <li class="text-muted-foreground text-sm">
              No agents in this session.
            </li>
          {/each}
        </ul>
      </section>
      <section class="px-3 py-3">
        <h3 class="text-muted-foreground mb-1.5 text-xs font-semibold">
          Background jobs
        </h3>
        <ul class="flex flex-col gap-1.5">
          {#each tasks as t (t.id)}
            <li class="rounded-lg border p-2.5">
              <div class="flex items-center gap-2">
                {#if t.state === "running"}<span
                    class="bg-info remote-pulse size-2 shrink-0 rounded-full"
                  ></span>{:else if t.state === "waiting"}<span
                    class="bg-warning size-2 shrink-0 rounded-full"
                  ></span>{:else}<Clock
                    class="text-muted-foreground size-3.5 shrink-0"
                  />{/if}
                <span class="min-w-0 flex-1 truncate text-sm">{t.name}</span>
                <span class="text-muted-foreground shrink-0 text-[11px]"
                  >{t.where}</span
                >
              </div>
              <p class="text-muted-foreground mt-1 truncate text-xs">
                {t.log[t.log.length - 1]}
              </p>
              {#if t.state === "running"}
                <div class="bg-muted mt-1.5 h-1 overflow-hidden rounded-full">
                  <span
                    class="bg-info block h-full transition-all duration-700"
                    style="width:{grow(t.progress)}%"
                  ></span>
                </div>
              {/if}
              <div class="mt-1.5 flex gap-1">
                <Button
                  size="xs"
                  variant="ghost"
                  onclick={() => {
                    termTask = t.id;
                    tab = "terminal";
                  }}><SquareTerminal />Output</Button
                >
              </div>
            </li>
          {/each}
        </ul>
      </section>
    {:else if tab === "artifacts"}
      <ul class="flex flex-col gap-1.5 p-3">
        {#each ARTIFACTS as a (a.id)}
          <li>
            <button
              type="button"
              class="hover:bg-muted flex w-full items-center gap-3 rounded-lg border p-2.5 text-left"
              onclick={() => {
                artifact = a.id;
                tab = "preview";
              }}
            >
              <FileText class="text-primary size-4 shrink-0" />
              <span class="min-w-0 flex-1">
                <span class="block truncate text-sm">{a.title}</span>
                <span class="text-muted-foreground text-xs"
                  >{a.type} · {SESSIONS.find((s) => s.id === a.session)
                    ?.title}</span
                >
              </span>
            </button>
          </li>
        {/each}
      </ul>
    {:else if tab === "terminal"}
      <div class="flex h-full flex-col">
        <select
          class="m-2 h-7 rounded-md border px-2 text-xs"
          aria-label="Job"
          bind:value={termTask}
        >
          {#each TASKS as t (t.id)}<option value={t.id}>{t.name}</option>{/each}
        </select>
        <pre
          class="mx-2 min-h-0 flex-1 overflow-auto rounded-md bg-black/80 p-3 font-mono text-xs leading-relaxed text-green-300">{term.log
            .map((l) => `${term.where} $ ${l}`)
            .join("\n")}{term.state === "running" ? "\n▍" : ""}</pre>
        <div class="m-2 flex items-center gap-2">
          <input
            class="bg-background/40 h-8 min-w-0 flex-1 rounded-md border px-2 font-mono text-xs"
            placeholder="qmx> commands run through the daemon"
            aria-label="Command"
            disabled
          />
        </div>
      </div>
    {:else if tab === "preview" && art}
      <div class="flex h-full flex-col gap-3 p-3">
        <div>
          <p class="text-muted-foreground text-xs">{art.type}</p>
          <h3 class="text-lg font-semibold">{art.title}</h3>
        </div>
        <div class="grid grid-cols-2 gap-2 text-sm">
          {#each [["Profit, 2 years", "+$5,460", "+$5,840"], ["Worst weekend", "−$560", "−$1,240"], ["FTX week", "−$1,100", "−$2,200"], ["Kill-line risk", "1.4%", "2.1%"]] as [k, a, b] (k)}
            <div class="rounded-lg border p-2.5">
              <p class="text-muted-foreground text-xs">{k}</p>
              <p class="num font-semibold">
                {a}<span class="text-muted-foreground ml-2 font-normal"
                  >vs {b}</span
                >
              </p>
            </div>
          {/each}
        </div>
        <p class="text-muted-foreground text-xs">
          Weekend rider first, Trend rider second. A real report is an
          interactive page the copilot builds; this is its summary.
        </p>
      </div>
    {:else}
      <EmptyState
        class="h-full"
        icon={tab === "browser" ? Globe : AppWindow}
        title={tab === "browser" ? "No page open" : "Nothing to preview"}
        description={tab === "browser"
          ? "Pages the copilot reads, or that you open, show here inside QMX."
          : "Open an artifact, a mini app or a report to see it here."}
      />
    {/if}
  </div>
</div>
