<script lang="ts">
  /**
   * A copilot session drawn block by block: your messages with what you
   * attached, its plan as a checklist, the sub-agents it handed work to,
   * tool calls, what it changed elsewhere in QMX (with links), things it
   * made, questions it needs you to answer, and actions that need your yes.
   * The shapes match what the daemon will stream.
   */
  import Check from "@lucide/svelte/icons/check";
  import Wrench from "@lucide/svelte/icons/wrench";
  import Paperclip from "@lucide/svelte/icons/paperclip";
  import ListChecks from "@lucide/svelte/icons/list-checks";
  import Users from "@lucide/svelte/icons/users";
  import ArrowUpRight from "@lucide/svelte/icons/arrow-up-right";
  import FileText from "@lucide/svelte/icons/file-text";
  import CircleHelp from "@lucide/svelte/icons/circle-help";
  import ShieldCheck from "@lucide/svelte/icons/shield-check";
  import Clock from "@lucide/svelte/icons/clock";
  import LoaderCircle from "@lucide/svelte/icons/loader-circle";
  import CircleDot from "@lucide/svelte/icons/circle-dot";
  import Copy from "@lucide/svelte/icons/copy";
  import LibraryBig from "@lucide/svelte/icons/library-big";
  import Shuffle from "@lucide/svelte/icons/shuffle";
  import { resolve } from "$app/paths";
  import { Button } from "$lib/components/ui/button";
  import EntityCard from "$lib/qmx/EntityCard.svelte";
  import { cn } from "$lib/utils";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import Pin from "@lucide/svelte/icons/pin";
  import SpecView from "$lib/sdk/SpecView.svelte";
  import type { Block, StepState } from "./demo";

  let {
    blocks,
    onartifact,
    onagent,
    oncontinue,
    onresolve,
    answers,
    onanswer,
    onopenagent,
    onpanel,
    compact = false,
  }: {
    blocks: Block[];
    /** Narrow side columns: less padding, smaller text. */
    compact?: boolean;
    onartifact?: (id: string) => void;
    onagent?: () => void;
    oncontinue?: () => void;
    /** A question or permission card was answered. */
    onresolve?: () => void;
    /** Answers kept by the session store (so the composer can take over). */
    answers?: Record<number, string>;
    onanswer?: (index: number, value: string) => void;
    /** Open a sub-agent's own thread. */
    onopenagent?: (agentId: string) => void;
    /** Keep, discard or pin a draft panel. */
    onpanel?: (index: number, state: "kept" | "discarded" | "pinned") => void;
  } = $props();

  let local = $state<Record<number, string>>({});
  const got = $derived(answers ?? local);
  function answer(i: number, v: string) {
    if (got[i]) return;
    if (onanswer) onanswer(i, v);
    else local[i] = v;
    onresolve?.();
  }
  let other = $state<Record<number, string>>({});

  const STEP: Record<
    StepState,
    { icon: typeof Check; tone: string; label: string }
  > = {
    done: { icon: Check, tone: "text-success", label: "Done" },
    running: { icon: LoaderCircle, tone: "text-info", label: "Working" },
    waiting: {
      icon: CircleDot,
      tone: "text-warning",
      label: "Waiting for you",
    },
    scheduled: {
      icon: Clock,
      tone: "text-muted-foreground",
      label: "Scheduled",
    },
  };
  const hrefOf = (path: string, query?: string) =>
    `${resolve(path as "/")}${query ? `?${query}` : ""}`;
  const head =
    "text-muted-foreground mb-2 flex items-center gap-2 text-xs font-medium";
</script>

<div
  class={cn(
    "mx-auto flex max-w-4xl flex-col leading-relaxed",
    compact ? "gap-3 px-3 py-3 text-sm" : "gap-4 px-6 py-6 text-[15px]",
  )}
