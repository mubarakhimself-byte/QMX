<script lang="ts">
  /**
   * Every copilot session in one place: what is running now and what is
   * waiting for you on top, then sessions grouped by where they started
   * (operator, 2026-10-03: collections per page). Any of them can be opened
   * here and continued by the main copilot. Sessions can run for days.
   */
  import Plus from "@lucide/svelte/icons/plus";
  import Search from "@lucide/svelte/icons/search";
  import ChevronRight from "@lucide/svelte/icons/chevron-right";
  import Pin from "@lucide/svelte/icons/pin";
  import MessagesSquare from "@lucide/svelte/icons/messages-square";
  import FlaskConical from "@lucide/svelte/icons/flask-conical";
  import BriefcaseBusiness from "@lucide/svelte/icons/briefcase-business";
  import LibraryBig from "@lucide/svelte/icons/library-big";
  import AppWindow from "@lucide/svelte/icons/app-window";
  import { Button } from "$lib/components/ui/button";
  import { Input } from "$lib/components/ui/input";
  import { cn } from "$lib/utils";
  import type { Origin, Session } from "./demo";

  let {
    sessions,
    active,
    onopen,
    onnew,
  }: {
    sessions: Session[];
    active: string | null;
    onopen: (id: string) => void;
    onnew: () => void;
  } = $props();

  let query = $state("");
  let folded = $state<string[]>([]);
  const ORIGINS: Origin[] = [
    "Main",
    "Lab",
    "Portfolio",
    "Library",
    "Mini apps",
  ];
  const ICON = {
    Main: MessagesSquare,
    Lab: FlaskConical,
    Portfolio: BriefcaseBusiness,
    Library: LibraryBig,
    "Mini apps": AppWindow,
  };
  const STATUS = {
    running: { dot: "bg-info remote-pulse", text: "Running" },
    waiting: { dot: "bg-warning", text: "Waiting for you" },
    done: { dot: "bg-muted-foreground/40", text: "" },
  };
  const q = $derived(query.trim().toLowerCase());
  const shown = $derived(
    sessions.filter((s) => !q || s.title.toLowerCase().includes(q)),
  );
  const live = $derived(shown.filter((s) => s.status !== "done"));
  const groups = $derived([
    {
      label: "Pinned",
      list: shown.filter((s) => s.pinned && s.status === "done"),
    },
    ...ORIGINS.map((o) => ({
      label:
        o === "Main"
          ? "Main copilot"
          : `From ${o === "Mini apps" ? "mini apps" : `the ${o}`}`,
      list: shown.filter(
        (s) => s.origin === o && !s.pinned && s.status === "done",
      ),
    })),
  ]);
</script>

{#snippet row(s: Session)}
  {@const Icon = ICON[s.origin]}
  <li>
    <button
      type="button"
      class={cn(
        "hover:bg-muted flex w-full items-start gap-2 rounded-md px-2 py-1.5 text-left",
        active === s.id && "bg-muted",
      )}
      aria-current={active === s.id ? "true" : undefined}
      onclick={() => onopen(s.id)}
    >
      <Icon class="text-muted-foreground mt-0.5 size-3.5 shrink-0" />
      <span class="min-w-0 flex-1">
        <span class="block truncate text-sm">{s.title}</span>
        <span class="text-muted-foreground flex items-center gap-1.5 text-xs">
          <span class={cn("size-1.5 rounded-full", STATUS[s.status].dot)}
          ></span>
          {STATUS[s.status].text || s.age}{#if s.status !== "done"}
            · {s.age}{/if}{#if s.agents && s.status === "running"}
            · {s.agents} agents{/if}
        </span>
      </span>
    </button>
  </li>
{/snippet}

<aside aria-label="Sessions" class="bg-panel flex h-full flex-col gap-2 p-2">
  <Button variant="outline" size="sm" class="justify-start" onclick={onnew}>
    <Plus /> New session
  </Button>
  <div class="relative">
    <Search
      class="text-muted-foreground pointer-events-none absolute top-1/2 left-2.5 size-3.5 -translate-y-1/2"
    />
    <Input
      bind:value={query}
      placeholder="Search sessions"
      aria-label="Search sessions"
      class="h-8 pl-8"
    />
  </div>
  <div class="min-h-0 flex-1 overflow-auto">
    {#if live.length}
      <div class="bg-muted/25 mb-2 rounded-lg p-1">
        <p class="text-muted-foreground px-1 py-1 text-xs font-semibold">
          Going on now
        </p>
        <ul>
          {#each live as s (s.id)}{@render row(s)}{/each}
        </ul>
      </div>
    {/if}
    {#each groups.filter((g) => g.list.length) as g (g.label)}
      {@const shut = folded.includes(g.label)}
      <div class="mb-1">
        <button
          type="button"
          class="text-muted-foreground hover:text-foreground flex w-full items-center gap-1.5 px-1 py-1.5 text-xs font-semibold"
          aria-expanded={!shut}
          onclick={() =>
            (folded = shut
              ? folded.filter((x) => x !== g.label)
              : [...folded, g.label])}
        >
          {#if g.label === "Pinned"}<Pin class="size-3" />{/if}
          <span class="flex-1 text-left">{g.label}</span>
          <span class="num font-normal">{g.list.length}</span>
          <ChevronRight
            class={cn("size-3.5 transition-transform", !shut && "rotate-90")}
          />
        </button>
        {#if !shut}
          <ul>
            {#each g.list as s (s.id)}{@render row(s)}{/each}
          </ul>
        {/if}
      </div>
    {/each}
  </div>
</aside>
