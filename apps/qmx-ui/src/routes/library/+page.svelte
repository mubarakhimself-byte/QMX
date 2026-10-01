<script lang="ts">
  import { onMount } from "svelte";
  import { resolve } from "$app/paths";
  import Search from "@lucide/svelte/icons/search";
  import Package from "@lucide/svelte/icons/package";
  import BookOpen from "@lucide/svelte/icons/book-open";
  import Blocks from "@lucide/svelte/icons/blocks";
  import ExternalLink from "@lucide/svelte/icons/external-link";
  import MessageSquarePlus from "@lucide/svelte/icons/message-square-plus";
  import FlaskConical from "@lucide/svelte/icons/flask-conical";
  import * as Resizable from "$lib/components/ui/resizable";
  import * as Tabs from "$lib/components/ui/tabs";
  import { Input } from "$lib/components/ui/input";
  import { Button } from "$lib/components/ui/button";
  import { Badge } from "$lib/components/ui/badge";
  import PageHeader from "$lib/workbench/PageHeader.svelte";
  import EmptyState from "$lib/workbench/EmptyState.svelte";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { cn } from "$lib/utils";

  type Article = {
    id: number;
    title: string;
    summary: string;
    published: string;
    section: string;
    series: string | null;
    part: number | null;
    url: string;
  };

  // Hit kinds stay separate; each keeps its own actions (UI LIBRARY §5).
  const KINDS = [
    { id: "knowledge", label: "Knowledge", icon: BookOpen },
    { id: "artifact", label: "Artifacts", icon: Package },
    { id: "contribution", label: "Apps & workflows", icon: Blocks },
  ] as const;
  let kind = $state<string>("knowledge");

  const demo = workbench.demoMode;
  let articles = $state.raw<Article[]>([]);
  let loadState = $state<"idle" | "loading" | "ready" | "failed">("idle");
  let query = $state("");
  let section = $state<string | null>(null);
  let openId = $state<number | null>(null);

  onMount(async () => {
    if (!demo) return;
    loadState = "loading";
    try {
      const res = await fetch(resolve("/demo/mql5-articles.json" as "/"));
      if (!res.ok) throw new Error(String(res.status));
      articles = (await res.json()).articles;
      loadState = "ready";
    } catch {
      loadState = "failed";
    }
  });

  const sections = $derived.by(() => {
    const counts: Record<string, number> = {};
    for (const a of articles) counts[a.section] = (counts[a.section] ?? 0) + 1;
    return Object.entries(counts).sort((a, b) => b[1] - a[1]);
  });
  const hits = $derived.by(() => {
    const q = query.trim().toLowerCase();
    return articles.filter(
      (a) =>
        (!section || a.section === section) &&
        (!q ||
          a.title.toLowerCase().includes(q) ||
          a.summary.toLowerCase().includes(q)),
    );
  });
  const open = $derived(articles.find((a) => a.id === openId));
</script>

