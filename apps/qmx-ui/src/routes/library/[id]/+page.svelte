<script lang="ts">
  import { resolve } from "$app/paths";
  import ArrowLeft from "@lucide/svelte/icons/arrow-left";
  import MessageSquarePlus from "@lucide/svelte/icons/message-square-plus";
  import Workflow from "@lucide/svelte/icons/workflow";
  import ShieldCheck from "@lucide/svelte/icons/shield-check";
  import Play from "@lucide/svelte/icons/play";
  import Check from "@lucide/svelte/icons/check";
  import FlaskConical from "@lucide/svelte/icons/flask-conical";
  import * as Tabs from "$lib/components/ui/tabs";
  import { Button } from "$lib/components/ui/button";
  import { Badge } from "$lib/components/ui/badge";
  import { Input } from "$lib/components/ui/input";
  import EmptyState from "$lib/workbench/EmptyState.svelte";
  import CoverArt from "$lib/qmx/CoverArt.svelte";
  import Sparkline from "$lib/demo/Sparkline.svelte";
  import { KIND_LABEL, PIPELINE } from "$lib/qmx/entities";
  import { DEMO_ARTIFACTS } from "$lib/demo/assets";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { cn } from "$lib/utils";

  let { data } = $props();
  const e = $derived(data.entity);

  const tabs = $derived.by(() => {
    if (!e) return [];
    const t = ["Overview"];
    if (e.evidence) t.push("Evidence");
    if (e.journal) t.push("Journal");
    if (e.connections) t.push("Connections");
    if (e.slots) t.push("Slots");
    if (e.ops) t.push("Operations");
    if (e.steps) t.push("Steps");
    if (e.artifacts?.length) t.push("Artifacts");
    return t;
  });
  let tab = $state("Overview");
  const stageIndex = $derived(e ? PIPELINE.indexOf(e.stage) : -1);
  const headless = $derived(e?.kind === "app" && (e.views?.length ?? 0) === 0);
  const linked = $derived(
    DEMO_ARTIFACTS.filter((a) => e?.artifacts?.includes(a.id)),
  );
  const ROLE_TONE = {
    confirmation: "text-success",
    trial: "text-muted-foreground",
    replicate: "text-info",
  };
</script>

<svelte:head
  ><title>{e?.name ?? "Not found"} · Library · QMX</title></svelte:head
>

