<script lang="ts">
  /**
   * One pod, to steer rather than read. Every control changes the numbers
   * here and on the Pods cards (podSim): the sizing method, the knobs, the
   * drawdown ladder and bot weights make a draft, replayed over the pod's
   * own history; Save makes the next version. Pause, resume and the live or
   * paper side act at once. Demo maths in the browser.
   */
  import { goto } from "$app/navigation";
  import { resolve } from "$app/paths";
  import FlaskConical from "@lucide/svelte/icons/flask-conical";
  import Pause from "@lucide/svelte/icons/pause";
  import Play from "@lucide/svelte/icons/play";
  import Plus from "@lucide/svelte/icons/plus";
  import X from "@lucide/svelte/icons/x";
  import Undo2 from "@lucide/svelte/icons/undo-2";
  import Save from "@lucide/svelte/icons/save";
  import Layers from "@lucide/svelte/icons/layers";
  import { Button } from "$lib/components/ui/button";
  import { Slider } from "$lib/components/ui/slider";
  import * as Popover from "$lib/components/ui/popover";
  import { cn } from "$lib/utils";
  import InfoTip from "$lib/workbench/InfoTip.svelte";
  import PanelSummary from "$lib/workbench/PanelSummary.svelte";
  import Segmented from "$lib/workbench/Segmented.svelte";
  import { panelSize } from "$lib/workbench/tiles/panel-size";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { growth } from "$lib/demo/sizing-math";
  import { accountById } from "../demo";
  import { pct, usd } from "../bits";
  import { portfolio } from "../portfolio.svelte";
  import { METHODS, fmtKnob, podSim, type Side } from "../pod-sim.svelte";

  const size = panelSize();
  const id = $derived(portfolio.pod);
  const v = $derived(podSim.view(id));
  const p = $derived(v.pod);
  const d = $derived(podSim.draft(id));
  const preview = $derived(podSim.preview(id));

  // Equity chart: both sides on one scale, plus the draft replay.
  const W = 600;
  const H = 120;
  const chart = $derived.by(() => {
    const all = [...v.curve, ...(v.other ?? []), ...(preview?.curve ?? [])];
    const min = Math.min(...all);
    const max = Math.max(...all);
    const path = (c: number[]) =>
      c
        .map((y, i) => {
          const x = (i / (c.length - 1)) * W;
          const yy = H - ((y - min) / (max - min || 1)) * (H - 8) - 4;
          return `${i ? "L" : "M"}${x.toFixed(1)},${yy.toFixed(1)}`;
        })
        .join("");
    const line = path(v.curve);
    return {
      line,
      fill: `${line}L${W},${H}L0,${H}Z`,
      other: v.other ? path(v.other) : null,
      draft: preview ? path(preview.curve) : null,
    };
  });

  const sides = $derived<
    { value: Side; label: string; dot: string; disabled?: boolean }[]
  >([
    {
      value: "live",
      label: "Live",
      dot: "var(--tone-live)",
      disabled: !v.hasLive,
    },
    { value: "paper", label: "Paper", dot: "var(--tone-paper)" },
  ]);
  const tone = (used: number) =>
    used >= 1 ? "bg-destructive" : used >= 0.75 ? "bg-warning" : "bg-success";

  function openInLab() {
    // eslint-disable-next-line svelte/no-navigation-without-resolve
    goto(`${resolve("/lab")}?layout=pod-design`);
  }

  function save() {
    const ver = podSim.save(id);
    workbench.notify(`${p.name} ${ver} saved.`);
  }
</script>

