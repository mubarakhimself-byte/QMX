<script lang="ts">
  /**
   * The copilot's right panel, as in T3 Code, Codex and bb: Activity (every
   * sub-agent and background job, where it runs, open its thread, stop),
   * Artifacts with a real preview of each, Diff (what a session changed),
   * Terminal (per job; commands go through the daemon once connected), and
   * an in-app Browser with an address bar. Jobs run on servers, so they
   * carry on when QMX or this laptop closes.
   */
  import { onMount } from "svelte";
  import Activity from "@lucide/svelte/icons/activity";
  import FileText from "@lucide/svelte/icons/file-text";
  import FileDiff from "@lucide/svelte/icons/file-diff";
  import Globe from "@lucide/svelte/icons/globe";
  import SquareTerminal from "@lucide/svelte/icons/square-terminal";
  import Square from "@lucide/svelte/icons/square";
  import Clock from "@lucide/svelte/icons/clock";
  import RotateCw from "@lucide/svelte/icons/rotate-cw";
  import { Button } from "$lib/components/ui/button";
  import SpecView from "$lib/sdk/SpecView.svelte";
  import { cn } from "$lib/utils";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { ARTIFACTS, TASKS } from "./demo";
  import { copilot } from "./store.svelte";

  let {
    tab = $bindable("activity"),
    artifact = $bindable<string | null>(null),
    session,
    onopenagent,
  }: {
    tab?: string;
    artifact?: string | null;
    session: string | null;
    onopenagent?: (sessionId: string) => void;
  } = $props();

  const TABS = [
    { id: "activity", label: "Helpers and jobs", icon: Activity },
    { id: "preview", label: "Reports", icon: FileText },
    { id: "diff", label: "Changes", icon: FileDiff },
    { id: "terminal", label: "Terminal", icon: SquareTerminal },
    { id: "browser", label: "Browser", icon: Globe },
  ];

  let tick = $state(0);
  onMount(() => {
    const t = setInterval(() => tick++, 2500);
    return () => clearInterval(t);
  });
  const grow = (p: number | undefined) =>
    Math.min(99, (p ?? 0) + Math.floor(tick / 2));

  let scope = $state<"this" | "all">("all");
  const root = $derived(
    session ? (copilot.session(session)?.parent ?? session) : null,
  );
  const agents = $derived(
    copilot.sessions.filter(
      (s) => s.parent && (scope === "all" || s.parent === root),
    ),
  );
  const tasks = $derived(
    TASKS.filter((t) => scope === "all" || t.session === root),
  );

  // Terminal: one per job; typed commands are kept but run only via the daemon.
  let termTask = $state(TASKS[0].id);
  let typed = $state<Record<string, string[]>>({});
  let command = $state("");
  const term = $derived(TASKS.find((t) => t.id === termTask)!);
  function run(e: SubmitEvent) {
    e.preventDefault();
    const c = command.trim();
    if (!c) return;
    typed[termTask] = [
      ...(typed[termTask] ?? []),
      `${term.where} $ ${c}`,
      "  (demo) runs on the server through the daemon once connected",
    ];
    command = "";
  }

  // Diff: what the weekend session changed (Trend rider v2 → Weekend rider v1).
  const DIFF: { t: " " | "+" | "-"; line: string }[] = [
    { t: "-", line: "pod: Trend rider" },
    { t: "+", line: "pod: Weekend rider" },
    { t: "-", line: "version: v2" },
    { t: "+", line: "version: v1" },
    { t: " ", line: "stack:" },
    { t: " ", line: "  inputs: [regime-input, vol-input]" },
    { t: " ", line: "  guards: [kill, brakes, news-kill]" },
    { t: " ", line: "  allocator: [equal]" },
    { t: " ", line: "  sizer: [fixed-frac]" },
    { t: "-", line: "  throttles: [regime, vol-spike]" },
    { t: "+", line: "  throttles: [regime, vol-spike, thin-hours]" },
    {
      t: "+",
      line: "  thin-hours: {factor: 0.5, from: Fri 20:00, to: Sun 20:00, zone: UTC}",
    },
    { t: " ", line: "  caps: [caps, corr-cap]" },
    { t: " ", line: "  ledger: [ledger-usd]" },
  ];

  // Browser: an address bar over an in-app page.
  let address = $state("https://arxiv.org/list/q-fin/new");
  let shown = $state("https://arxiv.org/list/q-fin/new");
  let reload = $state(0);

  const art = $derived(ARTIFACTS.find((a) => a.id === artifact));
