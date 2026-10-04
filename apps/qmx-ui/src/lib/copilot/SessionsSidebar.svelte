<script lang="ts">
  /**
   * Your errands, by what they need: the ones waiting for you, the ones
   * working on their own, and earlier ones. Where an errand started (Lab,
   * Portfolio, Library, a mini app) is a small icon, not a separate list.
   * Helpers sit under their errand when it is open.
   */
  import Plus from "@lucide/svelte/icons/plus";
  import Search from "@lucide/svelte/icons/search";
  import MessagesSquare from "@lucide/svelte/icons/messages-square";
  import FlaskConical from "@lucide/svelte/icons/flask-conical";
  import BriefcaseBusiness from "@lucide/svelte/icons/briefcase-business";
  import LibraryBig from "@lucide/svelte/icons/library-big";
  import AppWindow from "@lucide/svelte/icons/app-window";
  import { Button } from "$lib/components/ui/button";
  import { Input } from "$lib/components/ui/input";
  import { cn } from "$lib/utils";
  import type { Session } from "./demo";

  let {
    sessions,
    active,
    onopen,
    onnew,
    waitingIds = [],
  }: {
    sessions: Session[];
    active: string | null;
    onopen: (id: string) => void;
    onnew: () => void;
    /** Errands with a question or approval pending. */
    waitingIds?: string[];
  } = $props();

  let query = $state("");
  const ICON = {
    Main: MessagesSquare,
    Lab: FlaskConical,
    Portfolio: BriefcaseBusiness,
    Library: LibraryBig,
    "Mini apps": AppWindow,
  };
  const q = $derived(query.trim().toLowerCase());
  const top = $derived(
    sessions.filter(
      (s) => !s.parent && (!q || s.title.toLowerCase().includes(q)),
    ),
  );
  const isWaiting = (s: Session) =>
    s.status === "waiting" || waitingIds.includes(s.id);
  const groups = $derived([
    { label: "Needs you", list: top.filter(isWaiting) },
    {
      label: "Working",
      list: top.filter((s) => s.status === "running" && !isWaiting(s)),
    },
    {
      label: "Earlier",
      list: top.filter((s) => s.status === "done" && !isWaiting(s)),
    },
  ]);
  const activeParent = $derived(
    sessions.find((s) => s.id === active)?.parent ?? null,
  );
  const kids = (id: string) => sessions.filter((s) => s.parent === id);
</script>

<aside aria-label="Errands" class="bg-panel flex h-full flex-col gap-3 p-3">
  <Button variant="outline" class="justify-start" onclick={onnew}>
    <Plus /> New errand
  </Button>
  <div class="relative">
    <Search
      class="text-muted-foreground pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2"
    />
    <Input
      bind:value={query}
      placeholder="Search errands"
      aria-label="Search errands"
      class="h-9 pl-9"
    />
  </div>
  <div class="min-h-0 flex-1 overflow-auto">
    {#each groups.filter((g) => g.list.length) as g (g.label)}
      <p class="text-muted-foreground mt-2 mb-1 px-2 text-sm font-medium">
        {g.label}
      </p>
      <ul class="flex flex-col gap-0.5">
        {#each g.list as s (s.id)}
          {@const Icon = ICON[s.origin]}
          <li>
            <button
              type="button"
              class={cn(
                "hover:bg-muted flex w-full items-start gap-2.5 rounded-lg px-2.5 py-2 text-left",
                active === s.id && "bg-muted",
              )}
              aria-current={active === s.id ? "true" : undefined}
              title={`Started in ${s.origin === "Main" ? "the main copilot" : s.origin}`}
              onclick={() => onopen(s.id)}
            >
              <Icon class="text-muted-foreground mt-1 size-4 shrink-0" />
              <span class="min-w-0 flex-1">
                <span class="block truncate">{s.title}</span>
                <span class="text-muted-foreground block text-sm">{s.age}</span>
              </span>
              {#if g.label !== "Earlier"}<span
                  class={cn(
                    "mt-2 size-2 shrink-0 rounded-full",
                    g.label === "Needs you"
                      ? "bg-warning"
                      : "bg-info remote-pulse",
                  )}
                ></span>{/if}
            </button>
            {#if kids(s.id).length && (active === s.id || activeParent === s.id)}
              <ul class="border-border my-1 ml-5 flex flex-col border-l pl-2">
                {#each kids(s.id) as k (k.id)}
                  <li>
                    <button
                      type="button"
                      class={cn(
                        "hover:bg-muted flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm",
                        active === k.id && "bg-muted",
                      )}
                      onclick={() => onopen(k.id)}
                    >
                      <span
                        class={cn(
                          "size-1.5 shrink-0 rounded-full",
                          k.status === "running"
                            ? "bg-info remote-pulse"
                            : "bg-success",
                        )}
                      ></span>
                      <span class="min-w-0 flex-1 truncate">{k.title}</span>
                    </button>
                  </li>
                {/each}
              </ul>
            {/if}
          </li>
        {/each}
      </ul>
    {/each}
  </div>
</aside>
