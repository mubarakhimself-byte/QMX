<script lang="ts">
  /**
   * Pod resources: a pod's ingredients, which are not a strategy's
   * (operator, 2026-10-03). Your pods and where each stands, the bots a
   * test runs over, blocks by slot, stress scenarios (yours included) and
   * the paper money a pod soaks on. Ticks here are what Test runs.
   */
  import Layers2 from "@lucide/svelte/icons/layers-2";
  import Bot from "@lucide/svelte/icons/bot";
  import Puzzle from "@lucide/svelte/icons/puzzle";
  import Siren from "@lucide/svelte/icons/siren";
  import Wallet from "@lucide/svelte/icons/wallet";
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
  import { workbench } from "$lib/workbench/workbench.svelte";
  import {
    BLOCKS,
    LAB_PODS,
    MY_STRESS,
    PAPER_MONEY,
    POD_TEMPLATES,
    SLOTS,
    STAGE_LABEL,
    STRESS,
    TEST_BOTS,
  } from "../pods";
  import { lab } from "../lab.svelte";

  const EXPLAIN: Record<string, string> = {
    pods: "Tick the pods a test should run. The highlighted one is the pod you are working on.",
    bots: "Every pod in a test sizes the same trades from these bots, so the difference you see is the pod.",
    blocks:
      "A green dot means the block is in the pod you are working on. Click a block to read and tune it; add it with the + in its slot.",
    stress:
      "Tick the crises a test replays. Yours sit beside the built-in ones.",
    money:
      "Pods soak on paper money first. Real money is only wired in Portfolio, after you sign the promotion.",
  };
  const TABS = [
    { id: "pods", label: "Pods", icon: Layers2 },
    { id: "bots", label: "Bots", icon: Bot },
    { id: "blocks", label: "Blocks", icon: Puzzle },
    { id: "stress", label: "Stress", icon: Siren },
    { id: "money", label: "Money", icon: Wallet },
  ] as const;
  let tab = $state<(typeof TABS)[number]["id"]>("pods");
  const pod = $derived(LAB_PODS.find((p) => p.id === lab.labPod));
  const STAGE_TONE = {
    draft: "var(--muted-foreground)",
    tested: "var(--info)",
    paper: "var(--tone-paper)",
    live: "var(--tone-live)",
  };

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
    title={label}
    onchange={flip}
  />
{/snippet}

