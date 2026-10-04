<script lang="ts">
  /**
   * An errand's conversation, read like letters (Copilot redesign,
   * 2026-10-04: "bigger, less compact, with intention"). Your message, then
   * the copilot's reply in plain prose. Everything it did to get there
   * (helpers, tools, changes, reports) folds into one receipt line under
   * the reply; open it to see the detail. Questions, approvals and panels
   * it built stay in the letter because they need you.
   */
  import Check from "@lucide/svelte/icons/check";
  import ChevronDown from "@lucide/svelte/icons/chevron-down";
  import ArrowUpRight from "@lucide/svelte/icons/arrow-up-right";
  import FileText from "@lucide/svelte/icons/file-text";
  import CircleHelp from "@lucide/svelte/icons/circle-help";
  import ShieldCheck from "@lucide/svelte/icons/shield-check";
  import Paperclip from "@lucide/svelte/icons/paperclip";
  import Shuffle from "@lucide/svelte/icons/shuffle";
  import Pin from "@lucide/svelte/icons/pin";
  import Copy from "@lucide/svelte/icons/copy";
  import { resolve } from "$app/paths";
  import { Button } from "$lib/components/ui/button";
  import EntityCard from "$lib/qmx/EntityCard.svelte";
  import SpecView from "$lib/sdk/SpecView.svelte";
  import { cn } from "$lib/utils";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import type { Block } from "./demo";

  let {
    blocks,
    onartifact,
    onagent,
    oncontinue,
    onresolve,
    answers,
    onanswer,
    onopenagent,
    onpanel,
    compact = false,
    pendingBelow = false,
  }: {
    blocks: Block[];
    onartifact?: (id: string) => void;
    onagent?: () => void;
    oncontinue?: () => void;
    onresolve?: () => void;
    answers?: Record<number, string>;
    onanswer?: (index: number, value: string) => void;
    onopenagent?: (agentId: string) => void;
    onpanel?: (index: number, state: "kept" | "discarded" | "pinned") => void;
    /** Narrow side columns. */
    compact?: boolean;
    /** Unanswered questions are answered at the message box, not here. */
    pendingBelow?: boolean;
  } = $props();

  let local = $state<Record<number, string>>({});
  const got = $derived(answers ?? local);
  function answer(i: number, v: string) {
    if (got[i]) return;
    if (onanswer) onanswer(i, v);
    else local[i] = v;
    onresolve?.();
  }
  let other = $state<Record<number, string>>({});
  let open = $state<Record<number, boolean>>({});

  // Group the log into turns: your message, then everything until the next one.
  type Item = { b: Block; i: number };
  const turns = $derived.by(() => {
    const out: { you?: Item; reply: Item[] }[] = [];
    blocks.forEach((b, i) => {
      if (b.kind === "user" || !out.length) out.push({ reply: [] });
      if (b.kind === "user") out[out.length - 1].you = { b, i };
      else out[out.length - 1].reply.push({ b, i });
    });
    return out;
  });
  const WORK = ["tools", "agents", "changes", "artifact"];
  function receipt(items: Item[]) {
    const work = items.filter((x) => WORK.includes(x.b.kind));
    let tools = 0;
    let helpers = 0;
    let changes = 0;
    let reports = 0;
    for (const { b } of work) {
      if (b.kind === "tools") tools += b.calls.length;
      if (b.kind === "agents") helpers += b.agents.length;
      if (b.kind === "changes") changes += b.changes.length;
      if (b.kind === "artifact") reports += 1;
    }
    const parts = [
      helpers && `${helpers} ${helpers === 1 ? "helper" : "helpers"}`,
      tools && `${tools} ${tools === 1 ? "tool" : "tools"}`,
      changes && `changed ${changes} ${changes === 1 ? "thing" : "things"}`,
      reports && `${reports} ${reports === 1 ? "report" : "reports"}`,
    ].filter(Boolean);
    return { work, text: parts.join(" · ") };
  }
  const hrefOf = (path: string, query?: string) =>
    `${resolve(path as "/")}${query ? `?${query}` : ""}`;
</script>

