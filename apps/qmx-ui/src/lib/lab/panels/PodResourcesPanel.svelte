<script lang="ts">
  /**
   * Pod resources: a pod's ingredients (operator, 2026-10-03). One list in
   * groups, no tabs (DESIGN-RULES.md §4): your pods, the bots a test runs
   * over, stress scenarios and paper money. Ticks here are what Test runs.
   * Blocks are added from the Pod stack's "+" in each slot.
   */
  import ChevronDown from "@lucide/svelte/icons/chevron-down";
  import Plus from "@lucide/svelte/icons/plus";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import History from "@lucide/svelte/icons/history";
  import SlidersHorizontal from "@lucide/svelte/icons/sliders-horizontal";
  import LibraryBig from "@lucide/svelte/icons/library-big";
  import { resolve } from "$app/paths";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu";
  import { cn } from "$lib/utils";
  import InfoTip from "$lib/workbench/InfoTip.svelte";
  import { usd } from "$lib/portfolio/bits";
  import { panelSize } from "$lib/workbench/tiles/panel-size";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import {
    LAB_PODS,
    MY_STRESS,
    PAPER_MONEY,
    POD_TEMPLATES,
    STAGE_LABEL,
    STRESS,
    TEST_BOTS,
  } from "../pods";
  import { podModel } from "../pod-model.svelte";
  import { lab } from "../lab.svelte";

  const size = panelSize();
  const STAGE_TONE = {
    draft: "var(--muted-foreground)",
    tested: "var(--info)",
    paper: "var(--tone-paper)",
    live: "var(--tone-live)",
  };
  const SCENARIOS = [...STRESS.map((s) => ({ ...s, by: "" })), ...MY_STRESS];
  let open = $state({ pods: true, bots: true, stress: true, money: false });

  function toggle(list: string[], id: string) {
    return list.includes(id) ? list.filter((x) => x !== id) : [...list, id];
  }
</script>