</script>

<div class="bg-panel @container flex h-full flex-col">
  <div
    class="flex h-11 shrink-0 items-center gap-0.5 overflow-x-auto border-b pr-11 pl-1.5"
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
          "flex h-8 shrink-0 items-center gap-1.5 rounded-md px-2.5 text-sm",
          tab === t.id
            ? "bg-muted text-foreground"
            : "text-muted-foreground hover:text-foreground",
        )}
        onclick={() => (tab = t.id)}
        ><t.icon class="size-4" /><span class="hidden @[20rem]:inline"
          >{t.label}</span
        ></button
      >
    {/each}
  </div>

  <div class="min-h-0 flex-1 overflow-auto">
    {#if tab === "activity"}
      <div class="flex items-center gap-2 px-3 pt-3">
        <div class="bg-muted flex rounded-md p-0.5 text-sm" role="radiogroup">
          {#each [["all", "Everything"], ["this", "This session"]] as const as [v, label] (v)}
            <button
              type="button"
              role="radio"
              aria-checked={scope === v}
              class={cn(
                "h-7 rounded px-2.5",
                scope === v
                  ? "bg-background text-foreground shadow-sm"
                  : "text-muted-foreground",
              )}
              onclick={() => (scope = v)}>{label}</button
            >
          {/each}
        </div>
      </div>
      <section class="px-3 pt-3">
        <h3 class="text-muted-foreground mb-1.5 text-sm font-semibold">
          Sub-agents
        </h3>
        <ul class="flex flex-col gap-1.5">
          {#each agents as a (a.id)}
            <li class="rounded-lg border p-2.5">
              <div class="flex items-center gap-2">
                <span
                  class={cn(
                    "size-2 shrink-0 rounded-full",
                    a.status === "running"
                      ? "bg-info remote-pulse"
                      : "bg-success",
                  )}
                ></span>
                <button
                  type="button"
                  class="min-w-0 flex-1 truncate text-left text-sm font-medium hover:underline"
                  onclick={() => onopenagent?.(a.id)}>{a.title}</button
                >
                {#if a.status === "running"}
                  <Button
                    size="icon-xs"
                    variant="ghost"
                    aria-label="Stop this agent"
                    title="Stop this agent (its work so far is kept)"
                    onclick={() =>
                      workbench.notify(
                        "Stopping an agent needs the daemon; its work so far is kept.",
                      )}><Square /></Button
                  >
                {/if}
              </div>
              <p class="text-muted-foreground mt-0.5 truncate text-sm">
                From: {copilot.session(a.parent ?? null)?.title} · {a.age}
              </p>
            </li>
          {:else}
            <li class="text-muted-foreground text-sm">No sub-agents here.</li>
          {/each}
        </ul>
      </section>
      <section class="px-3 py-3">
        <h3 class="text-muted-foreground mb-1.5 text-sm font-semibold">
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
                <span class="text-muted-foreground shrink-0 text-xs"
                  >{t.where}</span
                >
              </div>
              <p class="text-muted-foreground mt-1 truncate text-sm">
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
              <Button
                size="xs"
                variant="ghost"
                class="mt-1"
                onclick={() => {
                  termTask = t.id;
                  tab = "terminal";
                }}><SquareTerminal />Output</Button
              >
            </li>
          {/each}
        </ul>
      </section>
    {:else if tab === "preview"}
      <ul class="flex flex-col gap-1.5 p-3">
        {#each ARTIFACTS as a (a.id)}
          <li>
            <button
              type="button"
              class={cn(
                "hover:bg-muted flex w-full items-center gap-3 rounded-lg border p-2.5 text-left",
                artifact === a.id && "border-primary bg-primary/8",
              )}
              onclick={() => (artifact = a.id)}
            >
              <FileText class="text-primary size-4 shrink-0" />
              <span class="min-w-0 flex-1">
                <span class="block truncate text-sm">{a.title}</span>
                <span class="text-muted-foreground text-sm"
                  >{a.type} · {copilot.session(a.session)?.title}</span
                >
              </span>
            </button>
          </li>
        {/each}
      </ul>
      {#if art}
        <div class="border-t p-3">
          {#if art.spec}
            <SpecView spec={art.spec} />
          {:else}
            <h3 class="text-base font-semibold">{art.title}</h3>
            <p class="text-muted-foreground mt-1 text-sm">
              {art.type}. Its full content opens here once the daemon stores it;
              the copilot saves it to the Library.
            </p>
          {/if}
        </div>
      {/if}
    {:else if tab === "diff"}
      <div class="p-3">
        <p class="mb-2 text-sm">
          <span class="font-medium">Trend rider v2 → Weekend rider v1</span>
          <span class="text-muted-foreground"> · from “Weekend-safe pod”</span>
        </p>
        <pre
          class="overflow-x-auto rounded-lg border font-mono text-sm leading-6">{#each DIFF as d, i (i)}<span
              class={cn(
                "block px-3",
                d.t === "+" && "bg-success/12 text-success",
                d.t === "-" && "bg-destructive/12 text-destructive",
              )}>{d.t} {d.line}</span
            >{/each}</pre>
        <div class="mt-2 flex gap-2">
          <Button
            size="sm"
            variant="outline"
            onclick={() =>
              workbench.notify(
                "Comment on a line and the copilot reads it on its next turn (needs the daemon).",
              )}>Comment</Button
          >
          <Button
            size="sm"
            variant="ghost"
            onclick={() =>
              workbench.notify("Reverting a draft change needs the daemon.")}
            >Revert</Button
          >
        </div>
      </div>
    {:else if tab === "terminal"}
      <div class="flex h-full flex-col">
        <div class="flex gap-1 overflow-x-auto border-b px-2 py-1.5">
          {#each TASKS as t (t.id)}
            <button
              type="button"
              class={cn(
                "shrink-0 rounded px-2 py-1 text-sm",
                termTask === t.id
                  ? "bg-muted text-foreground"
                  : "text-muted-foreground hover:text-foreground",
              )}
              title={t.name}
              onclick={() => (termTask = t.id)}
              >{t.name.split(":")[0]} · {t.where}</button
            >
          {/each}
        </div>
        <pre
          class="m-2 min-h-0 flex-1 overflow-auto rounded-md bg-black/85 p-3 font-mono text-sm leading-relaxed text-green-300">{[
            ...term.log.map((l) => `${term.where} $ ${l}`),
            ...(typed[termTask] ?? []),
          ].join("\n")}{term.state === "running" ? "\n▍" : ""}</pre>
        <form class="m-2 mt-0 flex items-center gap-2" onsubmit={run}>
          <span class="text-muted-foreground font-mono text-sm"
            >{term.where} $</span
          >
          <input
            class="bg-background/40 h-8 min-w-0 flex-1 rounded-md border px-2 font-mono text-sm"
            placeholder="type a command"
            aria-label="Command"
            bind:value={command}
          />
        </form>
      </div>
    {:else if tab === "browser"}
      <div class="flex h-full flex-col">
        <form
          class="flex items-center gap-1.5 border-b p-1.5"
          onsubmit={(e) => {
            e.preventDefault();
            shown = /^https?:\/\//.test(address)
              ? address
              : `https://${address}`;
          }}
        >
          <Button
            size="icon-sm"
            variant="ghost"
            type="button"
            aria-label="Reload"
            onclick={() => reload++}><RotateCw /></Button
          >
          <input
            class="bg-background/40 h-8 min-w-0 flex-1 rounded-md border px-2 font-mono text-sm"
            aria-label="Address"
            bind:value={address}
          />
        </form>
        {#key `${shown}-${reload}`}
          <iframe
            title="In-app browser"
            src={shown}
            class="bg-background min-h-0 w-full flex-1"
            sandbox="allow-scripts allow-same-origin allow-popups allow-forms"
            referrerpolicy="no-referrer"
          ></iframe>
        {/key}
        <p class="text-muted-foreground border-t px-3 py-1.5 text-sm">
          Some sites refuse to show inside other apps; the desktop app gives the
          copilot a real browser it can drive, with stop and take over.
        </p>
      </div>
    {/if}
  </div>
</div>