>
  {#each blocks as b, i (i)}
    {#if b.kind === "user"}
      <div class="ml-auto flex max-w-[85%] flex-col items-end gap-1.5">
        <div class="bg-muted rounded-xl px-3.5 py-2">{b.text}</div>
        {#if b.attached?.length}
          <ul class="flex flex-wrap justify-end gap-1">
            {#each b.attached as a (a)}
              <li
                class="text-muted-foreground flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs"
              >
                <Paperclip class="size-3" />{a}
              </li>
            {/each}
          </ul>
        {/if}
      </div>
    {:else if b.kind === "text"}
      <div>
        <p>{b.text}</p>
        {#if b.demo}<span
            class="text-muted-foreground mt-1 inline-block rounded border px-1.5 text-xs"
            >Demo reply · scripted, no model connected</span
          >{/if}
      </div>
    {:else if b.kind === "handoff"}
      <div
        class="border-info/40 bg-info/8 flex flex-wrap items-center gap-3 rounded-lg border px-3 py-2 text-sm"
      >
        <Shuffle class="text-info size-4 shrink-0" />
        <span class="min-w-0 flex-1">{b.note}</span>
        {#if oncontinue}
          <Button size="sm" variant="outline" onclick={oncontinue}
            >Continue here</Button
          >
        {/if}
      </div>
    {:else if b.kind === "plan"}
      <section class="rounded-xl border p-3">
        <p class={head}><ListChecks class="size-3.5" />{b.title}</p>
        <ol class="flex flex-col gap-1.5">
          {#each b.steps as s, k (k)}
            {@const st = STEP[s.state]}
            <li class="flex items-start gap-2.5 text-sm">
              <st.icon
                class={cn(
                  "mt-0.5 size-4 shrink-0",
                  st.tone,
                  s.state === "running" && "animate-spin",
                )}
              />
              <span
                class={cn(
                  "min-w-0 flex-1",
                  s.state === "done" && "text-muted-foreground",
                )}>{s.text}</span
              >
              {#if s.where}<span
                  class="text-muted-foreground shrink-0 rounded border px-1.5 text-xs"
                  >{s.where}</span
                >{/if}
            </li>
          {/each}
        </ol>
      </section>
    {:else if b.kind === "agents"}
      <section class="rounded-xl border p-3">
        <p class={head}>
          <Users class="size-3.5" />Working with {b.agents.length} sub-agents
          {#if onagent}<button
              type="button"
              class="text-primary ml-auto font-normal"
              onclick={onagent}>Watch them</button
            >{/if}
        </p>
        <ul class="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
          {#each b.agents as a (a.id)}
            <li
              class="bg-background/40 hover:border-ring/60 relative rounded-lg border p-2.5"
            >
              {#if onopenagent}<button
                  type="button"
                  class="absolute inset-0 rounded-lg"
                  aria-label={`Open ${a.name}'s thread`}
                  onclick={() => onopenagent(a.id)}
                ></button>{/if}
              <div class="flex items-center gap-2">
                <span
                  class={cn(
                    "size-2 rounded-full",
                    a.state === "running"
                      ? "bg-info remote-pulse"
                      : "bg-success",
                  )}
                ></span>
                <span class="text-sm font-medium">{a.name}</span>
                <span class="text-muted-foreground ml-auto text-xs"
                  >{a.where}</span
                >
              </div>
              <p class="text-muted-foreground text-xs">{a.role}</p>
              <p class="mt-1 truncate text-xs">{a.last}</p>
              {#if a.progress !== undefined && a.state === "running"}
                <div class="bg-muted mt-1.5 h-1 overflow-hidden rounded-full">
                  <span class="bg-info block h-full" style="width:{a.progress}%"
                  ></span>
                </div>
              {/if}
            </li>
          {/each}
        </ul>
      </section>
    {:else if b.kind === "tools"}
      <details class="rounded-lg border">
        <summary
          class="text-muted-foreground flex cursor-pointer items-center gap-2 px-3 py-2 text-sm"
        >
          <Wrench class="size-3.5" /> Used {b.calls.length}
          {b.calls.length === 1 ? "tool" : "tools"} ·
          <span class="num"
            >{(b.calls.reduce((t, c) => t + c.ms, 0) / 1000).toFixed(1)}s</span
          >
        </summary>
        <ul
          class="flex flex-col gap-1.5 border-t px-3 py-2.5 font-mono text-[13px]"
        >
          {#each b.calls as t, k (k)}
            <li class="flex items-center gap-2">
              <Check class="text-success size-3.5 shrink-0" />
              <span class="font-medium">{t.name}</span>
              <span class="text-muted-foreground truncate">{t.args}</span>
              <span class="text-muted-foreground ml-auto shrink-0"
                >{(t.ms / 1000).toFixed(1)}s</span
              >
            </li>
          {/each}
        </ul>
      </details>
    {:else if b.kind === "changes"}
      <section class="rounded-xl border p-3">
        <p class={head}>Changed elsewhere in QMX</p>
        <ul class="flex flex-col gap-1">
          <!-- eslint-disable svelte/no-navigation-without-resolve -->
          {#each b.changes as c, k (k)}
            <li>
              <a
                href={hrefOf(c.path, c.query)}
                class="hover:bg-muted flex items-center gap-2 rounded-md px-2 py-1.5 text-sm"
              >
                <span class="text-muted-foreground w-16 shrink-0 text-xs"
                  >{c.place}</span
                >
                <span class="min-w-0 flex-1 truncate">{c.what}</span>
                <ArrowUpRight class="text-muted-foreground size-3.5" />
              </a>
            </li>
          {/each}
          <!-- eslint-enable svelte/no-navigation-without-resolve -->
        </ul>
      </section>
    {:else if b.kind === "artifact"}
      <section
        class="flex items-center gap-3 rounded-xl border p-3"
        aria-label={b.title}
      >
        <span
          class="bg-primary/15 text-primary flex size-10 shrink-0 items-center justify-center rounded-lg"
          ><FileText class="size-5" /></span
        >
        <div class="min-w-0 flex-1">
          <p class="truncate text-sm font-medium">{b.title}</p>
          <p class="text-muted-foreground truncate text-xs">
            {b.type} · {b.note}
          </p>
        </div>
        <Button size="sm" variant="outline" onclick={() => onartifact?.(b.id)}
          >Open</Button
        >
        <Button
          size="icon-sm"
          variant="ghost"
          aria-label="Save to the Library"
          title="Save to the Library"
          onclick={() =>
            workbench.notify(
              `${b.title} would be filed in the Library (needs the daemon).`,
            )}><LibraryBig /></Button
        >
      </section>
    {:else if b.kind === "table"}
      <section class="surface overflow-hidden rounded-lg">
        <div class="flex h-8 items-center border-b pr-1 pl-3">
          <span class="text-muted-foreground text-xs font-medium"
            >{b.title}</span
          >
          <Button
            size="icon-xs"
            variant="ghost"
            class="ml-auto"
            aria-label="Copy table"
            onclick={() =>
              navigator.clipboard
                ?.writeText(
                  [b.head, ...b.rows].map((r) => r.join("\t")).join("\n"),
                )
                .then(() => workbench.notify("Table copied."))}><Copy /></Button
          >
        </div>
        <table class="w-full text-sm">
          <thead class="text-muted-foreground text-left">
            <tr>
              {#each b.head as h, k (k)}<th
                  class={cn("px-4 py-2 font-medium", k && "text-right")}>{h}</th
                >{/each}
            </tr>
          </thead>
          <tbody>
            {#each b.rows as r, k (k)}
              <tr class="border-t">
                {#each r as c, n (n)}<td
                    class={cn("px-4 py-2", n && "num text-right")}>{c}</td
                  >{/each}
              </tr>
            {/each}
          </tbody>
        </table>
      </section>
    {:else if b.kind === "cards"}
      <div class="grid gap-3 sm:grid-cols-2">
        <div>
          <p class="text-muted-foreground mb-1.5 text-xs">
            Before · {b.before.version}
          </p>
          <EntityCard
            entity={b.before}
            compact
            href={resolve("/library/[id]", { id: b.before.id })}
          />
        </div>
        <div>
          <p class="text-muted-foreground mb-1.5 text-xs">
            Draft edit · not run
          </p>
          <EntityCard
            entity={b.after}
            compact
            href={resolve("/library/[id]", { id: b.before.id })}
            changed={b.changed}
          />
        </div>
      </div>
    {:else if b.kind === "ask"}
      <section class="border-warning/50 rounded-xl border p-3">
        <p class={cn(head, "text-foreground text-sm")}>
          <CircleHelp class="text-warning size-4" />{b.question}
        </p>
        {#if got[i]}
          <p class="text-sm">
            <Check class="text-success mr-1 inline size-4" />You chose
            <span class="font-medium">{got[i]}</span>. It carries on with that.
          </p>
        {:else}
          <div class="grid gap-1.5">
            {#each b.options as o (o.label)}
              <button
                type="button"
                class="hover:border-ring/60 hover:bg-muted/40 flex flex-col rounded-lg border px-3 py-2 text-left"
                onclick={() => answer(i, o.label)}
              >
                <span class="text-sm font-medium"
                  >{o.label}{#if o.recommended}<span
                      class="text-primary ml-2 text-xs font-normal"
                      >Suggested</span
                    >{/if}</span
                >
                <span class="text-muted-foreground text-xs">{o.note}</span>
              </button>
            {/each}
            <form
              class="flex gap-1.5"
              onsubmit={(e) => {
                e.preventDefault();
                if (other[i]?.trim()) answer(i, other[i].trim());
              }}
            >
              <input
                class="bg-background/40 h-8 min-w-0 flex-1 rounded-md border px-2 text-sm"
                placeholder="Something else…"
                aria-label="Your own answer"
                bind:value={other[i]}
              />
              <Button size="sm" type="submit" variant="outline">Answer</Button>
            </form>
          </div>
        {/if}
      </section>
    {:else if b.kind === "permission"}
      <section class="border-primary/50 rounded-xl border p-3">
        <p class={cn(head, "text-foreground text-sm")}>
          <ShieldCheck class="text-primary size-4" />Needs your yes: {b.action}
        </p>
        <p class="text-sm">{b.detail}</p>
        <p class="text-muted-foreground mt-1 text-xs">{b.guard}</p>
        {#if got[i]}
          <p class="mt-2 text-sm">
            <Check class="text-success mr-1 inline size-4" />{got[i]}. In the
            demo nothing runs.
          </p>
        {:else}
          <div class="mt-2.5 flex flex-wrap gap-2">
            <Button size="sm" onclick={() => answer(i, "Allowed once")}
              >Allow</Button
            >
            <Button
              size="sm"
              variant="outline"
              onclick={() => answer(i, "Allowed for the rest of this session")}
              >Allow for this session</Button
            >
            <Button
              size="sm"
              variant="ghost"
              onclick={() => answer(i, "Not now; it will ask again later")}
              >Not now</Button
            >
          </div>
        {/if}
      </section>
    {:else if b.kind === "panel"}
      <section
        class={cn(
          "rounded-xl border",
          b.state === "draft" && "border-primary/50",
          b.state === "discarded" && "opacity-50",
        )}
      >
        <div class="flex flex-wrap items-center gap-2 border-b px-3 py-2">
          <span class="text-sm font-medium">{b.spec.title}</span>
          <span class="text-muted-foreground text-[13px]"
            >{b.state === "draft"
              ? "Draft panel"
              : b.state === "kept"
                ? "Kept in this session"
                : b.state === "pinned"
                  ? "Pinned to the Lab"
                  : "Thrown away"}</span
          >
          {#if b.state === "draft" && onpanel}
            <div class="ml-auto flex gap-1.5">
              <Button size="sm" onclick={() => onpanel(i, "pinned")}
                ><Pin />Pin to the Lab</Button
              >
              <Button
                size="sm"
                variant="outline"
                onclick={() => onpanel(i, "kept")}>Keep here</Button
              >
              <Button
                size="sm"
                variant="ghost"
                onclick={() => onpanel(i, "discarded")}>Throw away</Button
              >
            </div>
          {/if}
        </div>
        {#if b.state !== "discarded"}
          <div class="p-3">
            <SpecView
              spec={b.spec}
              onaction={(op) =>
                workbench.notify(`The panel asked the host to run ${op}.`)}
            />
          </div>
        {/if}
      </section>
    {/if}
  {/each}
</div>
