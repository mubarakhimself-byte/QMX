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

  // Fewer, denser tabs: performance, trading, setup (+ operations/steps).
  const tabs = $derived.by(() => {
    if (!e) return [] as string[];
    const t: string[] = [];
    if (e.kind === "bot" || e.kind === "model") t.push("Performance");
    if (e.journal || e.connections) t.push("Trading");
    if (e.slots) t.push("Slots");
    if (e.ops) t.push("Operations");
    if (e.steps) t.push("Steps");
    t.push("Setup");
    return t;
  });
  let tab = $state("");
  $effect(() => {
    if (!tabs.includes(tab)) tab = tabs[0];
  });
  const stageIndex = $derived(e ? PIPELINE.indexOf(e.stage) : -1);
  const headless = $derived(e?.kind === "app" && (e.views?.length ?? 0) === 0);
  const linked = $derived(
    DEMO_ARTIFACTS.filter((a) => e?.artifacts?.includes(a.id)),
  );
  const ROLE_TONE: Record<string, string> = {
    confirmation: "text-success",
    trial: "text-muted-foreground",
    replicate: "text-info",
  };
  // Return to the Library tab the item lives in, not the default tab.
  const backHref = $derived(
    `${resolve("/library")}?tab=${e && (e.kind === "bot" || e.kind === "model") ? "artifact" : "contribution"}`,
  );
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
  <div class="scrim flex h-full flex-col overflow-hidden">
    <div
      class="bg-warning/15 flex h-7 shrink-0 items-center gap-2 px-3 text-xs"
    >
      <FlaskConical class="text-warning size-3.5" /> Demo item. Sample numbers; nothing
      here is evidence.
    </div>
    <header
      class="bg-panel flex shrink-0 items-center gap-4 border-b px-4 py-3"
    >
      <!-- eslint-disable svelte/no-navigation-without-resolve -- backHref is resolve("/library") plus a query string -->
      <a
        href={backHref}
        class="text-muted-foreground hover:text-foreground"
        aria-label="Back to Library"><ArrowLeft class="size-5" /></a
      >
      <!-- eslint-enable svelte/no-navigation-without-resolve -->
      <CoverArt
        kind={e.kind}
        seed={e.id}
        series={e.spark}
        steps={e.steps?.length ?? 0}
        class="h-14 w-24 shrink-0 rounded-md"
      />
      <div class="min-w-0 flex-1">
        <p class="panel-label">
          {KIND_LABEL[e.kind]}{headless ? " · headless" : ""} · {e.family ??
            e.version}
        </p>
        <h1 class="truncate text-xl font-semibold">{e.name}</h1>
        <p class="text-muted-foreground truncate text-sm">
          {e.summary} · <span class="num">{e.version} · {e.fp}</span>
        </p>
      </div>
      {#if e.kind === "bot"}
        <ol class="hidden items-center gap-1.5 2xl:flex" aria-label="Pipeline">
          {#each PIPELINE as s, i (s)}
            <li
              class={cn(
                "flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs",
                i < stageIndex && "text-success border-success/40",
                i === stageIndex &&
                  "bg-primary text-primary-foreground border-transparent",
                i > stageIndex && "text-muted-foreground",
              )}
            >
              {#if i < stageIndex}<Check class="size-3" />{/if}{s}
            </li>
          {/each}
        </ol>
      {/if}
      <div class="flex shrink-0 gap-2">
        <Button size="sm" onclick={() => workbench.addRef(e.name)}
          ><MessageSquarePlus /> Add to copilot</Button
        >
        {#if e.kind !== "app"}<Button
            size="sm"
            variant="outline"
            href={resolve("/lab")}><Workflow /> Open in Lab</Button
          >{/if}
        {#if e.kind === "bot" && (e.stage === "Evidence" || e.stage === "Paper")}
          <!-- eslint-disable svelte/no-navigation-without-resolve -->
          <Button
            size="sm"
            variant="outline"
            href={`${resolve("/portfolio")}?layout=road`}
            title="Promotion happens on Portfolio's Road to live, where you sign the card"
            ><ShieldCheck /> Road to live</Button
          >
          <!-- eslint-enable svelte/no-navigation-without-resolve -->
        {/if}
      </div>
    </header>

    <Tabs.Root bind:value={tab} class="flex min-h-0 flex-1 flex-col gap-0">
      <div class="bg-panel shrink-0 border-b px-4">
        <Tabs.List variant="line"
          >{#each tabs as t (t)}<Tabs.Trigger value={t}>{t}</Tabs.Trigger
            >{/each}</Tabs.List
        >
      </div>
      <div class="flex min-h-0 flex-1 flex-col overflow-auto p-4">
        <Tabs.Content
          value="Performance"
          class="grid flex-1 gap-3 xl:grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)]"
        >
          <section class="surface flex flex-col gap-4 rounded-xl p-4">
            <div class="grid grid-cols-2 gap-x-4 gap-y-3">
              {#each e.measures as m (m.key)}
                <div title={m.help}>
                  <p class="text-muted-foreground text-xs">{m.label}</p>
                  <p
                    class={cn(
                      "num text-xl font-semibold",
                      m.tone === "up" && "text-success",
                      m.tone === "down" && "text-destructive",
                    )}
                  >
                    {m.value}
                  </p>
                  <p class="text-muted-foreground text-xs leading-snug">
                    {m.help}
                  </p>
                </div>
              {/each}
            </div>
            {#if e.spark}
              <div class="flex min-h-0 flex-1 flex-col">
                <p class="panel-label mb-1">
                  {e.kind === "bot"
                    ? "Equity, evidence period"
                    : "Validation score by fold"}
                </p>
                <Sparkline values={e.spark} class="h-full min-h-28 w-full" />
              </div>
            {/if}
          </section>
          <section class="surface overflow-hidden rounded-xl">
            <p class="panel-label border-b px-4 py-2.5">Evidence runs</p>
            <table class="w-full text-sm">
              <thead class="text-muted-foreground text-left text-xs">
                <tr
                  ><th class="px-4 py-2 font-medium">Experiment</th><th
                    class="font-medium">Role</th
                  ><th class="font-medium">Period</th><th
                    class="text-right font-medium">Sharpe</th
                  ><th class="text-right font-medium">Max DD</th><th
                    class="px-4 text-right font-medium">When</th
                  ></tr
                >
              </thead>
              <tbody>
                {#each e.evidence ?? [] as r (r.run)}
                  <tr class="hover:bg-muted/40 border-t">
                    <td class="px-4 py-2"
                      ><span class="block">{r.kind}</span><span
                        class="num text-muted-foreground text-xs">{r.run}</span
                      ></td
                    >
                    <td class={ROLE_TONE[r.role]}>{r.role}</td>
                    <td class="text-muted-foreground text-xs">{r.period}</td>
                    <td class="num text-right">{r.sharpe}</td>
                    <td class="num text-destructive text-right"
                      >{r.maxDrawdown}</td
                    >
                    <td class="text-muted-foreground px-4 text-right text-xs"
                      >{r.when}</td
                    >
                  </tr>
                {:else}
                  <tr
                    ><td
                      colspan="6"
                      class="text-muted-foreground px-4 py-6 text-center"
                      >No evidence runs yet</td
                    ></tr
                  >
                {/each}
              </tbody>
            </table>
            <p class="text-muted-foreground border-t px-4 py-2 text-xs">
              Only confirmation runs count toward a verdict.
            </p>
          </section>
        </Tabs.Content>

        <Tabs.Content
          value="Trading"
          class="grid flex-1 content-start gap-3 xl:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)]"
        >
          <section class="surface overflow-hidden rounded-xl">
            <p class="panel-label border-b px-4 py-2.5">Journal</p>
            <table class="w-full text-sm">
              <thead class="text-muted-foreground text-left text-xs">
                <tr
                  ><th class="px-4 py-2 font-medium">Closed</th><th
                    class="font-medium">Symbol</th
                  ><th class="font-medium">Side</th><th
                    class="text-right font-medium">Entry → exit</th
                  ><th class="text-right font-medium">P&amp;L</th><th
                    class="px-4 font-medium">Note</th
                  ></tr
                >
              </thead>
              <tbody>
                {#each e.journal ?? [] as j (j.time)}
                  <tr class="border-t">
                    <td class="text-muted-foreground px-4 py-2">{j.time}</td>
                    <td class="font-medium">{j.symbol}</td><td
                      >{j.side} {j.lots.toFixed(2)}</td
                    >
                    <td class="num text-right">{j.entry} → {j.exit}</td>
                    <td
                      class={cn(
                        "num text-right",
                        j.pnl >= 0 ? "text-success" : "text-destructive",
                      )}
                      >{j.pnl >= 0 ? "+" : "−"}${Math.abs(j.pnl).toFixed(2)}</td
                    >
                    <td class="text-muted-foreground px-4">{j.note || "—"}</td>
                  </tr>
                {:else}
                  <tr
                    ><td
                      colspan="6"
                      class="text-muted-foreground px-4 py-6 text-center"
                      >No trades yet</td
                    ></tr
                  >
                {/each}
              </tbody>
            </table>
          </section>
          <section class="flex flex-col gap-3">
            {#each e.connections ?? [] as c (c.pod)}
              <div class="surface flex flex-col gap-2 rounded-xl p-4">
                <p class="font-medium">Runs on {c.server}</p>
                <div class="flex flex-wrap gap-1.5">
                  <Badge
                    variant="outline"
                    style="color: var(--tone-{c.mode === 'Live'
                      ? 'live'
                      : 'paper'})">{c.mode}</Badge
                  >
                  <Badge variant="outline">Pod {c.pod}</Badge>
                  <Badge
                    variant="outline"
                    class={c.seat === "active" ? "" : "text-muted-foreground"}
                    >Seat {c.seat}</Badge
                  >
                </div>
                <p class="text-muted-foreground text-xs">
                  Sizing comes from the pod, never from the bot.
                </p>
              </div>
            {:else}
              <div class="surface rounded-xl p-4">
                <p class="font-medium">Not on a trading server yet</p>
                <p class="text-muted-foreground text-sm">
                  A bot reaches a trading server only after you promote it.
                </p>
              </div>
            {/each}
          </section>
        </Tabs.Content>

        <Tabs.Content
          value="Slots"
          class="grid gap-3 md:grid-cols-2 xl:grid-cols-4"
        >
          {#each e.slots ?? [] as s (s)}
            <section class="surface flex flex-col gap-2 rounded-xl p-4">
              <span class="font-medium">{s}</span><span
                class="text-muted-foreground text-xs">Not plugged in</span
              >
              <Button
                size="sm"
                variant="outline"
                class="mt-auto self-start aria-disabled:opacity-60"
                aria-disabled="true"
                title="Needs the daemon"
                onclick={(ev) => ev.preventDefault()}>Plug in…</Button
              >
            </section>
          {/each}
        </Tabs.Content>

        <Tabs.Content value="Operations" class="grid gap-3 xl:grid-cols-2">
          {#if headless}<p class="text-muted-foreground text-sm xl:col-span-2">
              This app has no screens. Run its operations here, from a workflow,
              or through the copilot; jobs show on Home.
            </p>{/if}
          {#each e.ops ?? [] as op (op.id)}
            <section class="surface flex flex-col gap-3 rounded-xl p-4">
              <div class="flex items-center gap-2">
                <span class="num font-medium">{op.id}</span><Badge
                  variant="outline"
                  class="text-xs">{op.effect}</Badge
                >
              </div>
              <p class="text-muted-foreground text-sm">{op.summary}</p>
              {#if op.inputs.length}
                <div class="grid gap-2 sm:grid-cols-2">
                  {#each op.inputs as inp (inp.name)}
                    <label class="flex flex-col gap-1 text-xs"
                      ><span class="text-muted-foreground"
                        >{inp.name}{inp.required ? "" : " (optional)"} · {inp.type}</span
                      ><Input
                        class="h-8"
                        disabled
                        placeholder={inp.type}
                      /></label
                    >
                  {/each}
                </div>
              {/if}
              <div>
                <Button size="sm" disabled><Play /> Run (needs daemon)</Button>
              </div>
            </section>
          {/each}
        </Tabs.Content>

        <Tabs.Content value="Steps">
          <ol class="flex flex-wrap items-center gap-2">
            {#each e.steps ?? [] as s, i (s)}
              <li class="flex items-center gap-2">
                <span class="surface num rounded-lg px-3 py-2 text-sm">{s}</span
                >{#if i < (e.steps?.length ?? 0) - 1}<span
                    class="text-muted-foreground">→</span
                  >{/if}
              </li>
            {/each}
          </ol>
          <p class="text-muted-foreground mt-3 text-sm">
            {e.runs} runs this month. A draft runs only after it is published.
          </p>
        </Tabs.Content>

        <Tabs.Content value="Setup" class="grid gap-3 xl:grid-cols-3">
          <section class="surface rounded-xl p-4">
            <p class="panel-label mb-2">Parameters</p>
            {#if e.parameters}
              <dl class="flex flex-col text-sm">
                {#each e.parameters as [k, v] (k)}<div
                    class="flex justify-between gap-3 border-t py-2"
                  >
                    <dt class="text-muted-foreground">{k}</dt>
                    <dd class="text-right">{v}</dd>
                  </div>{/each}
              </dl>
            {:else}<p class="text-muted-foreground text-sm">None</p>{/if}
          </section>
          <section class="surface rounded-xl p-4">
            <p class="panel-label mb-2">Reads</p>
            <ul class="flex flex-col gap-1.5 text-sm">
              {#each e.streams ?? [] as s (s)}<li
                  class="well rounded-md px-2.5 py-1.5"
                >
                  {s}
                </li>{:else}<li class="text-muted-foreground">
                  Nothing declared
                </li>{/each}
            </ul>
          </section>
          <section class="surface rounded-xl p-4">
            <p class="panel-label mb-2">Artifacts</p>
            <ul class="flex flex-col gap-1.5 text-sm">
              {#each linked as a (a.id)}
                <li
                  class="well flex items-center gap-2 rounded-md px-2.5 py-1.5"
                >
                  <span class="min-w-0 flex-1 truncate">{a.name}</span><span
                    class="text-muted-foreground text-xs">{a.type}</span
                  >
                </li>
              {:else}<li class="text-muted-foreground">None yet</li>{/each}
            </ul>
          </section>
        </Tabs.Content>
      </div>
    </Tabs.Root>
  </div>
{/if}
