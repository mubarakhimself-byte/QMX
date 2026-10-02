<script lang="ts">
  import { onMount } from "svelte";
  import { resolve } from "$app/paths";
  import Search from "@lucide/svelte/icons/search";
  import Package from "@lucide/svelte/icons/package";
  import BookOpen from "@lucide/svelte/icons/book-open";
  import Blocks from "@lucide/svelte/icons/blocks";
  import FileBox from "@lucide/svelte/icons/file-box";
  import Rss from "@lucide/svelte/icons/rss";
  import ExternalLink from "@lucide/svelte/icons/external-link";
  import Maximize2 from "@lucide/svelte/icons/maximize-2";
  import MessageSquarePlus from "@lucide/svelte/icons/message-square-plus";
  import Lightbulb from "@lucide/svelte/icons/lightbulb";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import RotateCw from "@lucide/svelte/icons/rotate-cw";
  import FlaskConical from "@lucide/svelte/icons/flask-conical";
  import * as Tabs from "$lib/components/ui/tabs";
  import * as Resizable from "$lib/components/ui/resizable";
  import { Input } from "$lib/components/ui/input";
  import { Button } from "$lib/components/ui/button";
  import { Skeleton } from "$lib/components/ui/skeleton";
  import PageHeader from "$lib/workbench/PageHeader.svelte";
  import EmptyState from "$lib/workbench/EmptyState.svelte";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import EntityCard from "$lib/qmx/EntityCard.svelte";
  import { loadArticleText, type ArticleText } from "$lib/qmx/article";
  import { DEMO_ENTITIES, DEMO_ARTIFACTS } from "$lib/demo/assets";
  import { SOURCES, FEED } from "$lib/demo/feeds";
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
  let text = $state<ArticleText | null>(null);
  let textFor = $state<number | null>(null);

  onMount(async () => {
    if (!demo) return;
    loadState = "loading";
    try {
      const res = await fetch(resolve("/demo/mql5-articles.json" as "/"));
      if (!res.ok) throw new Error(String(res.status));
      articles = (await res.json()).articles;
      loadState = "ready";
      openId = articles[0]?.id ?? null;
    } catch {
      loadState = "failed";
    }
  });

  // Load the selected article's text into the reader pane.
  $effect(() => {
    const id = openId;
    if (id === null || id === textFor) return;
    textFor = id;
    text = null;
    loadArticleText(id).then((t) => {
      if (textFor === id) text = t;
    });
  });

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
  const entities = $derived(
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

  // Sources open inside QMX. Some sites refuse to be embedded; then the
  // pane says so and offers the desktop browser instead.
  let sourceId = $state(SOURCES[0].id);
  const source = $derived(SOURCES.find((s) => s.id === sourceId)!);
  let frameKey = $state(0);
</script>

<div class="flex h-full flex-col">
  {#if demo}
    <div
      class="bg-warning/15 flex h-7 shrink-0 items-center gap-2 px-3 text-xs"
    >
      <FlaskConical class="text-warning size-3.5" />
      Demo Library. MQL5 titles and text from your local catalog; bots, models, apps
      and workflows are samples.
    </div>
  {/if}
  <PageHeader title="Library" subtitle="Everything QMX knows and has made">
    {#snippet actions()}
      <Tabs.Root bind:value={kind}>
        <Tabs.List>
          {#each KINDS as k (k.id)}<Tabs.Trigger value={k.id}
              ><k.icon />{k.label}</Tabs.Trigger
            >{/each}
        </Tabs.List>
      </Tabs.Root>
    {/snippet}
  </PageHeader>

  {#if !demo}
    <EmptyState
      class="flex-1"
      icon={BookOpen}
      title="Nothing here yet"
      description="Items appear here once QMX is connected to its daemon."
    />
  {:else if kind === "knowledge"}
    <Resizable.PaneGroup direction="horizontal" class="scrim min-h-0 flex-1">
      <Resizable.Pane defaultSize={16} minSize={12} maxSize={24}>
        <nav
          aria-label="Sections"
          class="bg-panel flex h-full flex-col gap-1 overflow-auto p-2"
        >
          <div class="relative mb-1">
            <Search
              class="text-muted-foreground pointer-events-none absolute top-1/2 left-2.5 size-3.5 -translate-y-1/2"
            />
            <Input
              bind:value={query}
              class="h-8 pl-8"
              placeholder="Search"
              aria-label="Search the Library"
            />
          </div>
          <button
            type="button"
            class={cn(
              "hover:bg-muted flex justify-between rounded-md px-2 py-1.5 text-sm",
              !section && "bg-muted font-medium",
            )}
            onclick={() => (section = null)}
          >
            All <span class="num text-muted-foreground text-xs"
              >{articles.length}</span
            >
          </button>
          {#each sections as [name, n] (name)}
            <button
              type="button"
              class={cn(
                "hover:bg-muted flex items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm",
                section === name && "bg-muted font-medium",
              )}
              onclick={() => (section = name)}
            >
              <span
                class="size-2 shrink-0 rounded-full"
                style="background: var({hueOf(name)})"
              ></span>
              <span class="min-w-0 flex-1 truncate">{name}</span>
              <span class="num text-muted-foreground text-xs">{n}</span>
            </button>
          {/each}
        </nav>
      </Resizable.Pane>
      <Resizable.Handle />
      <Resizable.Pane defaultSize={30} minSize={20}>
        <section aria-label="Articles" class="flex h-full flex-col">
          <p
            class="text-muted-foreground border-b px-3 py-2 text-xs"
            role="status"
          >
            {#if loadState === "loading"}Loading…{:else if loadState === "failed"}Could
              not load the demo catalog.{:else}{hits.length} articles{/if}
          </p>
          <ul class="min-h-0 flex-1 overflow-auto">
            {#each hits.slice(0, 200) as a (a.id)}
              <li>
                <button
                  type="button"
                  class={cn(
                    "hover:bg-muted/60 flex w-full gap-2.5 border-b px-3 py-2.5 text-left",
                    openId === a.id && "bg-muted",
                  )}
                  aria-current={openId === a.id ? "true" : undefined}
                  onclick={() => (openId = a.id)}
                >
                  <span
                    class="mt-1.5 h-8 w-1 shrink-0 rounded-full"
                    style="background: var({hueOf(a.section)})"
                  ></span>
                  <span class="min-w-0">
                    <span class="line-clamp-2 text-sm leading-snug font-medium"
                      >{a.title}</span
                    >
                    <span
                      class="text-muted-foreground mt-0.5 flex gap-2 text-xs"
                    >
                      <span class="num">{a.published}</span
                      >{a.section}{#if a.part}<span>· Part {a.part}</span>{/if}
                    </span>
                  </span>
                </button>
              </li>
            {/each}
          </ul>
        </section>
      </Resizable.Pane>
      <Resizable.Handle />
      <Resizable.Pane defaultSize={54} minSize={30}>
        {#if open}
          <article class="bg-panel flex h-full flex-col">
            <header class="flex flex-col gap-2 border-b px-6 py-4">
              <p class="panel-label">
                {open.section}{open.series ? ` · ${open.series}` : ""}
              </p>
              <h2 class="text-xl leading-snug font-semibold">{open.title}</h2>
              <div class="flex flex-wrap items-center gap-2">
                <span class="num text-muted-foreground mr-2 text-xs"
                  >{open.published}</span
                >
                <Button size="sm" onclick={() => workbench.addRef(open.title)}
                  ><MessageSquarePlus /> Add to copilot</Button
                >
                <Button
                  size="sm"
                  variant="outline"
                  aria-disabled="true"
                  class="aria-disabled:opacity-60"
                  title="Writes a Stage 0 hypothesis citing this article; needs the daemon"
                  onclick={(e) => e.preventDefault()}
                  ><Lightbulb /> Turn into hypothesis</Button
                >
                <Button
                  size="sm"
                  variant="ghost"
                  href={resolve("/library/article/[id]", {
                    id: String(open.id),
                  })}><Maximize2 /> Full page</Button
                >
                <Button
                  size="sm"
                  variant="ghost"
                  href={open.url}
                  target="_blank"
                  rel="noopener noreferrer"><ExternalLink /> Original</Button
                >
              </div>
            </header>
            <div class="min-h-0 flex-1 overflow-auto px-6 py-5">
              <section class="well mb-5 rounded-lg p-3.5">
                <p class="panel-label mb-1 flex items-center gap-1.5">
                  <Sparkles class="size-3.5" /> Key points
                </p>
                <p class="text-muted-foreground text-sm">{open.summary}</p>
                <p class="text-muted-foreground mt-1 text-xs">
                  A generated summary and testable claims come from a small
                  model on the daemon. Shown here: the article's opening.
                </p>
              </section>
              {#if text === null}
                <div class="flex flex-col gap-2">
                  <Skeleton class="h-4 w-full" /><Skeleton
                    class="h-4 w-11/12"
                  /><Skeleton class="h-32 w-full" />
                </div>
              {:else if text.status === "no-text"}
                <p class="text-muted-foreground text-sm">
                  Full text comes from the daemon's Library. For this demo,
                  start the preview with QMX_DEMO_MQL5_DIR set.
                </p>
              {:else}
                {#if text.figures.length}
                  <div
                    class="mb-5 flex gap-2 overflow-x-auto pb-1"
                    aria-label="Figures"
                  >
                    {#each text.figures as src (src)}<img
                        {src}
                        alt=""
                        loading="lazy"
                        class="h-20 shrink-0 rounded-md bg-white object-contain"
                      />{/each}
                  </div>
                {/if}
                <!-- Sanitised with DOMPurify in loadArticleText. -->
                <!-- eslint-disable-next-line svelte/no-at-html-tags -->
                <div class="prose-qmx max-w-3xl">{@html text.html}</div>
              {/if}
            </div>
          </article>
        {:else}
          <EmptyState
            class="bg-panel h-full"
            icon={BookOpen}
            title="Select an article"
          />
        {/if}
      </Resizable.Pane>
    </Resizable.PaneGroup>
  {:else if kind === "sources"}
    <Resizable.PaneGroup direction="horizontal" class="scrim min-h-0 flex-1">
      <Resizable.Pane defaultSize={20} minSize={14} maxSize={30}>
        <nav
          aria-label="Sources"
          class="bg-panel flex h-full flex-col gap-1 overflow-auto p-2"
        >
          {#each SOURCES as s (s.id)}
            <button
              type="button"
              class={cn(
                "hover:bg-muted flex flex-col rounded-md px-2.5 py-2 text-left",
                sourceId === s.id && "bg-muted",
              )}
              onclick={() => (sourceId = s.id)}
            >
              <span class="flex items-center gap-2 text-sm font-medium"
                >{s.name}<span
                  class="bg-background/50 ml-auto rounded-sm px-1.5 text-[10px]"
                  >{s.kind}</span
                ></span
              >
              <span class="text-muted-foreground text-xs">{s.how}</span>
              <span
                class={cn(
                  "text-[11px]",
                  s.status === "ruled"
                    ? "text-success"
                    : "text-muted-foreground",
                )}
                >{s.status === "ruled"
                  ? "Ruled source"
                  : "Proposed · needs backend"}</span
              >
            </button>
          {/each}
        </nav>
      </Resizable.Pane>
      <Resizable.Handle />
      <Resizable.Pane defaultSize={26} minSize={18}>
        <section aria-label="Latest" class="flex h-full flex-col">
          <p class="text-muted-foreground border-b px-3 py-2 text-xs">
            Latest from your sources · sample items
          </p>
          <ul class="min-h-0 flex-1 overflow-auto">
            {#each FEED as f (f.id)}
              <li class="flex items-start gap-2 border-b px-3 py-2.5">
                <span class="min-w-0 flex-1">
                  <span class="text-muted-foreground block text-xs"
                    >{f.source} · {f.age}</span
                  >
                  <span class="block text-sm font-medium">{f.title}</span>
                </span>
                <Button
                  size="icon-sm"
                  variant="ghost"
                  aria-label="Add to copilot"
                  onclick={() => workbench.addRef(f.title)}
                  ><MessageSquarePlus /></Button
                >
              </li>
            {/each}
          </ul>
        </section>
      </Resizable.Pane>
      <Resizable.Handle />
      <Resizable.Pane defaultSize={54} minSize={30}>
        <section aria-label="Browser" class="bg-panel flex h-full flex-col">
          <div class="flex items-center gap-2 border-b px-2 py-1.5">
            <Button
              size="icon-sm"
              variant="ghost"
              aria-label="Reload"
              onclick={() => frameKey++}><RotateCw /></Button
            >
            <div
              class="well flex-1 truncate rounded-md px-3 py-1 font-mono text-xs"
            >
              {source.url}
            </div>
            <Button
              size="sm"
              variant="ghost"
              href={source.url}
              target="_blank"
              rel="noopener noreferrer"><ExternalLink /> Outside QMX</Button
            >
          </div>
          {#key frameKey + sourceId}
            <iframe
              title={source.name}
              src={source.url}
              class="bg-background min-h-0 w-full flex-1"
              sandbox="allow-scripts allow-same-origin allow-popups allow-forms"
              referrerpolicy="no-referrer"
            ></iframe>
          {/key}
          <p class="text-muted-foreground border-t px-3 py-1.5 text-xs">
            If the page stays blank, the site refuses to be embedded; the
            desktop app shows it in its own browser pane.
          </p>
        </section>
      </Resizable.Pane>
    </Resizable.PaneGroup>
  {:else if kind === "files"}
    <div class="scrim min-h-0 flex-1 overflow-auto p-4">
      <div class="surface overflow-hidden rounded-lg">
        <table class="w-full text-sm">
          <thead class="text-muted-foreground text-left text-xs">
            <tr
              ><th class="px-4 py-2.5 font-medium">Artifact</th><th
                class="font-medium">Type</th
              ><th class="font-medium">Produced by</th><th class="font-medium"
                >Fingerprint</th
              ><th class="px-4 text-right font-medium">Size</th></tr
            >
          </thead>
          <tbody>
            {#each DEMO_ARTIFACTS.filter((a) => !q || a.name
                  .toLowerCase()
                  .includes(q)) as a (a.id)}
              <tr class="hover:bg-muted/50 border-t">
                <td class="px-4 py-3"
                  ><span class="block font-medium">{a.name}</span><span
                    class="text-muted-foreground text-xs">{a.date}</span
                  ></td
                >
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
    </div>
  {:else}
    <div class="scrim min-h-0 flex-1 overflow-auto p-4">
      <div class="relative mb-3 max-w-xl">
        <Search
          class="text-muted-foreground pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2"
        />
        <Input
          bind:value={query}
          class="h-9 pl-9"
          placeholder="Search names and roles"
          aria-label="Search the Library"
        />
      </div>
      <ul
        class="grid gap-3 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4"
        aria-label="Items"
      >
        {#each entities as a (a.id)}
          <li>
            <EntityCard
              entity={a}
              href={resolve("/library/[id]", { id: a.id })}
            />
          </li>
        {/each}
      </ul>
    </div>
  {/if}
</div>
