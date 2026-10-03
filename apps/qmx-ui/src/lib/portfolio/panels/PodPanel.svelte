<script lang="ts">
  /**
   * One pod, built for adjusting rather than reading: big numbers, a safety
   * meter down to the kill line, knobs with sliders, guard rings and bot
   * weights. Any change becomes a draft; saving makes a new version that
   * runs on paper first and needs your signature before live (DEC-0144).
   * How the pod sizes risk (Book + BMS, a model, a Lab workflow, a hybrid)
   * is built in the Lab and shown here.
   */
  import { goto } from "$app/navigation";
  import { resolve } from "$app/paths";
  import BookOpen from "@lucide/svelte/icons/book-open";
  import BrainCircuit from "@lucide/svelte/icons/brain-circuit";
  import Workflow from "@lucide/svelte/icons/workflow";
  import Combine from "@lucide/svelte/icons/combine";
  import ListChecks from "@lucide/svelte/icons/list-checks";
  import FlaskConical from "@lucide/svelte/icons/flask-conical";
  import Undo2 from "@lucide/svelte/icons/undo-2";
  import { Button } from "$lib/components/ui/button";
  import { Slider } from "$lib/components/ui/slider";
  import { cn } from "$lib/utils";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { accountById, podById, type Method } from "../demo";
  import { pct, usd } from "../bits";
  import { portfolio } from "../portfolio.svelte";

  const p = $derived(podById(portfolio.pod)!);
  let edits = $state<Record<string, Record<string, number>>>({});
  const val = (key: string, base: number) => edits[p.id]?.[key] ?? base;
  function set(key: string, v: number) {
    edits[p.id] = { ...(edits[p.id] ?? {}), [key]: v };
  }
  const changed = $derived(
    [
      ...p.knobs.map((k) => ({
        label: k.label,
        from: k.value,
        to: val(k.key, k.value),
        unit: k.unit,
      })),
      ...p.bots.map((b) => ({
        label: `${b.name} weight`,
        from: b.weight,
        to: val(`w-${b.id}`, b.weight),
        unit: "%",
      })),
    ].filter((c) => c.from !== c.to),
  );
  const fmt = (v: number, unit: string) =>
    unit === "$" ? usd(v) : `${v}${unit}`;
  const next = $derived(p.version.replace(/\d+/, (n) => String(+n + 1)));

  const METHODS: {
    kind: Method["kind"];
    label: string;
    icon: typeof BookOpen;
  }[] = [
    { kind: "book", label: "Book + BMS", icon: BookOpen },
    { kind: "model", label: "Model", icon: BrainCircuit },
    { kind: "workflow", label: "Workflow", icon: Workflow },
    { kind: "hybrid", label: "Hybrid", icon: Combine },
    { kind: "rules", label: "Simple rules", icon: ListChecks },
  ];

  // Safety meter: floor (kill line) → start capital → now.
  const lo = $derived(p.floor * 0.97);
  const hi = $derived(Math.max(p.start, p.equity) * 1.03);
  const at = (v: number) => ((v - lo) / (hi - lo)) * 100;
  const room = $derived(p.equity - p.floor);

  // Area chart of the pod's equity.
  const W = 600;
  const H = 120;
  const area = $derived.by(() => {
    const v = p.curve;
    const min = Math.min(...v);
    const max = Math.max(...v);
    const pts = v.map((y, i) => [
      (i / (v.length - 1)) * W,
      H - ((y - min) / (max - min || 1)) * (H - 8) - 4,
    ]);
    const line = pts
      .map(([x, y], i) => `${i ? "L" : "M"}${x.toFixed(1)},${y.toFixed(1)}`)
      .join("");
    return { line, fill: `${line}L${W},${H}L0,${H}Z` };
  });
  const ring = (used: number) => {
    const r = 22;
    const c = 2 * Math.PI * r;
    return { r, c, off: c * (1 - Math.min(1, used)) };
  };
</script>