<div
  class={cn(
    "mx-auto flex w-full max-w-[46rem] flex-col",
    compact ? "gap-5 px-4 py-4" : "gap-10 px-8 py-10",
  )}
>
  {#each turns as t, ti (ti)}
    <article class="flex flex-col gap-4">
      {#if t.you && t.you.b.kind === "user"}
        <div class="flex flex-col items-end gap-1.5">
          <p
            class={cn(
              "bg-muted max-w-[85%] rounded-2xl px-4 py-2.5 leading-relaxed",
              compact ? "text-sm" : "text-[1.05rem]",
            )}
          >
            {t.you.b.text}
          </p>
          {#if t.you.b.attached?.length}
            <p
              class="text-muted-foreground flex flex-wrap justify-end gap-x-3 gap-y-1 text-sm"
            >
              {#each t.you.b.attached as a (a)}<span
                  class="flex items-center gap-1"
                  ><Paperclip class="size-3.5" />{a}</span
                >{/each}
            </p>
          {/if}
        </div>
      {/if}

      {#each t.reply as { b, i } (i)}
        {#if b.kind === "text"}
          <div>
            <p
              class={cn(
                "leading-[1.7]",
                compact ? "text-sm" : "text-[1.12rem]",
              )}
            >
              {b.text}
            </p>
            {#if b.demo}<p class="text-muted-foreground mt-1.5 text-sm">
                Demo reply: scripted, no model connected.
              </p>{/if}
          </div>
        {:else if b.kind === "handoff"}
          <div
            class="border-info/40 flex flex-wrap items-center gap-3 rounded-xl border px-4 py-3"
          >
            <Shuffle class="text-info size-5 shrink-0" />
            <span class="min-w-0 flex-1">{b.note}</span>
            {#if oncontinue}<Button variant="outline" onclick={oncontinue}
                >Continue here</Button
              >{/if}
          </div>
        {:else if b.kind === "table"}
          <section class="overflow-hidden rounded-xl border">
            <div class="flex items-center border-b px-4 py-2">
              <span class="font-medium">{b.title}</span>
              <Button
                size="icon-sm"
                variant="ghost"
                class="ml-auto"
                aria-label="Copy table"
                onclick={() =>
                  navigator.clipboard
                    ?.writeText(
                      [b.head, ...b.rows].map((r) => r.join("\t")).join("\n"),
                    )
                    .then(() => workbench.notify("Table copied."))}
                ><Copy /></Button
              >
            </div>
            <table class="w-full">
              <thead class="text-muted-foreground text-left text-sm">
                <tr>
                  {#each b.head as h, k (k)}<th
                      class={cn("px-4 py-2 font-medium", k && "text-right")}
                      >{h}</th
                    >{/each}
                </tr>
              </thead>
              <tbody>
                {#each b.rows as r, k (k)}
                  <tr class="border-t">
                    {#each r as c, n (n)}<td
                        class={cn("px-4 py-2.5", n && "num text-right")}>{c}</td
                      >{/each}
                  </tr>
                {/each}
              </tbody>
            </table>
          </section>
        {:else if b.kind === "cards"}
          <div class="grid gap-4 sm:grid-cols-2">
            <div>
              <p class="text-muted-foreground mb-2 text-sm">
                Before · {b.before.version}
              </p>
              <EntityCard
                entity={b.before}
                compact
                href={resolve("/library/[id]", { id: b.before.id })}
              />
            </div>
            <div>
              <p class="text-muted-foreground mb-2 text-sm">Draft · not run</p>
              <EntityCard
                entity={b.after}
                compact
                href={resolve("/library/[id]", { id: b.before.id })}
                changed={b.changed}
              />
            </div>
          </div>
        {:else if b.kind === "panel"}
          <section
            class={cn(
              "rounded-2xl border",
              b.state === "draft" && "border-primary/60",
              b.state === "discarded" && "opacity-50",
            )}
          >
            <div class="flex flex-wrap items-center gap-3 border-b px-5 py-3">
              <span class="text-lg font-semibold">{b.spec.title}</span>
              <span class="text-muted-foreground text-sm"
                >{b.state === "draft"
                  ? "A draft it built for you"
                  : b.state === "kept"
                    ? "Kept here"
                    : b.state === "pinned"
                      ? "Pinned to the Lab"
                      : "Thrown away"}</span
              >
            </div>
            {#if b.state !== "discarded"}
              <div class="p-5">
                <SpecView
                  spec={b.spec}
                  onaction={(op) =>
                    workbench.notify(`The panel asked the host to run ${op}.`)}
                />
              </div>
            {/if}
            {#if b.state === "draft" && onpanel}
              <div class="flex flex-wrap gap-2 border-t px-5 py-3">
                <Button onclick={() => onpanel(i, "pinned")}
                  ><Pin />Pin to the Lab</Button
                >
                <Button variant="outline" onclick={() => onpanel(i, "kept")}
                  >Keep it here</Button
                >
                <Button variant="ghost" onclick={() => onpanel(i, "discarded")}
                  >Throw away</Button
                >
              </div>
            {/if}
          </section>
        {:else if (b.kind === "ask" || b.kind === "permission") && pendingBelow && !got[i]}
          <p
            class="border-warning/50 text-warning flex items-center gap-2 rounded-xl border border-dashed px-4 py-3"
          >
            <CircleHelp class="size-5 shrink-0" />{b.kind === "ask"
              ? b.question
              : `Needs your yes: ${b.action}.`} Answer below.
          </p>
        {:else if b.kind === "ask"}
          <section class="border-warning/50 rounded-2xl border px-5 py-4">
            <p class="flex items-center gap-2 text-[1.05rem] font-medium">
              <CircleHelp class="text-warning size-5" />{b.question}
            </p>
            {#if got[i]}
              <p class="mt-2">
                <Check class="text-success mr-1 inline size-4" />You chose
                <span class="font-medium">{got[i]}</span>.
              </p>
            {:else}
              <div class="mt-3 grid gap-2">
                {#each b.options as o (o.label)}
                  <button
                    type="button"
                    class="hover:border-ring/60 hover:bg-muted/40 flex flex-col rounded-xl border px-4 py-3 text-left"
                    onclick={() => answer(i, o.label)}
                  >
                    <span class="font-medium"
                      >{o.label}{#if o.recommended}<span
                          class="text-primary ml-2 text-sm font-normal"
                          >Suggested</span
                        >{/if}</span
                    >
                    <span class="text-muted-foreground text-sm">{o.note}</span>
                  </button>
                {/each}
                <form
                  class="flex gap-2"
                  onsubmit={(e) => {
                    e.preventDefault();
                    if (other[i]?.trim()) answer(i, other[i].trim());
                  }}
                >
                  <input
                    class="bg-background/40 h-10 min-w-0 flex-1 rounded-lg border px-3"
                    placeholder="Something else…"
                    aria-label="Your own answer"
                    bind:value={other[i]}
                  />
                  <Button type="submit" variant="outline">Answer</Button>
                </form>
              </div>
            {/if}
          </section>
        {:else if b.kind === "permission"}
          <section class="border-primary/50 rounded-2xl border px-5 py-4">
            <p class="flex items-center gap-2 text-[1.05rem] font-medium">
              <ShieldCheck class="text-primary size-5" />Needs your yes: {b.action}
            </p>
            <p class="mt-1">{b.detail}</p>
            <p class="text-muted-foreground mt-1 text-sm">{b.guard}</p>
            {#if got[i]}
              <p class="mt-2">
                <Check class="text-success mr-1 inline size-4" />{got[i]}.
              </p>
            {:else}
              <div class="mt-3 flex flex-wrap gap-2">
                <Button onclick={() => answer(i, "Allowed once")}>Allow</Button>
                <Button
                  variant="outline"
                  onclick={() =>
                    answer(i, "Allowed for the rest of this errand")}
                  >Allow for this errand</Button
                >
                <Button
                  variant="ghost"
                  onclick={() => answer(i, "Not now; it will ask again later")}
                  >Not now</Button
                >
              </div>
            {/if}
          </section>
        {/if}
      {/each}

      {#if receipt(t.reply).work.length}
        {@const r = receipt(t.reply)}
        <div>
          <button
            type="button"
            class="text-muted-foreground hover:text-foreground flex items-center gap-2 text-sm"
            aria-expanded={!!open[ti]}
            onclick={() => (open[ti] = !open[ti])}
          >
            <ChevronDown
              class={cn(
                "size-4 transition-transform",
                !open[ti] && "-rotate-90",
              )}
            />
            What it did: {r.text}
          </button>
          {#if open[ti]}
            <div
              class="border-border mt-3 ml-2 flex flex-col gap-4 border-l-2 pl-5"
            >
              {#each r.work as { b }, k (k)}
                {#if b.kind === "agents"}
                  <div>
                    <p class="mb-2 text-sm font-medium">Helpers</p>
                    <ul class="flex flex-col gap-1">
                      {#each b.agents as a (a.id)}
                        <li>
                          <button
                            type="button"
                            class="hover:bg-muted/50 flex w-full items-center gap-3 rounded-lg px-2 py-1.5 text-left"
                            onclick={() =>
                              onopenagent ? onopenagent(a.id) : onagent?.()}
                          >
                            <span
                              class={cn(
                                "size-2.5 shrink-0 rounded-full",
                                a.state === "running"
                                  ? "bg-info remote-pulse"
                                  : "bg-success",
                              )}
                            ></span>
                            <span class="min-w-0 flex-1">
                              <span class="font-medium">{a.name}</span>
                              <span class="text-muted-foreground">
                                · {a.last}</span
                              >
                            </span>
                            <span class="text-muted-foreground shrink-0 text-sm"
                              >{a.where}</span
                            >
                          </button>
                        </li>
                      {/each}
                    </ul>
                  </div>
                {:else if b.kind === "tools"}
                  <div>
                    <p class="mb-2 text-sm font-medium">Tools</p>
                    <ul class="flex flex-col gap-1 font-mono text-sm">
                      {#each b.calls as c, n (n)}
                        <li class="flex gap-3">
                          <Check class="text-success mt-0.5 size-4 shrink-0" />
                          <span class="min-w-0 flex-1 truncate"
                            >{c.name}
                            <span class="text-muted-foreground">{c.args}</span
                            ></span
                          >
                          <span class="text-muted-foreground shrink-0"
                            >{(c.ms / 1000).toFixed(1)}s</span
                          >
                        </li>
                      {/each}
                    </ul>
                  </div>
                {:else if b.kind === "changes"}
                  <div>
                    <p class="mb-2 text-sm font-medium">
                      Changed elsewhere in QMX
                    </p>
                    <ul class="flex flex-col gap-1">
                      <!-- eslint-disable svelte/no-navigation-without-resolve -->
                      {#each b.changes as c, n (n)}
                        <li>
                          <a
                            href={hrefOf(c.path, c.query)}
                            class="hover:bg-muted/50 flex items-center gap-3 rounded-lg px-2 py-1.5"
                          >
                            <span
                              class="text-muted-foreground w-16 shrink-0 text-sm"
                              >{c.place}</span
                            >
                            <span class="min-w-0 flex-1">{c.what}</span>
                            <ArrowUpRight
                              class="text-muted-foreground size-4"
                            />
                          </a>
                        </li>
                      {/each}
                      <!-- eslint-enable svelte/no-navigation-without-resolve -->
                    </ul>
                  </div>
                {:else if b.kind === "artifact"}
                  <button
                    type="button"
                    class="hover:bg-muted/50 flex items-center gap-3 rounded-xl border px-4 py-3 text-left"
                    onclick={() => onartifact?.(b.id)}
                  >
                    <FileText class="text-primary size-5 shrink-0" />
                    <span class="min-w-0 flex-1">
                      <span class="block font-medium">{b.title}</span>
                      <span class="text-muted-foreground text-sm"
                        >{b.type} · {b.note}</span
                      >
                    </span>
                    <span class="text-primary text-sm">Open</span>
                  </button>
                {/if}
              {/each}
            </div>
          {/if}
        </div>
      {/if}
    </article>
  {/each}
</div>