<div class="flex h-full flex-col">
  {#if demo}
    <div
      class="bg-warning/15 flex h-7 shrink-0 items-center gap-2 px-3 text-xs"
    >
      <FlaskConical class="text-warning size-3.5" />
      Demo Library. Titles and short excerpts of MQL5 articles from your local catalog;
      search runs in this window, not on the daemon.
    </div>
  {/if}
  <PageHeader title="Library" subtitle="Everything QMX knows and has made">
    {#snippet actions()}
      <Tabs.Root bind:value={kind}>
        <Tabs.List>
          {#each KINDS as k (k.id)}
            <Tabs.Trigger value={k.id}><k.icon />{k.label}</Tabs.Trigger>
          {/each}
        </Tabs.List>
      </Tabs.Root>
    {/snippet}
  </PageHeader>

  {#if kind !== "knowledge" || !demo}
    <EmptyState
      class="flex-1"
      icon={KINDS.find((k) => k.id === kind)?.icon}
      title={`No ${KINDS.find((k) => k.id === kind)?.label.toLowerCase()}`}
      description="Items appear here once QMX is connected to its daemon."
    />
  {:else}
    <Resizable.PaneGroup direction="horizontal" class="min-h-0 flex-1">
      <Resizable.Pane defaultSize={18} minSize={12} maxSize={28}>
        <nav aria-label="Sections" class="bg-panel h-full overflow-auto p-2">
          <p class="panel-label px-2 pb-1.5">Sections</p>
          <ul class="flex flex-col text-sm">
            <li>
              <button
                type="button"
                class={cn(
                  "hover:bg-muted flex w-full justify-between rounded-sm px-2 py-1",
                  !section && "bg-muted",
                )}
                aria-current={!section ? "true" : undefined}
                onclick={() => (section = null)}
              >
                All <span class="text-muted-foreground tabular"
                  >{articles.length}</span
                >
              </button>
            </li>
            {#each sections as [name, n] (name)}
              <li>
                <button
                  type="button"
                  class={cn(
                    "hover:bg-muted flex w-full justify-between gap-2 rounded-sm px-2 py-1 text-left",
                    section === name && "bg-muted",
                  )}
                  aria-current={section === name ? "true" : undefined}
                  onclick={() => (section = name)}
                >
                  <span class="truncate">{name}</span>
                  <span class="text-muted-foreground tabular">{n}</span>
                </button>
              </li>
            {/each}
          </ul>
        </nav>
      </Resizable.Pane>
      <Resizable.Handle />
      <Resizable.Pane defaultSize={42} minSize={28}>
        <section aria-label="Results" class="flex h-full flex-col">
          <div class="relative border-b p-2">
            <Search
              class="text-muted-foreground pointer-events-none absolute top-1/2 left-4 size-4 -translate-y-1/2"
            />
            <Input
              bind:value={query}
              class="h-8 pl-8"
              placeholder="Search titles and excerpts"
              aria-label="Search the Library"
            />
          </div>
          <p class="text-muted-foreground px-3 py-1.5 text-xs" role="status">
            {#if loadState === "loading"}Loading…{:else if loadState === "failed"}Could
              not load the demo catalog.{:else}{hits.length} articles{/if}
          </p>
          <ul class="min-h-0 flex-1 overflow-auto">
            {#each hits.slice(0, 200) as a (a.id)}
              <li>
                <button
                  type="button"
                  class={cn(
                    "hover:bg-muted/50 flex w-full flex-col gap-1 border-b px-3 py-2 text-left",
                    openId === a.id && "bg-muted",
                  )}
                  aria-current={openId === a.id ? "true" : undefined}
                  onclick={() => (openId = a.id)}
                >
                  <span class="text-sm leading-snug font-medium">{a.title}</span
                  >
                  <span
                    class="text-muted-foreground flex items-center gap-2 text-xs"
                  >
                    <span class="tabular">{a.published}</span>
                    <Badge variant="secondary" class="h-4 px-1.5 text-[10px]"
                      >{a.section}</Badge
                    >
                    {#if a.part}<span>Part {a.part}</span>{/if}
                  </span>
                  <span class="text-muted-foreground line-clamp-2 text-xs"
                    >{a.summary}</span
                  >
                </button>
              </li>
            {/each}
          </ul>
        </section>
      </Resizable.Pane>
      <Resizable.Handle />
      <Resizable.Pane defaultSize={40} minSize={25}>
        {#if open}
          <article class="bg-panel flex h-full flex-col overflow-auto p-4">
            <p class="panel-label">Knowledge · MQL5 article</p>
            <h2 class="mt-1 text-lg leading-snug font-semibold">
              {open.title}
            </h2>
            <p class="text-muted-foreground mt-1 text-xs">
              {open.published} · {open.section}{open.series
                ? ` · ${open.series}`
                : ""}
            </p>
            <div class="mt-3 flex flex-wrap gap-2">
              <Button
                size="sm"
                variant="outline"
                onclick={() => workbench.addRef(open.title)}
              >
                <MessageSquarePlus /> Add to copilot
              </Button>
              <Button
                size="sm"
                variant="outline"
                href={open.url}
                target="_blank"
                rel="noopener noreferrer"
              >
                <ExternalLink /> Open original
              </Button>
            </div>
            <p class="panel-label mt-5">Excerpt</p>
            <p class="mt-1 text-sm leading-relaxed">{open.summary}</p>
            <p class="text-muted-foreground mt-5 text-xs">
              A generated summary, key points and the full text come from the
              daemon's Library once it is connected.
            </p>
          </article>
        {:else}
          <EmptyState
            class="bg-panel h-full"
            icon={BookOpen}
            title="Select an article"
            description="Read its excerpt, add it to a copilot conversation, or open the original."
          />
        {/if}
      </Resizable.Pane>
    </Resizable.PaneGroup>
  {/if}
</div>