<div class="@container h-full overflow-auto">
  <div class="flex flex-col gap-4 p-4">
    <!-- Identity and money -->
    <div class="flex flex-wrap items-end gap-x-6 gap-y-2">
      <div class="min-w-0">
        <div class="flex items-center gap-2">
          <h3 class="text-2xl font-semibold tracking-tight">{p.name}</h3>
          <span
            class="rounded px-2 py-0.5 text-xs"
            style="background: color-mix(in oklab, var(--tone-{p.mode === 'LIVE'
              ? 'live'
              : 'paper'}) 22%, transparent)">{p.mode}</span
          >
          <span class="text-muted-foreground text-sm">{p.version}</span>
        </div>
        <p class="text-muted-foreground text-sm">
          {accountById(p.account)?.name}
        </p>
      </div>
      <div class="ml-auto text-right">
        <p class="num text-3xl font-semibold">{usd(p.equity)}</p>
        <p
          class={cn(
            "num text-sm",
            p.today >= 0 ? "text-success" : "text-destructive",
          )}
        >
          {pct(p.today)} today
        </p>
      </div>
    </div>

    <svg
      viewBox="0 0 {W} {H}"
      preserveAspectRatio="none"
      class="solid-backing h-28 w-full rounded-lg"
      role="img"
      aria-label="Pod equity"
    >
      <defs>
        <linearGradient id="pod-fill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stop-color="var(--primary)" stop-opacity="0.35" />
          <stop offset="1" stop-color="var(--primary)" stop-opacity="0" />
        </linearGradient>
      </defs>
      <path d={area.fill} fill="url(#pod-fill)" />
      <path
        d={area.line}
        fill="none"
        stroke="var(--primary)"
        stroke-width="2"
        vector-effect="non-scaling-stroke"
      />
    </svg>

    <!-- Safety meter -->
    <section>
      <div class="mb-2 flex items-baseline justify-between">
        <h4 class="text-base font-medium">Room above the kill line</h4>
        <span
          class="num text-xl {room / (p.start - p.floor) < 0.25
            ? 'text-destructive'
            : 'text-success'}">{usd(room)}</span
        >
      </div>
      <div
        class="relative h-4 rounded-full"
        style="background: linear-gradient(90deg, color-mix(in oklab, var(--destructive) 55%, transparent), color-mix(in oklab, var(--warning) 30%, transparent) 35%, color-mix(in oklab, var(--success) 35%, transparent))"
      >
        <span
          class="bg-destructive absolute -top-1.5 h-7 w-1 rounded"
          style="left:{at(val('floor', p.floor))}%"
        ></span>
        <span
          class="bg-muted-foreground absolute -top-1 h-6 w-0.5"
          style="left:{at(p.start)}%"
        ></span>
        <span
          class="border-background bg-foreground absolute -top-1 size-6 -translate-x-1/2 rounded-full border-4"
          style="left:{at(p.equity)}%"
        ></span>
      </div>
      <div class="text-muted-foreground mt-2 flex justify-between text-sm">
        <span
          >Kill line <span class="num text-foreground"
            >{usd(val("floor", p.floor))}</span
          ></span
        >
        <span
          >Started <span class="num text-foreground">{usd(p.start)}</span></span
        >
      </div>
    </section>

    <!-- How it sizes risk -->
    <section>
      <div class="mb-2 flex items-baseline gap-2">
        <h4 class="text-base font-medium">How it sizes risk</h4>
        <span class="text-muted-foreground text-sm">{p.method.from}</span>
      </div>
      <div class="grid grid-cols-2 gap-2 @lg:grid-cols-5">
        {#each METHODS as m (m.kind)}
          <button
            type="button"
            class={cn(
              "flex flex-col items-center gap-1.5 rounded-xl border-2 px-2 py-3 text-sm",
              p.method.kind === m.kind
                ? "border-primary bg-primary/12"
                : "hover:border-ring/50 border-transparent bg-muted/40",
            )}
            aria-pressed={p.method.kind === m.kind}
            onclick={() =>
              workbench.notify(
                `Changing how ${p.name} sizes risk is built in the Lab; the copilot brings the new version here on paper.`,
              )}
          >
            <m.icon class="size-6" />{m.label}
          </button>
        {/each}
      </div>
    </section>

    <!-- Knobs -->
    <section>
      <h4 class="mb-2 text-base font-medium">Adjust</h4>
      <div class="grid gap-3 @lg:grid-cols-2">
        {#each p.knobs as k (k.key)}
          {@const v = val(k.key, k.value)}
          <div
            class={cn(
              "rounded-xl border p-3",
              v !== k.value && "border-primary",
            )}
          >
            <div class="flex items-baseline justify-between gap-2">
              <span class="text-sm">{k.label}</span>
              <span class="num text-2xl font-semibold">{fmt(v, k.unit)}</span>
            </div>
            <Slider
              class="mt-3"
              type="single"
              min={k.min}
              max={k.max}
              step={k.step}
              value={v}
              onValueChange={(x: number) => set(k.key, x)}
              aria-label={k.label}
            />
            <div
              class="text-muted-foreground num mt-1.5 flex justify-between text-xs"
            >
              <span>{fmt(k.min, k.unit)}</span><span>{fmt(k.max, k.unit)}</span>
            </div>
          </div>
        {/each}
      </div>
    </section>

    <!-- Guards -->
    <section>
      <h4 class="mb-2 text-base font-medium">Limits right now</h4>
      <div class="grid grid-cols-1 gap-2 @md:grid-cols-3">
        {#each p.guards as g (g.name)}
          {@const r = ring(g.used)}
          {@const tone =
            g.used >= 1
              ? "var(--destructive)"
              : g.used >= 0.75
                ? "var(--warning)"
                : "var(--success)"}
          <div class="flex items-center gap-3 rounded-xl border p-3">
            <svg
              viewBox="0 0 56 56"
              class="size-14 shrink-0 -rotate-90"
              aria-hidden="true"
            >
              <circle
                cx="28"
                cy="28"
                r={r.r}
                fill="none"
                stroke="var(--muted)"
                stroke-width="6"
              />
              <circle
                cx="28"
                cy="28"
                r={r.r}
                fill="none"
                stroke={tone}
                stroke-width="6"
                stroke-linecap="round"
                stroke-dasharray={r.c}
                stroke-dashoffset={r.off}
              />
            </svg>
            <div class="min-w-0">
              <p class="text-sm">{g.name}</p>
              <p class="num text-lg font-semibold">{g.now}</p>
              <p class="text-muted-foreground text-xs">of {g.limit}</p>
            </div>
          </div>
        {/each}
      </div>
    </section>

    <!-- Bots and their weights -->
    <section>
      <h4 class="mb-2 text-base font-medium">Bots in this pod</h4>
      <div class="grid gap-2">
        {#each p.bots as b (b.id)}
          {@const w = val(`w-${b.id}`, b.weight)}
          <div
            class="grid grid-cols-[1fr_auto] items-center gap-x-4 gap-y-1 rounded-xl border p-3 @lg:grid-cols-[14rem_1fr_6rem_6rem]"
          >
            <span class="flex items-center gap-2">
              <span
                class={cn(
                  "size-2.5 rounded-full",
                  b.state === "trading" ? "bg-success" : "bg-warning",
                )}
              ></span>
              <span class="font-medium">{b.name}</span>
              <span class="text-muted-foreground text-xs">{b.symbol}</span>
            </span>
            <Slider
              class="col-span-2 @lg:col-span-1"
              type="single"
              min={0}
              max={100}
              step={5}
              value={w}
              onValueChange={(x: number) => set(`w-${b.id}`, x)}
              aria-label={`${b.name} weight`}
            />
            <span class="num text-right text-lg">{w}%</span>
            <span
              class={cn(
                "num text-right",
                b.pnl >= 0 ? "text-success" : "text-destructive",
              )}>{usd(b.pnl)}</span
            >
          </div>
        {/each}
      </div>
    </section>
  </div>

  {#if changed.length}
    <div
      class="bg-panel sticky bottom-0 flex flex-wrap items-center gap-3 border-t px-4 py-3"
    >
      <span class="text-sm font-medium">Draft {next}</span>
      <span class="text-muted-foreground min-w-0 flex-1 truncate text-sm">
        {changed
          .map(
            (c) => `${c.label} ${fmt(c.from, c.unit)} → ${fmt(c.to, c.unit)}`,
          )
          .join(" · ")}
      </span>
      <Button variant="ghost" size="sm" onclick={() => (edits[p.id] = {})}
        ><Undo2 />Discard</Button
      >
      <Button
        size="sm"
        onclick={() =>
          workbench.notify(
            `${p.name} ${next} would run on paper first, then wait for your signature. Saving needs the trading node.`,
          )}>Save {next} to paper</Button
      >
    </div>
  {:else}
    <div
      class="text-muted-foreground flex items-center gap-2 border-t px-4 py-2 text-xs"
    >
      <FlaskConical class="size-3.5" />Built in the Lab.
      <button
        type="button"
        class="hover:text-foreground underline underline-offset-2"
        onclick={() => goto(resolve("/lab"))}>Open it there</button
      >
    </div>
  {/if}
</div>