<div class="flex h-full flex-col">
  <div
    class="flex h-9 shrink-0 items-center gap-0.5 border-b px-1.5"
    role="tablist"
    aria-label="Pod resources"
  >
    {#each TABS as t (t.id)}
      <button
        type="button"
        role="tab"
        aria-selected={tab === t.id}
        class={cn(
          "flex h-7 items-center gap-1.5 rounded-md px-1.5 text-xs @[20rem]:px-2",
          tab === t.id
            ? "bg-muted text-foreground"
            : "text-muted-foreground hover:text-foreground",
        )}
        title={t.label}
        onclick={() => (tab = t.id)}
        ><t.icon class="size-3.5" /><span class="hidden @[20rem]:inline"
          >{t.label}</span
        ></button
      >
    {/each}
    <InfoTip
      class="ml-auto"
      label="Explain this list"
      text={EXPLAIN[tab] ?? ""}
    />
    <!-- eslint-disable svelte/no-navigation-without-resolve -->
    <a
      href={`${resolve("/library")}?shelf=pods`}
      class="text-muted-foreground hover:text-foreground hover:bg-muted flex size-7 items-center justify-center rounded-md"
      aria-label="Open the Library"
      title="Open the Library"><LibraryBig class="size-3.5" /></a
    >
    <!-- eslint-enable svelte/no-navigation-without-resolve -->
  </div>

  <div class="min-h-0 flex-1 overflow-auto">
    {#if tab === "pods"}
      <ul class="p-1.5">
        {#each LAB_PODS as p (p.id)}
          <li
            class={cn(
              "flex items-center gap-2 rounded-md px-2 py-2",
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
              class="flex min-w-0 flex-1 items-center gap-2 text-left"
              onclick={() => (lab.labPod = p.id)}
            >
              <span
                class="size-2.5 shrink-0 rounded-full"
                style="background:{p.color}"
              ></span>
              <span class="min-w-0 flex-1">
                <span class="block truncate text-sm font-medium"
                  >{p.name}
                  <span class="text-muted-foreground font-normal"
                    >{p.version}</span
                  ></span
                >
                <span class="text-muted-foreground block truncate text-xs"
                  >{p.template}</span
                >
              </span>
              <span
                class="shrink-0 rounded border px-1.5 text-xs"
                style="color:{STAGE_TONE[
                  p.stage
                ]}; border-color:color-mix(in oklab, {STAGE_TONE[
                  p.stage
                ]} 50%, transparent)">{STAGE_LABEL[p.stage]}</span
              >
            </button>
          </li>
        {/each}
      </ul>
      <div class="px-3 pb-3">
        <DropdownMenu.Root>
          <DropdownMenu.Trigger
            class="hover:bg-muted flex h-8 w-full items-center justify-center gap-1.5 rounded-md border border-dashed text-sm"
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
      </div>
    {:else if tab === "bots"}
      <ul class="p-1.5">
        {#each TEST_BOTS as b (b.id)}
          <li class="hover:bg-muted/40 flex items-center gap-2 rounded-md px-2">
            <label class="flex flex-1 items-center gap-2 py-2">
              {@render tick(
                lab.botsTicked.includes(b.id),
                `Run tests over ${b.name}`,
                () => (lab.botsTicked = toggle(lab.botsTicked, b.id)),
              )}
              <span class="flex-1 text-sm">{b.name}</span>
              <span class="text-muted-foreground num text-xs">{b.symbol}</span>
            </label>
          </li>
        {/each}
      </ul>
      <p class="text-muted-foreground px-3 pb-3 text-xs">
        <!-- eslint-disable svelte/no-navigation-without-resolve -->
        <a
          href={`${resolve("/library")}?shelf=bots`}
          class="text-primary underline">More bots in the Library</a
        >
        <!-- eslint-enable svelte/no-navigation-without-resolve -->
      </p>
    {:else if tab === "blocks"}
      <div class="flex flex-col gap-3 p-3">
        {#each SLOTS as s (s.id)}
          <div>
            <p class="text-muted-foreground mb-1 text-xs">{s.label}</p>
            <div class="flex flex-wrap gap-1">
              {#each BLOCKS.filter((b) => b.slot === s.id) as b (b.id)}
                {@const inPod = pod?.stack[s.id].includes(b.id)}
                <button
                  type="button"
                  class={cn(
                    "rounded-md border px-2 py-1 text-left text-xs",
                    lab.block === b.id
                      ? "border-primary bg-primary/12"
                      : "hover:border-ring/60",
                    inPod && "font-medium",
                  )}
                  title={`${b.what}${inPod ? " (in this pod)" : ""}`}
                  onclick={() => (lab.block = b.id)}
                  >{#if inPod}<span class="text-success mr-1">●</span
                    >{/if}{b.name}</button
                >
              {/each}
            </div>
          </div>
        {/each}
      </div>
    {:else if tab === "stress"}
      <ul class="p-1.5">
        {#each [...STRESS.map( (s) => ({ ...s, by: "" }) ), ...MY_STRESS] as s (s.id)}
          <li class="hover:bg-muted/40 flex items-center gap-2 rounded-md px-2">
            <label class="flex flex-1 items-center gap-2 py-2">
              {@render tick(
                lab.stressTicked.includes(s.id),
                `Include ${s.name}`,
                () => (lab.stressTicked = toggle(lab.stressTicked, s.id)),
              )}
              <span class="flex-1 text-sm"
                >{s.name}{#if s.by}<span
                    class="text-muted-foreground block text-xs">{s.by}</span
                  >{/if}</span
              >
            </label>
          </li>
        {/each}
      </ul>
      <div class="px-3 pb-3">
        <DropdownMenu.Root>
          <DropdownMenu.Trigger
            class="hover:bg-muted flex h-8 w-full items-center justify-center gap-1.5 rounded-md border border-dashed text-sm"
            ><Plus class="size-3.5" />New scenario</DropdownMenu.Trigger
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
      </div>
    {:else}
      <ul class="p-1.5">
        {#each PAPER_MONEY as m (m.id)}
          <li class="rounded-md px-2 py-2">
            <div class="flex items-baseline justify-between gap-2">
              <span class="text-sm font-medium">{m.name}</span>
              <span class="num text-sm">{usd(m.balance)}</span>
            </div>
            <p class="text-muted-foreground text-xs">{m.note}</p>
          </li>
        {/each}
      </ul>
    {/if}
  </div>
</div>
