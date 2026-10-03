<script lang="ts">
  /**
   * The Library (redesign, operator 2026-10-03: "needs a bloody redesign …
   * needs to connect to all the other parts"). One store room every screen
   * reads from and saves to. Shelves on the left (things that trade, things
   * that run, proof, inputs, knowledge), the shelf in the middle as cards or
   * a list, and the selected item on the right with where it is used across
   * QMX. Articles keep the reader; sources keep the in-app browser.
   * Deep links: ?shelf=<id>&item=<id>; old ?tab= links still land.
   */
  import { onMount } from "svelte";
  import { resolve } from "$app/paths";
  import { page } from "$app/state";
  import Search from "@lucide/svelte/icons/search";
  import BookOpen from "@lucide/svelte/icons/book-open";
  import Plus from "@lucide/svelte/icons/plus";
  import LayoutGrid from "@lucide/svelte/icons/layout-grid";
  import Rows3 from "@lucide/svelte/icons/rows-3";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import Upload from "@lucide/svelte/icons/upload";
  import LayoutTemplate from "@lucide/svelte/icons/layout-template";
  import Library from "@lucide/svelte/icons/library-big";
  import ExternalLink from "@lucide/svelte/icons/external-link";
  import Maximize2 from "@lucide/svelte/icons/maximize-2";
  import MessageSquarePlus from "@lucide/svelte/icons/message-square-plus";
  import Lightbulb from "@lucide/svelte/icons/lightbulb";
  import RotateCw from "@lucide/svelte/icons/rotate-cw";
  import AppWindow from "@lucide/svelte/icons/app-window";
  import FlaskConical from "@lucide/svelte/icons/flask-conical";
  import * as Resizable from "$lib/components/ui/resizable";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu";
  import { Input } from "$lib/components/ui/input";
  import { Button } from "$lib/components/ui/button";
  import { Skeleton } from "$lib/components/ui/skeleton";
  import EmptyState from "$lib/workbench/EmptyState.svelte";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import EntityCard from "$lib/qmx/EntityCard.svelte";
  import { loadArticleText, type ArticleText } from "$lib/qmx/article";
  import { FEED } from "$lib/demo/feeds";
  import { cn } from "$lib/utils";
  import {
    LIBRARY,
    SHELF_GROUPS,
    familyColor,
    itemById,
    shelfById,
    type LibraryItem,
  } from "$lib/library/items";
  import ItemCard from "$lib/library/ItemCard.svelte";
  import ItemInspector from "$lib/library/ItemInspector.svelte";

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

  // Old tab ids from before the redesign.
  const OLD_TAB: Record<string, string> = {
    knowledge: "articles",
    sources: "sources",
    files: "files",
    artifact: "bots",
    contribution: "apps",
  };
  const params = page.url.searchParams;
  const asked =
    params.get("shelf") ?? OLD_TAB[params.get("tab") ?? ""] ?? "everything";
  let shelf = $state<string>(
    asked === "everything" || shelfById(asked) ? asked : "everything",
  );
  const askedItem = params.get("item");
  let selectedId = $state<string | null>(askedItem);
  if (askedItem && itemById(askedItem) && !params.get("shelf"))
    shelf = itemById(askedItem)!.shelf;

  let view = $state<"cards" | "list">("cards");
  try {
    if (localStorage.getItem("qmx.library.view") === "list") view = "list";
  } catch {
    /* storage unavailable */
  }
  function setView(v: "cards" | "list") {
    view = v;
    try {
      localStorage.setItem("qmx.library.view", v);
    } catch {
      /* storage unavailable */
    }
  }

  const VIEWS = [
    ["cards", LayoutGrid, "Cards"],
    ["list", Rows3, "List"],
  ] as const;

  const demo = workbench.demoMode;
  let query = $state("");
  const q = $derived(query.trim().toLowerCase());
  const match = (i: LibraryItem) =>
    !q ||
    i.name.toLowerCase().includes(q) ||
    i.summary.toLowerCase().includes(q) ||
    (i.family ?? "").toLowerCase().includes(q);

  const mode = $derived(
    shelf === "articles"
      ? "articles"
      : shelf === "sources"
        ? "sources"
        : "items",
  );
  const items = $derived(
    LIBRARY.filter(
      (i) =>
        (shelf === "everything" || i.shelf === shelf) &&
        i.shelf !== "sources" &&
        match(i),
    ),
  );
  const grouped = $derived(
    SHELF_GROUPS.flatMap((g) => g.shelves)
      .map((s) => ({ s, list: items.filter((i) => i.shelf === s.id) }))
      .filter((x) => x.list.length),
  );
  const selected = $derived(
    selectedId ? itemById(selectedId) : (items[0] ?? null),
  );
  const countOf = (id: string) => LIBRARY.filter((i) => i.shelf === id).length;

  // Articles: the reader, as before but wider, with a side column.
  let articles = $state.raw<Article[]>([]);
  let loadState = $state<"idle" | "loading" | "ready" | "failed">("idle");
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
  $effect(() => {
    const id = openId;
    if (id === null || id === textFor) return;
    textFor = id;
    text = null;
    loadArticleText(id).then((t) => {
      if (textFor === id) text = t;
    });
  });
  const sections = $derived.by(() => {
    const counts: Record<string, number> = {};
    for (const a of articles) counts[a.section] = (counts[a.section] ?? 0) + 1;
    return Object.entries(counts).sort((a, b) => b[1] - a[1]);
  });
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

  // Sources: open inside QMX.
  const sources = $derived(
    LIBRARY.filter((i) => i.shelf === "sources" && match(i)),
  );
  let sourceId = $state("src-arxiv");
  const source = $derived(itemById(sourceId));
  const sourceUrl = $derived(
    source?.details?.find(([k]) => k === "Address")?.[1] ?? "",
  );
  let frameKey = $state(0);

  function pick(id: string) {
    shelf = id;
    selectedId = null;
  }