{#snippet tick(on: boolean, label: string, flip: () => void)}
  <input
    type="checkbox"
    class="accent-primary size-3.5 shrink-0"
    checked={on}
    aria-label={label}
    onchange={flip}
  />
{/snippet}

{#snippet group(key: keyof typeof open, title: string, count: string)}
  <button
    type="button"
    class="text-muted-foreground hover:text-foreground py-row flex w-full items-center gap-1.5 text-xs font-medium"
    aria-expanded={open[key]}
    onclick={() => (open[key] = !open[key])}
  >
    <ChevronDown
      class={cn("size-3.5 transition-transform", !open[key] && "-rotate-90")}
    />
    {title}
    <span class="num ml-auto font-normal">{count}</span>
  </button>
{/snippet}

<div class="flex h-full flex-col">
  <div class="px-tile flex h-9 shrink-0 items-center gap-1">
    <span class="text-muted-foreground truncate px-1.5 text-xs"
      >{lab.podsTicked.length} pods · {lab.botsTicked.length} bots · {lab
        .stressTicked.length} crises</span
    >
    <InfoTip
      class="ml-auto"
      label="Explain this list"
      text="Tick what a test runs: pods, the bots they all size, and the crises they replay. The highlighted pod is the one you are working on. Pods soak on paper money before real money, which is wired in Portfolio after you sign."
    />
    <!-- eslint-disable svelte/no-navigation-without-resolve -->
    <a
      href={`${resolve("/library")}?shelf=pods`}
      class="text-muted-foreground hover:text-foreground hover:bg-muted flex size-7 shrink-0 items-center justify-center rounded-md"
      aria-label="Open the Library"
      title="Open the Library"><LibraryBig class="size-3.5" /></a
    >
    <!-- eslint-enable svelte/no-navigation-without-resolve -->
  </div>

  <div
    class="px-panel pb-panel gap-group flex min-h-0 flex-1 flex-col overflow-auto"
  >
    <section aria-label="Pods">
      {@render group(
        "pods",
        "Pods",
        `${lab.podsTicked.length}/${LAB_PODS.length}`,
      )}
      {#if open.pods}
        <ul>
          {#each LAB_PODS as p (p.id)}
            {@const stage = podModel.stage(p.id)}
            <li
              class={cn(
                "py-row -mx-1.5 flex items-center gap-2 rounded-md px-1.5",
                lab.labPod === p.id ? "bg-muted" : "hover:bg-muted/40",
              )}
            >
              {@render tick(
                lab.podsTicked.includes(p.id),
                `Include ${p.name} in tests`,
                () => (lab.podsTicked = toggle(lab.podsTicked, p.id)),
              )}
              <button
                type="button"
                class="flex min-w-0 flex-1 items-center gap-2 text-left text-sm"
                aria-pressed={lab.labPod === p.id}
                onclick={() => (lab.labPod = p.id)}
              >
                <span
                  class="size-2 shrink-0 rounded-full"
                  style="background:{p.color}"
                ></span>
                <span class="min-w-0 flex-1 truncate">{p.name}</span>
                {#if size.mode !== "compact"}<span
                    class="shrink-0 text-xs"
                    style="color:{STAGE_TONE[stage]}">{STAGE_LABEL[stage]}</span
                  >{:else}<span
                    class="size-1.5 shrink-0 rounded-full"
                    style="background:{STAGE_TONE[stage]}"
                    title={STAGE_LABEL[stage]}
                  ></span>{/if}
              </button>
            </li>
          {/each}
        </ul>
        <DropdownMenu.Root>
          <DropdownMenu.Trigger
            class="text-muted-foreground hover:text-foreground mt-row flex items-center gap-1.5 text-xs"
            ><Plus class="size-3.5" />New pod</DropdownMenu.Trigger
          >
          <DropdownMenu.Content class="w-72">
            <DropdownMenu.Item
              onclick={() =>
                lab.ask(
                  "Build me a new pod for my momentum bots: risk about 0.5% a trade, stop everything at −10%, and slow down on weekends.",
                )}><Sparkles />Describe it to the copilot</DropdownMenu.Item
            >
            <DropdownMenu.Separator />
            <DropdownMenu.Label>Start from a template</DropdownMenu.Label>
            {#each POD_TEMPLATES as t (t.id)}
              <DropdownMenu.Item
                onclick={() =>
                  workbench.notify(
                    `A draft from "${t.name}" opens in Design. Nothing changes until you save it.`,
                  )}
              >
                <span class="flex flex-col"
                  ><span>{t.name}</span><span
                    class="text-muted-foreground text-xs">{t.note}</span
                  ></span
                >
              </DropdownMenu.Item>
            {/each}
          </DropdownMenu.Content>
        </DropdownMenu.Root>
      {/if}
    </section>

    <section aria-label="Bots">
      {@render group(
        "bots",
        "Bots",
        `${lab.botsTicked.length}/${TEST_BOTS.length}`,
      )}
      {#if open.bots}
        <ul>
          {#each TEST_BOTS as b (b.id)}
            <li>
              <label class="py-row flex items-center gap-2 text-sm">
                {@render tick(
                  lab.botsTicked.includes(b.id),
                  `Run tests over ${b.name}`,
                  () => (lab.botsTicked = toggle(lab.botsTicked, b.id)),
                )}
                <span class="min-w-0 flex-1 truncate">{b.name}</span>
                {#if size.mode !== "compact"}<span
                    class="text-muted-foreground num text-xs">{b.symbol}</span
                  >{/if}
              </label>
            </li>
          {/each}
        </ul>
      {/if}
    </section>

    <section aria-label="Stress">
      {@render group(
        "stress",
        "Crises",
        `${lab.stressTicked.length}/${SCENARIOS.length}`,
      )}
      {#if open.stress}
        <ul>
          {#each SCENARIOS as s (s.id)}
            <li>
              <label class="py-row flex items-center gap-2 text-sm">
                {@render tick(
                  lab.stressTicked.includes(s.id),
                  `Include ${s.name}`,
                  () => (lab.stressTicked = toggle(lab.stressTicked, s.id)),
                )}
                <span class="min-w-0 flex-1 truncate" title={s.name}
                  >{s.name}</span
                >
                {#if s.by}<span class="text-info shrink-0 text-xs">Yours</span
                  >{/if}
              </label>
            </li>
          {/each}
        </ul>
        <DropdownMenu.Root>
          <DropdownMenu.Trigger
            class="text-muted-foreground hover:text-foreground mt-row flex items-center gap-1.5 text-xs"
            ><Plus class="size-3.5" />New crisis</DropdownMenu.Trigger
          >
          <DropdownMenu.Content class="w-72">
            <DropdownMenu.Item
              onclick={() =>
                lab.ask(
                  "Build a stress scenario: BTC drops 15% in an hour while Binance pauses withdrawals for 6 hours.",
                )}><Sparkles />Describe it to the copilot</DropdownMenu.Item
            >
            <DropdownMenu.Item
              onclick={() =>
                workbench.notify(
                  "Pick dates on the chart; the test replays that stretch of real prices through every pod.",
                )}><History />Replay real dates</DropdownMenu.Item
            >
            <DropdownMenu.Item
              onclick={() =>
                workbench.notify(
                  "Set the shocks yourself: price move, speed, spread, outage length, stablecoin price.",
                )}
              ><SlidersHorizontal />Set the shocks by hand</DropdownMenu.Item
            >
          </DropdownMenu.Content>
        </DropdownMenu.Root>
      {/if}
    </section>

    <section aria-label="Paper money">
      {@render group("money", "Paper money", `${PAPER_MONEY.length}`)}
      {#if open.money}
        <ul>
          {#each PAPER_MONEY as m (m.id)}
            <li
              class="py-row flex items-baseline justify-between gap-2 text-sm"
              title={m.note}
            >
              <span class="truncate">{m.name}</span>
              <span class="num shrink-0">{usd(m.balance)}</span>
            </li>
          {/each}
        </ul>
      {/if}
    </section>
  </div>
</div>