{#if !e}
  <EmptyState
    class="h-full"
    title="Not in the Library"
    description="This item does not exist or was removed. Removed items keep a tombstone once the daemon is connected."
  />
{:else}
  <div class="h-full overflow-auto">
    <div class="bg-warning/15 flex h-7 items-center gap-2 px-3 text-xs">
      <FlaskConical class="text-warning size-3.5" /> Demo item. Sample numbers; nothing
      here is evidence.
    </div>
    <div class="relative">
      <CoverArt
        kind={e.kind}
        seed={e.id}
        series={e.spark}
        steps={e.steps?.length ?? 0}
        class="h-44 w-full"
      />
      <div
        class="from-background absolute inset-0 bg-linear-to-t to-transparent"
      ></div>
      <a
        href={resolve("/library")}
        class="bg-background/70 hover:bg-background absolute top-3 left-3 flex items-center gap-1 rounded-md px-2 py-1 text-sm backdrop-blur"
      >
        <ArrowLeft class="size-4" /> Library
      </a>
    </div>

    <div class="mx-auto -mt-14 flex max-w-6xl flex-col gap-5 px-6 pb-10">
      <header class="relative flex flex-wrap items-end gap-4">
        <div class="min-w-0 flex-1">
          <p class="panel-label">
            {KIND_LABEL[e.kind]}{headless ? " · headless" : ""} · {e.family ??
              e.version}
          </p>
          <h1 class="text-3xl font-semibold tracking-tight">{e.name}</h1>
          <p class="text-muted-foreground mt-1 text-[15px]">{e.summary}</p>
          <p class="text-muted-foreground num mt-1 text-xs">
            {e.version} · {e.fp}
          </p>
        </div>
        <div class="flex flex-wrap gap-2">
          <Button onclick={() => workbench.addRef(e.name)}
            ><MessageSquarePlus /> Add to copilot</Button
          >
          {#if e.kind !== "app"}
            <Button variant="outline" href={resolve("/authoring")}
              ><Workflow /> Open in Authoring</Button
            >
          {/if}
          {#if e.kind === "bot" && (e.stage === "Evidence" || e.stage === "Paper")}
            <Button
              variant="outline"
              aria-disabled="true"
              class="aria-disabled:opacity-60"
              title="Promotion is a signed card you approve on the trading node; needs the daemon"
              onclick={(ev) => ev.preventDefault()}
            >
              <ShieldCheck /> Promote…
            </Button>
          {/if}
        </div>
      </header>

      {#if e.kind === "bot"}
        <ol
          class="surface flex items-center gap-2 overflow-x-auto rounded-xl p-3"
          aria-label="Pipeline"
        >
          {#each PIPELINE as s, i (s)}
            <li class="flex items-center gap-2">
              <span
                class={cn(
                  "flex size-6 items-center justify-center rounded-full border text-xs",
                  i < stageIndex &&
                    "bg-success/20 border-success/40 text-success",
                  i === stageIndex &&
                    "bg-primary text-primary-foreground border-transparent",
                  i > stageIndex && "text-muted-foreground",
                )}
              >
                {#if i < stageIndex}<Check class="size-3.5" />{:else}{i +
                    1}{/if}
              </span>
              <span
                class={cn(
                  "text-sm whitespace-nowrap",
                  i === stageIndex ? "font-semibold" : "text-muted-foreground",
                )}>{s}</span
              >
              {#if i < PIPELINE.length - 1}<span class="bg-border h-px w-8"
                ></span>{/if}
            </li>
          {/each}
          <li
            class="text-muted-foreground ml-auto pl-4 text-xs whitespace-nowrap"
          >
            Paper → Live needs your promotion and activation
          </li>
        </ol>
      {/if}

      <Tabs.Root bind:value={tab}>
        <Tabs.List variant="line">
          {#each tabs as t (t)}<Tabs.Trigger value={t}>{t}</Tabs.Trigger>{/each}
        </Tabs.List>

        <Tabs.Content
          value="Overview"
          class="mt-4 grid gap-4 lg:grid-cols-[1fr_22rem]"
        >
          <section class="surface flex flex-col gap-4 rounded-xl p-5">
            <div class="grid grid-cols-2 gap-4 md:grid-cols-4">
              {#each e.measures as m (m.key)}
                <div>
                  <p class="text-muted-foreground text-xs">{m.label}</p>
                  <p
                    class={cn(
                      "num text-2xl font-semibold",
                      m.tone === "up" && "text-success",
                      m.tone === "down" && "text-destructive",
                    )}
                  >
                    {m.value}
                  </p>
                  <p class="text-muted-foreground mt-0.5 text-xs leading-snug">
                    {m.help}
                  </p>
                </div>
              {/each}
            </div>
            {#if e.spark}
              <div>
                <p class="panel-label mb-1">
                  {e.kind === "bot"
                    ? "Equity, evidence period"
                    : "Validation score by fold"}
                </p>
                <Sparkline values={e.spark} class="h-36 w-full" />
              </div>
            {/if}
          </section>
          <aside class="flex flex-col gap-4">
            {#if e.parameters}
              <section class="surface rounded-xl p-4">
                <p class="panel-label mb-2">Parameters</p>
                <dl class="flex flex-col text-sm">
                  {#each e.parameters as [k, v] (k)}
                    <div class="flex justify-between gap-3 border-t py-2">
                      <dt class="text-muted-foreground">{k}</dt>
                      <dd class="text-right">{v}</dd>
                    </div>
                  {/each}
                </dl>
              </section>
            {/if}
            {#if e.streams}
              <section class="surface rounded-xl p-4">
                <p class="panel-label mb-2">Reads</p>
                <ul class="flex flex-col gap-1.5 text-sm">
                  {#each e.streams as s (s)}<li
                      class="bg-muted rounded-md px-2.5 py-1.5"
                    >
                      {s}
                    </li>{/each}
                </ul>
              </section>
            {/if}
          </aside>
        </Tabs.Content>

        <Tabs.Content value="Evidence" class="mt-4">
          <div class="surface overflow-hidden rounded-xl">
            <table class="w-full text-sm">
              <thead class="text-muted-foreground text-left text-xs">
                <tr
                  ><th class="px-4 py-2.5 font-medium">Run</th><th
                    class="font-medium">Experiment</th
                  ><th class="font-medium">Role</th><th class="font-medium"
                    >Period</th
                  ><th class="text-right font-medium">Sharpe</th><th
                    class="text-right font-medium">Max drawdown</th
                  ><th class="text-right font-medium">Trades</th><th
                    class="px-4 text-right font-medium">When</th
                  ></tr
                >
              </thead>
              <tbody>
                {#each e.evidence ?? [] as r (r.run)}
                  <tr class="hover:bg-muted/50 border-t">
                    <td class="num px-4 py-2.5 text-xs">{r.run}</td>
                    <td>{r.kind}</td>
                    <td class={ROLE_TONE[r.role]}>{r.role}</td>
                    <td class="text-muted-foreground">{r.period}</td>
                    <td class="num text-right">{r.sharpe}</td>
                    <td class="num text-destructive text-right"
                      >{r.maxDrawdown}</td
                    >
                    <td class="num text-right">{r.trades}</td>
                    <td class="text-muted-foreground px-4 text-right"
                      >{r.when}</td
                    >
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
          <p class="text-muted-foreground mt-2 text-xs">
            Only confirmation runs count toward a verdict. Trials and replicates
            are kept for the record.
          </p>
        </Tabs.Content>

        <Tabs.Content value="Journal" class="mt-4">
          <div class="surface overflow-hidden rounded-xl">
            <table class="w-full text-sm">
              <thead class="text-muted-foreground text-left text-xs">
                <tr
                  ><th class="px-4 py-2.5 font-medium">Closed</th><th
                    class="font-medium">Symbol</th
                  ><th class="font-medium">Side</th><th
                    class="text-right font-medium">Lots</th
                  ><th class="text-right font-medium">Entry</th><th
                    class="text-right font-medium">Exit</th
                  ><th class="text-right font-medium">P&amp;L</th><th
                    class="px-4 font-medium">Note</th
                  ></tr
                >
              </thead>
              <tbody>
                {#each e.journal ?? [] as j (j.time)}
                  <tr class="border-t">
                    <td class="text-muted-foreground px-4 py-2.5">{j.time}</td>
                    <td class="font-medium">{j.symbol}</td>
                    <td>{j.side}</td>
                    <td class="num text-right">{j.lots.toFixed(2)}</td>
                    <td class="num text-right">{j.entry}</td>
                    <td class="num text-right">{j.exit}</td>
                    <td
                      class={cn(
                        "num text-right",
                        j.pnl >= 0 ? "text-success" : "text-destructive",
                      )}
                      >{j.pnl >= 0 ? "+" : "−"}${Math.abs(j.pnl).toFixed(2)}</td
                    >
                    <td class="text-muted-foreground px-4">{j.note || "—"}</td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        </Tabs.Content>

        <Tabs.Content value="Connections" class="mt-4">
          {#if e.connections?.length}
            <div class="grid gap-3 md:grid-cols-2">
              {#each e.connections as c (c.book)}
                <section class="surface flex flex-col gap-2 rounded-xl p-4">
                  <p class="font-medium">{c.node}</p>
                  <div class="flex gap-2">
                    <Badge
                      variant="outline"
                      class={c.mode === "Live"
                        ? "text-success"
                        : "text-warning"}>{c.mode}</Badge
                    >
                    <Badge variant="outline">Book {c.book}</Badge>
                    <Badge
                      variant="outline"
                      class={c.seat === "active" ? "" : "text-muted-foreground"}
                      >Seat {c.seat}</Badge
                    >
                  </div>
                  <p class="text-muted-foreground text-xs">
                    Sizing comes from the book, never from the bot.
                  </p>
                </section>
              {/each}
            </div>
          {:else}
            <EmptyState
              title="Not on any node yet"
              description="Bots reach a node only after you promote them; until then they live in research and evidence."
            />
          {/if}
        </Tabs.Content>

        <Tabs.Content value="Slots" class="mt-4 grid gap-3 md:grid-cols-2">
          {#each e.slots ?? [] as s (s)}
            <section class="surface flex items-center gap-3 rounded-xl p-4">
              <span class="min-w-0 flex-1"
                ><span class="block font-medium">{s}</span><span
                  class="text-muted-foreground block text-xs"
                  >Not plugged in</span
                ></span
              >
              <Button
                size="sm"
                variant="outline"
                aria-disabled="true"
                class="aria-disabled:opacity-60"
                title="Needs the daemon"
                onclick={(ev) => ev.preventDefault()}>Plug in…</Button
              >
            </section>
          {/each}
        </Tabs.Content>

        <Tabs.Content value="Operations" class="mt-4 flex flex-col gap-3">
          {#if headless}
            <p class="text-muted-foreground text-sm">
              This app has no screens. You run its operations here, from a
              workflow, or by asking the copilot; jobs show up on Home.
            </p>
          {/if}
          {#each e.ops ?? [] as op (op.id)}
            <section class="surface flex flex-col gap-3 rounded-xl p-4">
              <div class="flex items-center gap-2">
                <span class="num font-medium">{op.id}</span>
                <Badge variant="outline" class="text-[10px]">{op.effect}</Badge>
                <span class="text-muted-foreground text-sm">{op.summary}</span>
              </div>
              {#if op.inputs.length}
                <div class="grid gap-2 sm:grid-cols-2">
                  {#each op.inputs as inp (inp.name)}
                    <label class="flex flex-col gap-1 text-xs">
                      <span class="text-muted-foreground"
                        >{inp.name}{inp.required ? "" : " (optional)"} · {inp.type}</span
                      >
                      <Input class="h-8" disabled placeholder={inp.type} />
                    </label>
                  {/each}
                </div>
              {/if}
              <div>
                <Button size="sm" disabled><Play /> Run (needs daemon)</Button>
              </div>
            </section>
          {/each}
        </Tabs.Content>

        <Tabs.Content value="Steps" class="mt-4">
          <ol class="flex flex-wrap items-center gap-2">
            {#each e.steps ?? [] as s, i (s)}
              <li class="flex items-center gap-2">
                <span class="surface num rounded-lg px-3 py-2 text-sm">{s}</span
                >
                {#if i < (e.steps?.length ?? 0) - 1}<span
                    class="text-muted-foreground">→</span
                  >{/if}
              </li>
            {/each}
          </ol>
          <p class="text-muted-foreground mt-3 text-sm">
            {e.runs} runs this month. Open in Authoring to edit; a draft runs only
            after it is published.
          </p>
        </Tabs.Content>

        <Tabs.Content value="Artifacts" class="mt-4">
          <ul class="grid gap-2 md:grid-cols-2">
            {#each linked as a (a.id)}
              <li class="surface flex items-center gap-3 rounded-lg p-3">
                <span class="bg-muted rounded-sm px-2 py-0.5 text-xs"
                  >{a.type}</span
                >
                <span class="min-w-0 flex-1 truncate text-sm font-medium"
                  >{a.name}</span
                >
                <span class="num text-muted-foreground text-xs">{a.size}</span>
              </li>
            {/each}
          </ul>
        </Tabs.Content>
      </Tabs.Root>
    </div>
  </div>
{/if}
