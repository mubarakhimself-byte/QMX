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
  import X from "@lucide/svelte/icons/x";
  import FileBox from "@lucide/svelte/icons/file-box";
  import Rss from "@lucide/svelte/icons/rss";
  import Newspaper from "@lucide/svelte/icons/newspaper";
  import AppWindowMac from "@lucide/svelte/icons/app-window-mac";
  import { SOURCES, FEED, HEADLINES, NEWS_CONSUMERS } from "$lib/demo/feeds";

  /** Omarchy-style web app: the site gets its own window. */
  function openWebApp(url: string, name: string) {
    window.open(url, `qmx-webapp-${name}`, "popup,width=1280,height=860");
  }
  let feedKind = $state<string | null>(null);
  import * as Tabs from "$lib/components/ui/tabs";
  import { Input } from "$lib/components/ui/input";
  import { Button } from "$lib/components/ui/button";
  import PageHeader from "$lib/workbench/PageHeader.svelte";
  import EmptyState from "$lib/workbench/EmptyState.svelte";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import EntityCard from "$lib/qmx/EntityCard.svelte";
  import { DEMO_ENTITIES, DEMO_ARTIFACTS } from "$lib/demo/assets";
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
    { id: "sources", label: "Sources", icon: Rss },
    { id: "news", label: "News", icon: Newspaper },
    { id: "files", label: "Artifacts", icon: FileBox },
    { id: "artifact", label: "Bots & models", icon: Package },
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

  /** Stable hue per section so cards are scannable by colour and label. */
  const HUES = [
    "--chart-1",
    "--chart-2",
    "--chart-3",
    "--chart-4",
    "--chart-5",
  ];
  const sections = $derived.by(() => {
    const counts: Record<string, number> = {};
    for (const a of articles) counts[a.section] = (counts[a.section] ?? 0) + 1;
    return Object.entries(counts).sort((a, b) => b[1] - a[1]);
  });
  const hueOf = (s: string) =>
    HUES[
      Math.max(
        0,
        sections.findIndex(([n]) => n === s),
      ) % HUES.length
    ];
  const q = $derived(query.trim().toLowerCase());
  const hits = $derived(
    articles.filter(
      (a) =>
        (!section || a.section === section) &&
        (!q ||
          a.title.toLowerCase().includes(q) ||
          a.summary.toLowerCase().includes(q)),
    ),
  );
  const open = $derived(articles.find((a) => a.id === openId));
  const assets = $derived(
    DEMO_ENTITIES.filter((a) =>
      kind === "artifact"
        ? a.kind === "bot" || a.kind === "model"
        : a.kind === "app" || a.kind === "workflow",
    ).filter(
      (a) =>
        !q ||
        a.name.toLowerCase().includes(q) ||
        a.summary.toLowerCase().includes(q),
    ),
  );
  const chip = (on: boolean) =>
    cn(
      "flex h-7 shrink-0 items-center gap-1.5 rounded-full border px-3 text-sm transition-colors",
      on
        ? "bg-primary text-primary-foreground border-transparent"
        : "hover:bg-muted",
    );
</script>

