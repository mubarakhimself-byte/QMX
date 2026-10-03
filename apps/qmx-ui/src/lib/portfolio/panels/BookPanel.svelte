<script lang="ts">
  /**
   * One Book: where its risk comes from (rules, a model, both, or a workflow
   * built in the Lab), the USD sizing ladder from capital down to the kill
   * line, and its seats. Edits never overwrite: they draft a new version,
   * and money-rule changes need a fresh demo run and a signature (DEC-0144,
   * DEC-0203).
   */
  import GitBranch from "@lucide/svelte/icons/git-branch";
  import Copy from "@lucide/svelte/icons/copy";
  import FlaskConical from "@lucide/svelte/icons/flask-conical";
  import { Button } from "$lib/components/ui/button";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu";
  import { cn } from "$lib/utils";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { accountById, bookById, sizing, type Engine } from "../demo";
  import { usd } from "../bits";
  import { portfolio } from "../portfolio.svelte";

  const b = $derived(bookById(portfolio.book)!);
  const s = $derived(sizing(b));
  const ENGINES: Engine[] = [
    {
      kind: "rules",
      label: "Rules",
      note: "The Book's sizing ladder and limits",
    },
    {
      kind: "model",
      label: "Vol forecaster",
      note: "A model sizes trades; rules stay as hard limits",
    },
    {
      kind: "hybrid",
      label: "Rules + regime HMM",
      note: "Rules size; a regime model throttles",
    },
  ];
  // Where equity sits between the kill line and a little above capital.
  const top = $derived(Math.max(b.capital, b.equity) * 1.04);
  const pos = (v: number) =>
    ((v - b.killLine * 0.96) / (top - b.killLine * 0.96)) * 100;
  const LADDER = $derived([
    ["Book capital", usd(b.capital), "Equity at period open"],
    ["Kill line", usd(b.killLine), "Breach: flatten, stand down, go to paper"],
    ["Loss runway", usd(s.runway), "Capital minus kill line"],
    ["Periods", String(b.runwayPeriods), "Runway is spread over"],
    ["Loss budget per period", usd(s.budget), "Runway ÷ periods"],
    ["Losing trades allowed", String(b.seatAllowance), "Per seat, per period"],
    ["Price of 1 R", usd(s.rPrice), "Budget ÷ losing trades allowed"],
  ] as [string, string, string][]);
</script>