</script>

{#snippet itemList(list: LibraryItem[])}
  {#if view === "cards"}
    <ul
      class="grid gap-2.5"
      style="grid-template-columns: repeat(auto-fill, minmax(13rem, 1fr))"
    >
      {#each list as i (i.id)}
        <li>
          {#if i.entity}
            <div
              role="button"
              tabindex="0"
              class={cn(
                "h-full rounded-xl",
                selected?.id === i.id && "ring-primary ring-2",
              )}
              aria-pressed={selected?.id === i.id}
              onclick={() => (selectedId = i.id)}
              onkeydown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  selectedId = i.id;
                }
              }}
            >
              <EntityCard entity={i.entity} compact tint={familyColor(i)} />
            </div>
          {:else}
            <ItemCard
              item={i}
              selected={selected?.id === i.id}
              onselect={() => (selectedId = i.id)}
            />
          {/if}
        </li>
      {/each}
    </ul>
  {:else}
    <ul class="flex flex-col">
      {#each list as i (i.id)}
        {@const s = shelfById(i.shelf)!}
        <li>
          <button
            type="button"
            class={cn(
              "hover:bg-muted/60 flex w-full items-center gap-3 border-b px-2 py-2 text-left",
              selected?.id === i.id && "bg-muted",
            )}
            aria-pressed={selected?.id === i.id}
            onclick={() => (selectedId = i.id)}
          >
            <span
              class="h-7 w-1 shrink-0 rounded-full"
              style="background:{familyColor(i)}"
            ></span>
            <s.icon class="text-muted-foreground size-4 shrink-0" />
            <span class="min-w-0 flex-1">
              <span class="block truncate text-sm font-medium"
                >{i.name}{#if i.version}<span
                    class="text-muted-foreground ml-1.5 font-normal"
                    >{i.version}</span
                  >{/if}</span
              >
              <span class="text-muted-foreground block truncate text-xs"
                >{i.family ?? s.label} · {i.summary}</span
              >
            </span>
            {#if i.stage}<span
                class="text-muted-foreground hidden shrink-0 rounded border px-1.5 text-[11px] @[34rem]:inline"
                >{i.stage}</span
              >{/if}
            <span
              class="text-muted-foreground num hidden w-32 shrink-0 truncate text-right text-xs @[28rem]:inline"
              >{i.starts
                ? "Template"
                : [...new Set(i.uses.map((u) => u.place))].join(", ") ||
                  "Not used"}</span
            >
          </button>
        </li>
      {/each}
    </ul>
  {/if}
{/snippet}

<div class="flex h-full flex-col">
  {#if demo}
    <div
      class="bg-warning/15 flex h-7 shrink-0 items-center gap-2 px-3 text-xs"
    >
      <FlaskConical class="text-warning size-3.5" />
      Demo Library. Items are the samples from the Lab, Portfolio and Copilot, so
      every "used in" link opens the real screen; MQL5 text comes from your local
      catalog.
    </div>
  {/if}
  <header class="flex h-12 shrink-0 items-center gap-3 border-b px-3">
    <h1 class="flex items-center gap-2 text-base font-semibold">
      <Library class="size-4" />Library
    </h1>
    <div class="relative w-full max-w-md">
      <Search
        class="text-muted-foreground pointer-events-none absolute top-1/2 left-2.5 size-3.5 -translate-y-1/2"
      />
      <Input
        bind:value={query}
        class="h-8 pl-8"
        placeholder="Find anything: a bot, a pod, a report, an article…"
        aria-label="Search the Library"
      />
    </div>
    <div class="ml-auto flex items-center gap-1.5">
      {#if mode === "items"}
        <div
          class="bg-muted flex rounded-md p-0.5"
          role="radiogroup"
          aria-label="View"
        >
          {#each VIEWS as [v, Icon, label] (v)}
            <button
              type="button"
              role="radio"
              aria-checked={view === v}
              aria-label={label}
              title={label}
              class={cn(
                "flex h-7 w-8 items-center justify-center rounded",
                view === v
                  ? "bg-background text-foreground shadow-sm"
                  : "text-muted-foreground",
              )}
              onclick={() => setView(v)}><Icon class="size-4" /></button
            >
          {/each}
        </div>
      {/if}
      <DropdownMenu.Root>
        <DropdownMenu.Trigger>
          {#snippet child({ props })}
            <Button {...props} size="sm"><Plus />New</Button>
          {/snippet}
        </DropdownMenu.Trigger>
        <DropdownMenu.Content align="end" class="w-64">
          <DropdownMenu.Item onclick={() => pick("templates")}
            ><LayoutTemplate />Start from a template</DropdownMenu.Item
          >
          <DropdownMenu.Item
            onclick={() =>
              workbench.notify(
                "Importing goes through the daemon: drop a file, QMX fingerprints it and files it on the right shelf.",
              )}><Upload />Import a file</DropdownMenu.Item
          >
          <DropdownMenu.Item
            onclick={() =>
              workbench.notify(
                "Ask the copilot to make anything (a bot, a pod, a scenario, a mini app); what it makes is saved here.",
              )}><Sparkles />Ask the copilot</DropdownMenu.Item
          >
        </DropdownMenu.Content>
      </DropdownMenu.Root>
    </div>
  </header>

  {#if !demo}
    <EmptyState
      class="flex-1"
      icon={BookOpen}
      title="Nothing here yet"
      description="Items appear here once QMX is connected to its daemon."
    />
  {:else}
    {#key mode}
      <Resizable.PaneGroup direction="horizontal" class="scrim min-h-0 flex-1">
        <Resizable.Pane defaultSize={15} minSize={11} maxSize={24}>
          <nav
            aria-label="Shelves"
            class="bg-panel flex h-full flex-col gap-3 overflow-auto p-2"
          >
            <button
              type="button"
              class={cn(
                "hover:bg-muted flex items-center justify-between rounded-md px-2 py-1.5 text-sm",
                shelf === "everything" && "bg-muted font-medium",
              )}
              onclick={() => pick("everything")}
              >Everything<span class="num text-muted-foreground text-xs"
                >{LIBRARY.filter((i) => i.shelf !== "sources").length}</span
              ></button
            >
            {#each SHELF_GROUPS as g (g.label)}
              <div>
                <p class="text-muted-foreground mb-1 px-2 text-xs">{g.label}</p>
                {#each g.shelves as s (s.id)}
                  <button
                    type="button"
                    class={cn(
                      "hover:bg-muted flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm",
                      shelf === s.id && "bg-muted font-medium",
                    )}
                    title={s.note}
                    aria-current={shelf === s.id ? "true" : undefined}
                    onclick={() => pick(s.id)}
                  >
                    <s.icon class="text-muted-foreground size-4 shrink-0" />
                    <span class="min-w-0 flex-1 truncate">{s.label}</span>
                    <span class="num text-muted-foreground text-xs"
                      >{s.id === "articles"
                        ? articles.length || ""
                        : countOf(s.id)}</span
                    >
                  </button>
                {/each}
              </div>
            {/each}
          </nav>
        </Resizable.Pane>
        <Resizable.Handle />

        {#if mode === "items"}
          <Resizable.Pane defaultSize={47} minSize={28}>
            <section aria-label="Items" class="@container flex h-full flex-col">
              <p
                class="text-muted-foreground flex h-9 shrink-0 items-center border-b px-3 text-xs"
              >
                {shelf === "everything"
                  ? `${items.length} items on every shelf`
                  : `${items.length} · ${shelfById(shelf)?.note}`}
              </p>
              <div class="min-h-0 flex-1 overflow-auto p-3">
                {#if !items.length}
                  <EmptyState
                    icon={Search}
                    title="Nothing matches"
                    description="Try another word, or look on Everything."
                  />
                {:else if shelf === "everything"}
                  {#each grouped as { s, list } (s.id)}
                    <h2
                      class="text-muted-foreground mt-1 mb-2 flex items-center gap-1.5 text-xs font-medium"
                    >
                      <s.icon class="size-3.5" />{s.label}
                      <button
                        type="button"
                        class="text-primary ml-auto font-normal"
                        onclick={() => pick(s.id)}>Open shelf</button
                      >
                    </h2>
                    <div class="mb-4">
                      {@render itemList(
                        list.slice(0, view === "cards" ? 4 : 6),
                      )}
                    </div>
                  {/each}
                {:else}
                  {@render itemList(items)}
                {/if}
              </div>
            </section>
          </Resizable.Pane>
          <Resizable.Handle />
          <Resizable.Pane defaultSize={38} minSize={26}>
            <aside class="bg-panel h-full" aria-label="Selected item">
              {#if selected}
                <ItemInspector item={selected} />
              {:else}
                <EmptyState
                  class="h-full"
                  icon={Library}
                  title="Pick something"
                  description="Its settings and everywhere it is used show here."
                />
              {/if}
            </aside>
          </Resizable.Pane>
        {:else if mode === "articles"}
          <Resizable.Pane defaultSize={26} minSize={18}>
            <section aria-label="Articles" class="flex h-full flex-col">
              <div class="flex h-9 shrink-0 items-center gap-2 border-b px-3">
                <select
                  class="h-7 max-w-full min-w-0 flex-1 rounded-md border px-2 text-xs"
                  aria-label="Section"
                  value={section ?? ""}
                  onchange={(e) =>
                    (section = (e.target as HTMLSelectElement).value || null)}
                >
                  <option value="">All sections ({articles.length})</option>
                  {#each sections as [name, n] (name)}<option value={name}
                      >{name} ({n})</option
                    >{/each}
                </select>
                <span
                  class="text-muted-foreground num shrink-0 text-xs"
                  role="status"
                  >{#if loadState === "loading"}Loading…{:else if loadState === "failed"}Failed{:else}{hits.length}{/if}</span
                >
              </div>
              <ul class="min-h-0 flex-1 overflow-auto">
                {#each hits.slice(0, 200) as a (a.id)}
                  <li>
                    <button
                      type="button"
                      class={cn(
                        "hover:bg-muted/60 flex w-full flex-col border-b px-3 py-2.5 text-left",
                        openId === a.id && "bg-muted",
                      )}
                      aria-current={openId === a.id ? "true" : undefined}
                      onclick={() => (openId = a.id)}
                    >
                      <span
                        class="line-clamp-2 text-sm leading-snug font-medium"
                        >{a.title}</span
                      >
                      <span class="text-muted-foreground mt-0.5 text-xs"
                        ><span class="num">{a.published}</span> · {a.section}{#if a.part}
                          · Part {a.part}{/if}</span
                      >
                    </button>
                  </li>
                {/each}
              </ul>
            </section>
          </Resizable.Pane>
          <Resizable.Handle />
          <Resizable.Pane defaultSize={59} minSize={34}>
            {#if open}
              <article class="bg-panel @container flex h-full flex-col">
                <header class="flex flex-col gap-2 border-b px-6 py-4">
                  <p class="text-muted-foreground text-xs">
                    {open.section}{open.series ? ` · ${open.series}` : ""} ·
                    <span class="num">{open.published}</span>
                  </p>
                  <h2 class="text-xl leading-snug font-semibold">
                    {open.title}
                  </h2>
                  <div class="flex flex-wrap items-center gap-2">
                    <Button
                      size="sm"
                      onclick={() => workbench.addRef(open.title)}
                      ><MessageSquarePlus /> Add to copilot</Button
                    >
                    <Button
                      size="sm"
                      variant="outline"
                      onclick={() =>
                        workbench.notify(
                          "The Article to hypothesis workflow pulls testable claims and drafts a hypothesis citing this article. Needs the daemon.",
                        )}><Lightbulb /> Turn into hypothesis</Button
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
                      rel="noopener noreferrer"
                      ><ExternalLink /> Original</Button
                    >
                  </div>
                </header>
                <div
                  class="grid min-h-0 flex-1 grid-cols-1 overflow-auto @[56rem]:grid-cols-[minmax(0,1fr)_17rem]"
                >
                  <div class="min-w-0 px-6 py-5">
                    {#if text === null}
                      <div class="flex flex-col gap-2">
                        <Skeleton class="h-4 w-full" /><Skeleton
                          class="h-4 w-11/12"
                        /><Skeleton class="h-32 w-full" />
                      </div>
                    {:else if text.status === "no-text"}
                      <p class="text-muted-foreground text-sm">
                        Full text comes from the daemon's Library. For this
                        demo, start the preview with QMX_DEMO_MQL5_DIR set.
                      </p>
                    {:else}
                      <!-- Sanitised with DOMPurify in loadArticleText. -->
                      <div class="prose-qmx max-w-[78ch]">
                        <!-- eslint-disable-next-line svelte/no-at-html-tags -->
                        {@html text.html}
                      </div>
                    {/if}
                  </div>
                  <aside
                    class="flex flex-col gap-4 border-t px-5 py-5 @[56rem]:border-t-0 @[56rem]:border-l"
                  >
                    <section>
                      <h3
                        class="mb-1 flex items-center gap-1.5 text-sm font-medium"
                      >
                        <Sparkles class="size-3.5" /> Key points
                      </h3>
                      <p class="text-muted-foreground text-sm">
                        {open.summary}
                      </p>
                      <p class="text-muted-foreground mt-1 text-xs">
                        A small model on the daemon writes real key points and
                        testable claims. Shown: the article's opening.
                      </p>
                    </section>
                    {#if text && text.status !== "no-text" && text.figures.length}
                      <section>
                        <h3 class="mb-1 text-sm font-medium">Figures</h3>
                        <div class="grid grid-cols-2 gap-1.5">
                          {#each text.figures.slice(0, 6) as src (src)}<img
                              {src}
                              alt=""
                              loading="lazy"
                              class="h-20 w-full rounded-md bg-white object-contain"
                            />{/each}
                        </div>
                      </section>
                    {/if}
                    <section>
                      <h3 class="mb-1 text-sm font-medium">Use it</h3>
                      <ul
                        class="text-muted-foreground flex flex-col gap-1 text-sm"
                      >
                        <li>
                          Turn it into a hypothesis, then test it in the Lab.
                        </li>
                        <li>Add it to the copilot to ask about it.</li>
                        <li>
                          Diagrams of the method: planned (a cheap model draws
                          them).
                        </li>
                      </ul>
                    </section>
                  </aside>
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
        {:else}
          <Resizable.Pane defaultSize={27} minSize={18}>
            <section aria-label="Sources" class="flex h-full flex-col">
              <ul class="shrink-0 border-b p-1.5">
                {#each sources as s (s.id)}
                  <li>
                    <button
                      type="button"
                      class={cn(
                        "hover:bg-muted flex w-full flex-col rounded-md px-2.5 py-2 text-left",
                        sourceId === s.id && "bg-muted",
                      )}
                      onclick={() => (sourceId = s.id)}
                    >
                      <span class="flex items-center gap-2 text-sm font-medium"
                        >{s.name}<span
                          class="bg-background/50 ml-auto rounded-sm px-1.5 text-[10px]"
                          >{s.family}</span
                        ></span
                      >
                      <span class="text-muted-foreground text-xs"
                        >{s.summary}</span
                      >
                    </button>
                  </li>
                {/each}
              </ul>
              <p class="text-muted-foreground px-3 pt-2 text-xs">
                Latest from your sources · sample items
              </p>
              <ul class="min-h-0 flex-1 overflow-auto">
                {#each FEED as f (f.id)}
                  <li class="flex items-start gap-2 border-b px-3 py-2">
                    <span class="min-w-0 flex-1">
                      <span class="text-muted-foreground block text-xs"
                        >{f.source} · {f.age}</span
                      >
                      <span class="block text-sm">{f.title}</span>
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
              <div class="border-t p-2">
                <Button
                  size="sm"
                  variant="outline"
                  class="w-full"
                  onclick={() =>
                    workbench.notify(
                      "Add a feed, a site or a video channel; the daemon fetches it and files new items here.",
                    )}><Plus />Add a source</Button
                >
              </div>
            </section>
          </Resizable.Pane>
          <Resizable.Handle />
          <Resizable.Pane defaultSize={58} minSize={30}>
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
                  {sourceUrl}
                </div>
                <Button
                  size="sm"
                  variant="ghost"
                  onclick={() =>
                    workbench.notify(
                      `${source?.name} becomes a web app on the rail, in its own window with QMX's look (needs the desktop app).`,
                    )}><AppWindow /> Make it an app</Button
                >
                <Button
                  size="sm"
                  variant="ghost"
                  href={sourceUrl}
                  target="_blank"
                  rel="noopener noreferrer"><ExternalLink /> Outside QMX</Button
                >
              </div>
              {#key frameKey + sourceId}
                <iframe
                  title={source?.name}
                  src={sourceUrl}
                  class="bg-background min-h-0 w-full flex-1"
                  sandbox="allow-scripts allow-same-origin allow-popups allow-forms"
                  referrerpolicy="no-referrer"
                ></iframe>
              {/key}
              <p class="text-muted-foreground border-t px-3 py-1.5 text-xs">
                Some sites refuse to be shown inside other apps and stay blank
                here. For those, the daemon fetches a clean reader copy instead
                (planned).
              </p>
            </section>
          </Resizable.Pane>
        {/if}
      </Resizable.PaneGroup>
    {/key}
  {/if}
</div>