<div class="flex h-full flex-col">
  {#if demo}
    <div
      class="bg-warning/15 flex h-7 shrink-0 items-center gap-2 px-3 text-xs"
    >
      <FlaskConical class="text-warning size-3.5" />
      Demo Library. MQL5 article titles and excerpts from your local catalog; bots,
      models, apps and workflows are samples.
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

  {#if !demo}
    <EmptyState
      class="flex-1"
      icon={KINDS.find((k) => k.id === kind)?.icon}
      title="Nothing here yet"
      description="Items appear here once QMX is connected to its daemon."
    />
  {:else}
    <div class="flex min-h-0 flex-1">
      <div class="flex min-w-0 flex-1 flex-col">
        <div class="flex flex-col gap-2 px-4 pt-3 pb-2">
          <div class="relative max-w-2xl">
            <Search
              class="text-muted-foreground pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2"
            />
            <Input
              bind:value={query}
              class="well h-9 border-0 pl-9"
              placeholder={kind === "knowledge"
                ? "Search titles and excerpts"
                : "Search names and roles"}
              aria-label="Search the Library"
            />
          </div>
          {#if kind === "knowledge"}
            <div
              class="flex gap-1.5 overflow-x-auto pb-1"
              role="group"
              aria-label="Sections"
            >
              <button
                type="button"
                class={chip(!section)}
                aria-pressed={!section}
                onclick={() => (section = null)}
              >
                All <span class="num opacity-70">{articles.length}</span>
              </button>
              {#each sections as [name, n] (name)}
                <button
                  type="button"
                  class={chip(section === name)}
                  aria-pressed={section === name}
                  onclick={() => (section = section === name ? null : name)}
                >
                  <span
                    class="size-2 rounded-full"
                    style="background: var({hueOf(name)})"
                  ></span>
                  {name} <span class="num opacity-70">{n}</span>
                </button>
              {/each}
            </div>
          {/if}
        </div>

        <div class="min-h-0 flex-1 overflow-auto px-4 pb-4">
          {#if kind === "knowledge"}
            <p class="text-muted-foreground mb-2 text-sm" role="status">
              {#if loadState === "loading"}Loading…{:else if loadState === "failed"}Could
                not load the demo catalog.{:else}{hits.length} articles{/if}
            </p>
            <ul
              class="grid gap-3 sm:grid-cols-2 2xl:grid-cols-3"
              aria-label="Articles"
            >
              {#each hits.slice(0, 120) as a (a.id)}
                <li>
                  <button
                    type="button"
                    class={cn(
                      "surface flex h-full w-full flex-col gap-2 overflow-hidden rounded-lg p-4 text-left transition-transform hover:-translate-y-0.5",
                      openId === a.id && "ring-ring ring-2",
                    )}
                    aria-current={openId === a.id ? "true" : undefined}
                    onclick={() => (openId = a.id)}
                  >
                    <span class="flex items-center gap-2 text-xs">
                      <span
                        class="h-3 w-1 rounded-full"
                        style="background: var({hueOf(a.section)})"
                      ></span>
                      <span class="text-muted-foreground">{a.section}</span>
                      {#if a.part}<span class="text-muted-foreground"
                          >· Part {a.part}</span
                        >{/if}
                      <span class="num text-muted-foreground ml-auto"
                        >{a.published}</span
                      >
                    </span>
                    <span class="text-[15px] leading-snug font-semibold"
                      >{a.title}</span
                    >
                    <span
                      class="text-muted-foreground line-clamp-3 text-sm leading-relaxed"
                      >{a.summary}</span
                    >
                  </button>
                </li>
              {/each}
            </ul>
          {:else if kind === "sources"}
            <div class="grid gap-4 xl:grid-cols-[22rem_minmax(0,1fr)]">
              <section aria-label="Sources" class="flex flex-col gap-2">
                {#each SOURCES as src (src.id)}
                  <div class="surface flex flex-col gap-2 rounded-lg p-3.5">
                    <div class="flex items-center gap-2">
                      <span class="font-medium">{src.name}</span>
                      <span
                        class="bg-muted ml-auto rounded-sm px-1.5 py-0.5 text-[11px]"
                        >{src.kind}</span
                      >
                    </div>
                    <p class="text-muted-foreground text-sm">{src.how}</p>
                    <div class="flex items-center gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onclick={() => openWebApp(src.url, src.id)}
                      >
                        <AppWindowMac /> Open as web app
                      </Button>
                      <span
                        class={cn(
                          "ml-auto text-[11px]",
                          src.status === "ruled"
                            ? "text-success"
                            : "text-muted-foreground",
                        )}
                      >
                        {src.status === "ruled"
                          ? "Ruled source"
                          : "Proposed · needs backend"}
                      </span>
                    </div>
                  </div>
                {/each}
              </section>
              <section
                aria-label="Latest from your sources"
                class="flex flex-col gap-2"
              >
                <div class="flex flex-wrap gap-1.5">
                  {#each [null, "Papers", "Articles", "Calendar"] as k (k ?? "all")}
                    <button
                      type="button"
                      class={chip(feedKind === k)}
                      aria-pressed={feedKind === k}
                      onclick={() => (feedKind = k)}>{k ?? "Everything"}</button
                    >
                  {/each}
                </div>
                <p class="text-muted-foreground text-xs">
                  Sample items. The daemon fetches feeds and stores what you
                  keep.
                </p>
                <ul class="flex flex-col gap-2">
                  {#each FEED.filter((f) => !feedKind || f.kind === feedKind) as f (f.id)}
                    <li class="surface flex items-start gap-3 rounded-lg p-3.5">
                      <span class="min-w-0 flex-1">
                        <span class="text-muted-foreground block text-xs"
                          >{f.source} · {f.age}</span
                        >
                        <span class="block font-medium">{f.title}</span>
                        <span class="mt-1 flex gap-1"
                          >{#each f.tags as t (t)}<span
                              class="bg-muted rounded-sm px-1.5 text-[11px]"
                              >{t}</span
                            >{/each}</span
                        >
                      </span>
                      <Button
                        size="sm"
                        variant="ghost"
                        onclick={() => workbench.addRef(f.title)}
                        ><MessageSquarePlus /> Copilot</Button
                      >
                    </li>
                  {/each}
                </ul>
              </section>
            </div>
          {:else if kind === "news"}
            <div class="grid gap-4 xl:grid-cols-[minmax(0,1fr)_20rem]">
              <section
                aria-label="Headlines"
                class="surface overflow-hidden rounded-lg"
              >
                <div class="flex items-center gap-2 border-b px-4 py-2.5">
                  <span class="bg-destructive size-2 animate-pulse rounded-full"
                  ></span>
                  <span class="panel-label">Headlines · sample</span>
                </div>
                <ul>
                  {#each HEADLINES as h (h.time + h.title)}
                    <li
                      class="hover:bg-muted/40 grid grid-cols-[3.5rem_minmax(0,1fr)_auto] items-start gap-3 border-t px-4 py-3 first:border-t-0"
                    >
                      <span class="num text-muted-foreground text-sm"
                        >{h.time}</span
                      >
                      <span class="min-w-0">
                        <span class="block font-medium">{h.title}</span>
                        <span
                          class="text-muted-foreground mt-0.5 flex items-center gap-2 text-xs"
                        >
                          {h.source}
                          {#each h.symbols as sym (sym)}<span
                              class="bg-muted text-foreground rounded-sm px-1.5"
                              >{sym}</span
                            >{/each}
                          <span
                            class={h.tone === "positive"
                              ? "text-success"
                              : h.tone === "negative"
                                ? "text-destructive"
                                : ""}
                          >
                            {h.tone === "positive"
                              ? "▲"
                              : h.tone === "negative"
                                ? "▼"
                                : "●"}
                            {h.tone}
                          </span>
                        </span>
                      </span>
                      <span
                        class={cn(
                          "rounded-sm px-1.5 py-0.5 text-[10px] uppercase",
                          h.impact === "high"
                            ? "bg-destructive/15 text-destructive"
                            : h.impact === "medium"
                              ? "bg-warning/15 text-warning"
                              : "bg-muted text-muted-foreground",
                        )}>{h.impact}</span
                      >
                    </li>
                  {/each}
                </ul>
              </section>
              <aside class="flex flex-col gap-2">
                <p class="panel-label">Where news goes</p>
                {#each NEWS_CONSUMERS as c (c.name)}
                  <div class="surface rounded-lg p-3.5">
                    <p class="font-medium">{c.name}</p>
                    <p class="text-muted-foreground text-sm">{c.what}</p>
                  </div>
                {/each}
              </aside>
            </div>
          {:else if kind === "files"}
            <div class="surface overflow-hidden rounded-lg">
              <table class="w-full text-sm">
                <thead class="text-muted-foreground text-left text-xs">
                  <tr>
                    <th class="px-4 py-2.5 font-medium">Artifact</th>
                    <th class="font-medium">Type</th>
                    <th class="font-medium">Produced by</th>
                    <th class="font-medium">Fingerprint</th>
                    <th class="px-4 text-right font-medium">Size</th>
                  </tr>
                </thead>
                <tbody>
                  {#each DEMO_ARTIFACTS.filter((a) => !q || a.name
                        .toLowerCase()
                        .includes(q)) as a (a.id)}
                    <tr class="hover:bg-muted/50 border-t">
                      <td class="px-4 py-3">
                        <span class="block font-medium">{a.name}</span>
                        <span class="text-muted-foreground text-xs"
                          >{a.date}</span
                        >
                      </td>
                      <td
                        ><span class="bg-muted rounded-sm px-2 py-0.5 text-xs"
                          >{a.type}</span
                        ></td
                      >
                      <td class="text-muted-foreground">{a.producedBy}</td>
                      <td class="num text-muted-foreground text-xs">{a.fp}</td>
                      <td class="num px-4 text-right">{a.size}</td>
                    </tr>
                  {/each}
                </tbody>
              </table>
            </div>
          {:else}
            <ul
              class="grid gap-3 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4"
              aria-label="Assets"
            >
              {#each assets as a (a.id)}
                <li>
                  <EntityCard
                    entity={a}
                    href={resolve("/library/[id]", { id: a.id })}
                  />
                </li>
              {/each}
            </ul>
          {/if}
        </div>
      </div>

      {#if kind === "knowledge" && open}
        <article
          class="bg-panel flex w-[28rem] shrink-0 flex-col overflow-auto border-l p-5"
        >
          <div class="flex items-start gap-2">
            <p class="panel-label">Knowledge · MQL5 article</p>
            <Button
              variant="ghost"
              size="icon-xs"
              class="ml-auto"
              aria-label="Close article"
              onclick={() => (openId = null)}
            >
              <X />
            </Button>
          </div>
          <h2 class="mt-1 text-xl leading-snug font-semibold">{open.title}</h2>
          <p class="text-muted-foreground mt-1 text-sm">
            {open.published} · {open.section}{open.series
              ? ` · ${open.series}`
              : ""}
          </p>
          <div class="mt-4 flex flex-wrap gap-2">
            <Button
              size="sm"
              href={resolve("/library/article/[id]", { id: String(open.id) })}
            >
              <BookOpen /> Read
            </Button>
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
          <p class="panel-label mt-6">Excerpt</p>
          <p class="mt-1.5 text-[15px] leading-relaxed">{open.summary}</p>
          <p class="text-muted-foreground mt-6 text-sm">
            A generated summary, key points and the full text come from the
            daemon's Library once it is connected.
          </p>
        </article>
      {/if}
    </div>
  {/if}
</div>