<div class="flex h-full flex-col overflow-auto">
  <div class="flex flex-wrap items-center gap-x-3 gap-y-1 border-b px-3 py-2">
    <span class="text-base font-semibold">{b.name}</span>
    <span class="text-muted-foreground text-xs"
      >{b.template} · {b.version} · {accountById(b.account)?.name}</span
    >
    <span
      class="ml-auto rounded px-1.5 py-0.5 text-xs"
      style="background: color-mix(in oklab, {b.mode === 'LIVE'
        ? 'var(--tone-live)'
        : 'var(--tone-paper)'} 20%, transparent)">{b.mode} · {b.binding}</span
    >
  </div>

  <section class="border-b px-3 py-3">
    <div class="mb-2 flex items-center gap-2">
      <h4 class="text-sm font-medium">Risk comes from</h4>
      <span class="text-muted-foreground text-xs"
        >rules, a model, both, or a workflow from the Lab</span
      >
    </div>
    <div class="flex flex-wrap gap-1.5">
      {#each ENGINES as e (e.kind)}
        <button
          type="button"
          class={cn(
            "rounded-md border px-2.5 py-1.5 text-left text-xs",
            b.engine.kind === e.kind
              ? "border-primary bg-primary/12"
              : "hover:border-ring/60",
          )}
          onclick={() =>
            workbench.notify(
              `Switching ${b.name} to "${e.label}" drafts ${b.version.replace(/\d+/, (n) => String(+n + 1))}. It needs a demo run and your signature before live.`,
            )}
        >
          <span class="block font-medium">{e.label}</span>
          <span class="text-muted-foreground">{e.note}</span>
          {#if e.kind !== "rules"}<span class="text-info block text-[11px]"
              >new scope</span
            >{/if}
        </button>
      {/each}
      <DropdownMenu.Root>
        <DropdownMenu.Trigger>
          {#snippet child({ props })}
            <button
              {...props}
              type="button"
              class="hover:border-ring/60 rounded-md border border-dashed px-2.5 py-1.5 text-left text-xs"
            >
              <span class="flex items-center gap-1 font-medium"
                ><FlaskConical class="size-3.5" />From the Lab…</span
              >
              <span class="text-muted-foreground"
                >A kill switch or sizing workflow you built</span
              >
            </button>
          {/snippet}
        </DropdownMenu.Trigger>
        <DropdownMenu.Content>
          <DropdownMenu.Label>Published workflows</DropdownMenu.Label>
          {#each ["Volatility-scaled sizing v2", "News-aware kill switch v1", "Drawdown ladder v3"] as w (w)}
            <DropdownMenu.Item
              onclick={() =>
                workbench.notify(
                  `${w} would draft a new version of ${b.name}.`,
                )}>{w}</DropdownMenu.Item
            >
          {/each}
        </DropdownMenu.Content>
      </DropdownMenu.Root>
    </div>
  </section>

  <section class="border-b px-3 py-3">
    <h4 class="mb-3 text-sm font-medium">
      Sizing ladder <span class="text-muted-foreground font-normal">USD</span>
    </h4>
    <div
      class="relative mb-5 h-3 rounded-full bg-gradient-to-r from-[color-mix(in_oklab,var(--destructive)_45%,transparent)] via-[color-mix(in_oklab,var(--warning)_25%,transparent)] to-[color-mix(in_oklab,var(--success)_30%,transparent)]"
    >
      <span
        class="bg-destructive absolute -top-1 h-5 w-0.5"
        style="left:{pos(b.killLine)}%"
        title="Kill line"
      ></span>
      <span
        class="bg-muted-foreground absolute -top-1 h-5 w-0.5"
        style="left:{pos(b.capital)}%"
        title="Book capital"
      ></span>
      <span
        class="border-background bg-foreground absolute -top-0.5 size-4 -translate-x-1/2 rounded-full border-2"
        style="left:{pos(b.equity)}%"
        title="Equity now"
      ></span>
      <span
        class="text-muted-foreground num absolute top-4 text-[11px]"
        style="left:{pos(b.killLine)}%">kill {usd(b.killLine)}</span
      >
      <span
        class="num absolute top-4 -translate-x-1/2 text-[11px]"
        style="left:{pos(b.equity)}%">now {usd(b.equity)}</span
      >
    </div>
    <dl class="grid grid-cols-[1fr_auto] gap-x-4 gap-y-1.5 text-sm">
      {#each LADDER as [k, v, note] (k)}
        <dt class="flex flex-col">
          <span>{k}</span>
          <span class="text-muted-foreground text-xs">{note}</span>
        </dt>
        <dd class="num self-center text-right">{v}</dd>
      {/each}
    </dl>
  </section>

  <section class="px-3 py-3">
    <h4 class="mb-2 text-sm font-medium">Seats</h4>
    <ul class="grid gap-1">
      {#each b.seats as st (st.bot)}
        <li class="flex items-center gap-2 text-sm">
          <span
            class={cn(
              "size-2 rounded-full",
              st.state === "active" ? "bg-success" : "bg-warning",
            )}
          ></span>
          {st.bot}
          <span class="text-muted-foreground text-xs">{st.state}</span>
          <span class="num text-muted-foreground ml-auto text-xs">{st.r}</span>
          <span
            class={cn(
              "num w-16 text-right text-xs",
              st.pnl >= 0 ? "text-success" : "text-destructive",
            )}>{usd(st.pnl)}</span
          >
        </li>
      {/each}
    </ul>
    <p class="text-muted-foreground mt-2 text-xs">
      Benching is automatic after qualifying losses; it resets at the next
      period open.
    </p>
  </section>

  <div class="mt-auto flex flex-wrap gap-2 border-t px-3 py-2">
    <Button
      size="sm"
      variant="outline"
      onclick={() =>
        workbench.notify(
          `Editing drafts ${b.name} ${b.version.replace(/\d+/, (n) => String(+n + 1))}; the live version keeps trading.`,
        )}><GitBranch />Edit as new version</Button
    >
    <Button
      size="sm"
      variant="ghost"
      onclick={() => workbench.notify(`${b.name} saved as a template.`)}
      ><Copy />Save as template</Button
    >
  </div>
</div>