{#snippet sizing()}
  <section class="gap-row flex flex-col" aria-label="Sizing">
    <div class="flex items-center gap-2">
      <h4 class="text-sm font-medium">Sizing</h4>
      <InfoTip
        label="Explain the sizing methods"
        text="How the pod turns a bot's entry into a size. Book + BMS is the docs' method; a model, a Lab workflow or a hybrid size differently. In this demo each method leans on wins and losses differently, so the replay changes."
      />
    </div>
    <Segmented
      label="Sizing method"
      options={METHODS.map((m) => ({ value: m.kind, label: m.label }))}
      value={d.method}
      onchange={(k) => podSim.edit(id, (s) => (s.method = k))}
    />
    <ul class="flex flex-col">
      {#each p.knobs as k (k.key)}
        {@const val = d.knobs[k.key]}
        <li
          class="py-row grid grid-cols-[minmax(0,9rem)_1fr_4.5rem] items-center gap-3 text-sm"
        >
          <span
            class={cn(
              "truncate",
              val !== podSim.settings(id).knobs[k.key] && "text-primary",
            )}>{k.label}</span
          >
          <Slider
            type="single"
            min={k.min}
            max={k.max}
            step={k.step}
            value={val}
            onValueChange={(x: number) =>
              podSim.edit(id, (s) => (s.knobs[k.key] = x))}
            aria-label={k.label}
          />
          <span class="num text-right">{fmtKnob(val, k.unit)}</span>
        </li>
      {/each}
    </ul>
  </section>
{/snippet}

{#snippet ladder()}
  <section class="gap-row flex flex-col" aria-label="Drawdown ladder">
    <div class="flex items-center gap-2">
      <h4 class="text-sm font-medium">Drawdown ladder</h4>
      <InfoTip
        label="Explain the ladder"
        text="Below the pod's peak by the first number, every size is multiplied by the second. The deepest step reached wins."
      />
    </div>
    {#each d.ladder as step, i (i)}
      <div
        class="grid grid-cols-[3.5rem_1fr_3.5rem_1fr_auto] items-center gap-2 text-sm"
      >
        <span class="num text-right">−{step.at}%</span>
        <Slider
          type="single"
          min={1}
          max={30}
          step={1}
          value={step.at}
          onValueChange={(x: number) =>
            podSim.edit(id, (s) => (s.ladder[i].at = x))}
          aria-label={`Step ${i + 1} depth`}
        />
        <span class="num text-right">×{step.mult}</span>
        <Slider
          type="single"
          min={0}
          max={1}
          step={0.05}
          value={step.mult}
          onValueChange={(x: number) =>
            podSim.edit(id, (s) => (s.ladder[i].mult = x))}
          aria-label={`Step ${i + 1} size`}
        />
        <button
          type="button"
          class="text-muted-foreground hover:text-destructive flex size-6 items-center justify-center rounded"
          aria-label={`Remove step ${i + 1}`}
          onclick={() => podSim.edit(id, (s) => s.ladder.splice(i, 1))}
          ><X class="size-3.5" /></button
        >
      </div>
    {:else}
      <p class="text-muted-foreground text-sm">
        No steps: full size at any dip
      </p>
    {/each}
    <Button
      size="sm"
      variant="outline"
      class="self-start"
      disabled={d.ladder.length >= 4}
      onclick={() =>
        podSim.edit(id, (s) => {
          const last = s.ladder[s.ladder.length - 1];
          s.ladder.push({
            at: (last?.at ?? 0) + 5,
            mult: Math.round(((last?.mult ?? 1) / 2) * 100) / 100,
          });
        })}><Plus />Step</Button
    >
  </section>
{/snippet}

{#snippet bots()}
  <section class="gap-row flex flex-col" aria-label="Bots">
    <h4 class="text-sm font-medium">Bots</h4>
    <ul class="flex flex-col">
      {#each p.bots as b (b.id)}
        <li
          class="py-row grid grid-cols-[minmax(0,9rem)_1fr_3rem_4.5rem] items-center gap-3 text-sm"
        >
          <span class="flex min-w-0 items-center gap-2">
            <span
              class={cn(
                "size-2 shrink-0 rounded-full",
                v.paused
                  ? "bg-muted-foreground"
                  : b.state === "trading"
                    ? "bg-success"
                    : "bg-warning",
              )}
              title={v.paused ? "Paused" : b.state}
            ></span>
            <span class="truncate">{b.name}</span>
          </span>
          <Slider
            type="single"
            min={0}
            max={100}
            step={5}
            value={d.weights[b.id]}
            onValueChange={(x: number) =>
              podSim.edit(id, (s) => (s.weights[b.id] = x))}
            aria-label={`${b.name} weight`}
          />
          <span class="num text-right">{d.weights[b.id]}%</span>
          <span
            class={cn(
              "num text-right",
              b.pnl >= 0 ? "text-success" : "text-destructive",
            )}>{usd(b.pnl)}</span
          >
        </li>
      {/each}
    </ul>
  </section>
{/snippet}

{#snippet figures()}
  <dl class="gap-x-group gap-y-row grid grid-cols-2 text-sm @lg:grid-cols-4">
    <div>
      <dt class="text-muted-foreground text-xs">At stake next trade</dt>
      <dd class="num text-lg font-semibold" data-figure="at-stake">
        {usd(v.perTrade)}
      </dd>
    </div>
    <div>
      <dt class="text-muted-foreground text-xs">Losses to kill line</dt>
      <dd class="num text-lg font-semibold" data-figure="losses-to-kill">
        {Number.isFinite(v.tradesToKill) ? v.tradesToKill : "—"}
      </dd>
    </div>
    <div>
      <dt class="text-muted-foreground text-xs">Room to kill line</dt>
      <dd
        class={cn(
          "num text-lg font-semibold",
          v.roomShare < 0.25 ? "text-destructive" : "text-success",
        )}
      >
        {usd(v.room)}
      </dd>
    </div>
    <div>
      <dt class="text-muted-foreground text-xs">Deepest dip</dt>
      <dd class="num text-lg font-semibold">−{v.dip.toFixed(1)}%</dd>
    </div>
  </dl>
{/snippet}

{#snippet limits()}
  <table class="w-full text-sm" aria-label="Limits right now">
    <tbody>
      {#each v.limits as g (g.name)}
        <tr class="border-t first:border-t-0">
          <td class="py-row pr-3">{g.name}</td>
          <td class="py-row w-1/4">
            <span class="bg-muted block h-1.5 overflow-hidden rounded-full"
              ><span
                class={cn("block h-full", tone(g.used))}
                style="width:{Math.max(3, g.used * 100)}%"
              ></span></span
            >
          </td>
          <td class="num py-row pl-3 text-right">{g.now}</td>
          <td class="num py-row text-muted-foreground pl-2 text-right text-xs"
            >{g.limit}</td
          >
        </tr>
      {/each}
    </tbody>
  </table>
{/snippet}

{#if size.mode === "compact"}
  <PanelSummary
    label={p.name}
    value={usd(v.equity)}
    status={v.paused ? "Paused" : `${pct(v.today)} today · ${usd(v.room)} room`}
    tone={v.paused ? "warn" : v.roomShare < 0.25 ? "bad" : "good"}
    values={v.curve}
  />
{:else}
  <div class="flex h-full min-h-0 flex-col">
    <div class="px-panel flex h-11 shrink-0 items-center gap-2">
      <h3 class="truncate text-base font-semibold">{p.name}</h3>
      <span class="text-muted-foreground num hidden text-xs @md:inline"
        >{v.version}</span
      >
      <Segmented
        label="Live or paper side"
        options={sides}
        value={v.side}
        onchange={(s) => podSim.setSide(id, s)}
      />
      <span class="ml-auto flex items-center gap-1">
        <Button
          size="sm"
          variant={v.paused ? "default" : "outline"}
          onclick={() => {
            podSim.togglePause(id);
            workbench.notify(
              `${p.name} ${podSim.view(id).paused ? "paused: no new trades" : "resumed"}.`,
            );
          }}
          aria-label={v.paused ? "Resume" : "Pause"}
          >{#if v.paused}<Play /><span class="hidden @lg:inline">Resume</span
            >{:else}<Pause /><span class="hidden @lg:inline">Pause</span
            >{/if}</Button
        >
        <Button
          size="icon-sm"
          variant="ghost"
          aria-label="Open in the Lab"
          title="Open in the Lab"
          onclick={openInLab}><FlaskConical /></Button
        >
      </span>
    </div>

    <div class="min-h-0 flex-1 overflow-auto">
      <div
        class={cn(
          "px-panel pb-panel gap-group grid",
          size.mode === "expanded" &&
            "grid-cols-[minmax(0,1fr)_minmax(24rem,32rem)]",
        )}
      >
        <div class="gap-group flex min-w-0 flex-col">
          <div class="flex items-end justify-between gap-3">
            <div class="min-w-0">
              <p class="num text-3xl font-semibold" data-figure="equity">
                {usd(v.equity)}
              </p>
              <p class="text-muted-foreground truncate text-xs">
                {accountById(v.side === "live" ? p.account : p.paper.account)
                  ?.name}
              </p>
            </div>
            <p
              class={cn(
                "num text-sm",
                v.paused
                  ? "text-warning"
                  : v.today >= 0
                    ? "text-success"
                    : "text-destructive",
              )}
            >
              {v.paused ? "Paused" : `${pct(v.today)} today`}
            </p>
          </div>
          <svg
            viewBox="0 0 {W} {H}"
            preserveAspectRatio="none"
            class={cn(
              "solid-backing w-full rounded-lg",
              size.mode === "expanded" ? "h-48" : "h-28",
            )}
            role="img"
            aria-label="Pod equity"
          >
            <defs>
              <linearGradient id="pod-fill" x1="0" y1="0" x2="0" y2="1">
                <stop
                  offset="0"
                  stop-color="var(--primary)"
                  stop-opacity="0.3"
                />
                <stop offset="1" stop-color="var(--primary)" stop-opacity="0" />
              </linearGradient>
            </defs>
            <path d={chart.fill} fill="url(#pod-fill)" />
            {#if chart.other}
              <path
                d={chart.other}
                fill="none"
                stroke="var(--tone-{v.side === 'live' ? 'paper' : 'live'})"
                stroke-width="1.5"
                stroke-dasharray="5 4"
                opacity="0.7"
                vector-effect="non-scaling-stroke"
              />
            {/if}
            <path
              d={chart.line}
              fill="none"
              stroke="var(--primary)"
              stroke-width="2"
              vector-effect="non-scaling-stroke"
            />
            {#if chart.draft}
              <path
                d={chart.draft}
                fill="none"
                stroke="var(--foreground)"
                stroke-width="2"
                stroke-dasharray="2 3"
                vector-effect="non-scaling-stroke"
              />
            {/if}
          </svg>
          {@render figures()}
          {@render limits()}
        </div>

        <div class="gap-group flex min-w-0 flex-col">
          {@render sizing()}
          {#if size.mode === "expanded"}
            {@render ladder()}
          {:else}
            <Popover.Root>
              <Popover.Trigger>
                {#snippet child({ props })}
                  <Button
                    {...props}
                    size="sm"
                    variant="outline"
                    class="self-start"
                    ><Layers />Ladder · {d.ladder.length} step{d.ladder
                      .length === 1
                      ? ""
                      : "s"}</Button
                  >
                {/snippet}
              </Popover.Trigger>
              <Popover.Content align="start" class="w-96">
                {@render ladder()}
              </Popover.Content>
            </Popover.Root>
          {/if}
          {@render bots()}
        </div>
      </div>
    </div>

    {#if preview}
      <div
        class="bg-panel px-panel py-row flex shrink-0 flex-wrap items-center gap-x-3 gap-y-1 border-t"
      >
        <span class="text-sm font-medium">Draft {preview.version}</span>
        <span class="text-muted-foreground num text-xs" data-figure="draft">
          {pct(growth(v.curve), 0)} → {pct(preview.gain, 0)} · dip −{v.dip.toFixed(
            1,
          )}% → −{preview.dip.toFixed(1)}%{preview.stoodDown
            ? " · hits kill line"
            : ""}
        </span>
        <InfoTip
          label="What changed"
          side="top"
          text={preview.changes.join(" · ")}
        />
        <span class="ml-auto flex items-center gap-1">
          <Button variant="ghost" size="sm" onclick={() => podSim.discard(id)}
            ><Undo2 />Discard</Button
          >
          <Button size="sm" onclick={save}
            ><Save />Save {preview.version}</Button
          >
        </span>
      </div>
    {/if}
  </div>
{/if}
