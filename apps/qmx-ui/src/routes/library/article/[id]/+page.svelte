<script lang="ts">
  import { onMount } from "svelte";
  import { resolve } from "$app/paths";
  import { marked } from "marked";
  import DOMPurify from "dompurify";
  import ArrowLeft from "@lucide/svelte/icons/arrow-left";
  import ExternalLink from "@lucide/svelte/icons/external-link";
  import MessageSquarePlus from "@lucide/svelte/icons/message-square-plus";
  import Lightbulb from "@lucide/svelte/icons/lightbulb";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import FlaskConical from "@lucide/svelte/icons/flask-conical";
  import { Button } from "$lib/components/ui/button";
  import { Skeleton } from "$lib/components/ui/skeleton";
  import { workbench } from "$lib/workbench/workbench.svelte";

  let { data } = $props();

  type Meta = {
    id: number;
    title: string;
    published: string;
    section: string;
    series: string | null;
    url: string;
  };
  let meta = $state<Meta | null>(null);
  let html = $state("");
  let toc = $state<{ id: string; text: string; level: number }[]>([]);
  let figures = $state<string[]>([]);
  let status = $state<"loading" | "ready" | "no-text" | "missing">("loading");

  /** Drop front matter and the scraped page chrome above the first real section. */
  function clean(md: string): string {
    let body = md.replace(/\r\n?/g, "\n").replace(/^---\n[\s\S]*?\n---\n/, "");
    // Everything before the first section heading is scraped page chrome
    // (title, views, author, contents list).
    const first = body.search(/^#{2,3} (?!Contents\b)/m);
    if (first >= 0) body = body.slice(first);
    return body;
  }

  onMount(async () => {
    try {
      const idx = await fetch(resolve("/demo/mql5-articles.json" as "/")).then(
        (r) => r.json(),
      );
      meta = idx.articles.find((a: Meta) => String(a.id) === data.id) ?? null;
    } catch {
      meta = null;
    }
    if (!meta) {
      status = "missing";
      return;
    }
    const res = await fetch(
      `/__demo/mql5/${encodeURIComponent(data.id)}`,
    ).catch(() => null);
    if (!res?.ok) {
      status = "no-text";
      return;
    }
    const raw = await marked.parse(clean(await res.text()), { gfm: true });
    // Scraped content: sanitise, open links outside, collect headings and figures.
    const doc = new DOMParser().parseFromString(
      DOMPurify.sanitize(raw, { FORBID_TAGS: ["style", "form", "iframe"] }),
      "text/html",
    );
    const headings: typeof toc = [];
    doc.querySelectorAll("h2, h3").forEach((h, i) => {
      if (!h.textContent?.trim()) {
        h.remove();
        return;
      }
      h.id = `s-${i}`;
      headings.push({
        id: h.id,
        text: h.textContent ?? "",
        level: h.tagName === "H2" ? 2 : 3,
      });
    });
    doc.querySelectorAll("a").forEach((a) => {
      a.setAttribute("target", "_blank");
      a.setAttribute("rel", "noopener noreferrer");
    });
    doc.querySelectorAll("img").forEach((img) => {
      img.setAttribute("loading", "lazy");
      const src = img.getAttribute("src");
      if (src && !src.endsWith(".svg") && !src.includes("icons"))
        figures.push(src);
    });
    toc = headings;
    figures = figures.slice(0, 12);
    html = doc.body.innerHTML;
    status = "ready";
  });
</script>

<svelte:head
  ><title>{meta?.title ?? "Article"} · Library · QMX</title></svelte:head
>

<div class="h-full overflow-auto">
  <div class="bg-warning/15 flex h-7 items-center gap-2 px-3 text-xs">
    <FlaskConical class="text-warning size-3.5" />
    Demo reader. Full text comes from your local MQL5 catalog through the dev server;
    the daemon's Library replaces this.
  </div>
  <div
    class="mx-auto grid max-w-7xl gap-8 px-6 py-6 lg:grid-cols-[14rem_minmax(0,1fr)_16rem]"
  >
    <nav aria-label="Contents" class="hidden lg:block">
      <div class="sticky top-4 flex flex-col gap-1">
        <a
          href={resolve("/library")}
          class="text-muted-foreground hover:text-foreground mb-3 flex items-center gap-1 text-sm"
        >
          <ArrowLeft class="size-4" /> Library
        </a>
        {#if toc.length}
          <p class="panel-label mb-1">Contents</p>
          {#each toc as h (h.id)}
            <a
              href="#{h.id}"
              class="text-muted-foreground hover:text-foreground truncate text-sm {h.level ===
              3
                ? 'pl-3'
                : ''}">{h.text}</a
            >
          {/each}
        {/if}
      </div>
    </nav>

    <article class="surface min-w-0 rounded-2xl p-6 md:p-10">
      {#if meta}
        <p class="panel-label">
          {meta.section}{meta.series ? ` · ${meta.series}` : ""}
        </p>
        <h1 class="mt-1 text-3xl leading-tight font-semibold tracking-tight">
          {meta.title}
        </h1>
        <p class="text-muted-foreground mt-2 text-sm">
          {meta.published} · MQL5 article
        </p>
      {/if}
      <div class="mt-6">
        {#if status === "loading"}
          <div class="flex flex-col gap-3">
            <Skeleton class="h-4 w-full" /><Skeleton
              class="h-4 w-11/12"
            /><Skeleton class="h-4 w-4/5" /><Skeleton class="h-40 w-full" />
          </div>
        {:else if status === "missing"}
          <p class="text-muted-foreground">
            This article is not in the Library.
          </p>
        {:else if status === "no-text"}
          <div class="surface rounded-xl p-5">
            <p class="font-medium">Full text not available here</p>
            <p class="text-muted-foreground mt-1 text-sm">
              The daemon's Library serves article text. For this demo, start the
              preview with QMX_DEMO_MQL5_DIR pointing at your local catalog.
            </p>
          </div>
        {:else}
          <!-- Sanitised with DOMPurify above. -->
          <!-- eslint-disable-next-line svelte/no-at-html-tags -->
          <div class="prose-qmx">{@html html}</div>
        {/if}
      </div>
    </article>

    <aside class="flex flex-col gap-4">
      <div class="sticky top-4 flex flex-col gap-4">
        {#if meta}
          <div class="flex flex-col gap-2">
            <Button onclick={() => workbench.addRef(meta!.title)}
              ><MessageSquarePlus /> Add to copilot</Button
            >
            <Button
              variant="outline"
              aria-disabled="true"
              class="aria-disabled:opacity-60"
              title="Writes a Stage 0 hypothesis citing this article; needs the daemon"
              onclick={(e) => e.preventDefault()}
            >
              <Lightbulb /> Turn into hypothesis
            </Button>
            <Button
              variant="outline"
              href={meta.url}
              target="_blank"
              rel="noopener noreferrer"><ExternalLink /> Open original</Button
            >
          </div>
        {/if}
        <section class="surface rounded-xl p-4">
          <p class="panel-label mb-1.5 flex items-center gap-1.5">
            <Sparkles class="size-3.5" /> Key points
          </p>
          <p class="text-muted-foreground text-sm">
            A short summary and the article's testable claims, written by a
            small model on the daemon. Not connected.
          </p>
        </section>
        {#if figures.length}
          <section class="surface rounded-xl p-4">
            <p class="panel-label mb-2">Figures · {figures.length}</p>
            <div class="grid grid-cols-2 gap-2">
              {#each figures as src (src)}
                <img
                  {src}
                  alt=""
                  loading="lazy"
                  class="aspect-video w-full rounded-md bg-white object-contain"
                />
              {/each}
            </div>
          </section>
        {/if}
      </div>
    </aside>
  </div>
</div>
