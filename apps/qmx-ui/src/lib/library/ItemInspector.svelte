<script lang="ts">
  /**
   * The selected Library item: what it is, where it is used across QMX (as a
   * map and as links), its settings, and what you can do with it. Every
   * "used in" row is a real link into the Lab, Portfolio, Copilot or Home.
   */
  import ArrowUpRight from "@lucide/svelte/icons/arrow-up-right";
  import MessageSquarePlus from "@lucide/svelte/icons/message-square-plus";
  import Maximize2 from "@lucide/svelte/icons/maximize-2";
  import GitBranch from "@lucide/svelte/icons/git-branch";
  import Play from "@lucide/svelte/icons/play";
  import Download from "@lucide/svelte/icons/download";
  import { resolve } from "$app/paths";
  import { Button } from "$lib/components/ui/button";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import ConnectionsMap from "./ConnectionsMap.svelte";
  import {
    familyColor,
    shelfById,
    type LibraryItem,
    type Place,
    type Use,
  } from "./items";

  let { item }: { item: LibraryItem } = $props();
  let filter = $state<Place | null>(null);
  $effect(() => {
    void item.id;
    filter = null;
  });

  const shelf = $derived(shelfById(item.shelf)!);
  const color = $derived(familyColor(item));
  const shown = $derived(
    filter ? item.uses.filter((u) => u.place === filter) : item.uses,
  );
  const hrefOf = (u: Use) =>
    `${resolve(u.path as "/")}${u.query ? `?${u.query}` : ""}`;
  const details = $derived<[string, string][]>(
    item.details ??
      item.entity?.parameters ??
      (item.entity?.steps
        ? item.entity.steps.map((s, i) => [`Step ${i + 1}`, s])
        : []),
  );
</script>

<div class="flex h-full flex-col">
  <header class="shrink-0 border-b">
    <div class="h-1.5" style="background:{color}"></div>
    <div class="flex flex-col gap-2 px-4 py-3">
      <p class="text-muted-foreground flex items-center gap-1.5 text-xs">
        <shelf.icon class="size-3.5" />{shelf.label}{item.family
          ? ` · ${item.family}`
          : ""}
      </p>
      <h2 class="text-xl leading-snug font-semibold">
        {item.name}{#if item.version}<span
            class="text-muted-foreground ml-2 text-base font-normal"
            >{item.version}</span
          >{/if}
      </h2>
      <p class="text-muted-foreground text-sm">{item.summary}</p>
      <!-- eslint-disable svelte/no-navigation-without-resolve -->
      <div class="flex flex-wrap gap-1.5">
        {#if item.starts}
          <Button size="sm" href={hrefOf(item.starts)}
            ><Play />Use this template</Button
          >
        {/if}
        {#if item.entity}
          <Button
            size="sm"
            variant={item.starts ? "outline" : "default"}
            href={resolve("/library/[id]", { id: item.entity.id })}
            ><Maximize2 />Full page</Button
          >
        {/if}
        {#if item.uses[0] && !item.starts}
          <Button size="sm" variant="outline" href={hrefOf(item.uses[0])}
            ><ArrowUpRight />Open in {item.uses[0].place}</Button
          >
        {/if}
        <Button
          size="sm"
          variant="ghost"
          onclick={() => workbench.addRef(item.name)}
          ><MessageSquarePlus />Add to copilot</Button
        >
        {#if item.shelf === "files"}
          <Button
            size="sm"
            variant="ghost"
            onclick={() =>
              workbench.notify(
                `Opening ${item.name} needs the daemon; it streams the file from the Library store.`,
              )}><Download />Open file</Button
          >
        {:else if !item.starts}
          <Button
            size="sm"
            variant="ghost"
            onclick={() =>
              workbench.notify(
                `A new version of ${item.name} starts as a draft; the current one stays as it is.`,
              )}><GitBranch />New version</Button
          >
        {/if}
      </div>
      <!-- eslint-enable svelte/no-navigation-without-resolve -->
    </div>
  </header>

  <div class="min-h-0 flex-1 overflow-auto px-4 py-3">
    {#if item.starts}
      <section class="mb-4">
        <h3 class="mb-1 text-sm font-medium">What it starts</h3>
        <p class="text-muted-foreground text-sm">
          {item.starts.what} in the {item.starts.place}. You get a draft;
          nothing runs until you save and start it.
        </p>
      </section>
    {:else}
      <section class="mb-4">
        <h3 class="mb-1 text-sm font-medium">Where it's used</h3>
        <ConnectionsMap uses={item.uses} {color} bind:filter />
        {#if shown.length}
          <ul class="mt-2 flex flex-col gap-1">
            <!-- eslint-disable svelte/no-navigation-without-resolve -->
            {#each shown as u, i (i)}
              <li>
                <a
                  href={hrefOf(u)}
                  class="hover:bg-muted flex items-center gap-2 rounded-md border px-3 py-2 text-sm"
                >
                  <span class="text-muted-foreground w-20 shrink-0 text-xs"
                    >{u.place}</span
                  >
                  <span class="min-w-0 flex-1 truncate">{u.what}</span>
                  <ArrowUpRight class="text-muted-foreground size-3.5" />
                </a>
              </li>
            {/each}
            <!-- eslint-enable svelte/no-navigation-without-resolve -->
          </ul>
        {:else}
          <p class="text-muted-foreground text-sm">
            Not used anywhere yet. Add it to a pod, a test or the copilot.
          </p>
        {/if}
      </section>
    {/if}

    {#if details.length}
      <section class="mb-4">
        <h3 class="mb-1 text-sm font-medium">Settings</h3>
        <dl
          class="grid grid-cols-[minmax(6rem,auto)_1fr] gap-x-4 gap-y-1.5 text-sm"
        >
          {#each details as [k, v] (k)}
            <dt class="text-muted-foreground">{k}</dt>
            <dd class="min-w-0 break-words">{v}</dd>
          {/each}
        </dl>
      </section>
    {/if}

    {#if item.entity?.measures?.length}
      <section>
        <h3 class="mb-1 text-sm font-medium">Measures</h3>
        <div class="grid grid-cols-2 gap-2">
          {#each item.entity.measures as m (m.key)}
            <div class="rounded-lg border px-3 py-2" title={m.help}>
              <p class="text-muted-foreground text-xs">{m.label}</p>
              <p class="num text-base font-semibold">{m.value}</p>
            </div>
          {/each}
        </div>
      </section>
    {/if}
  </div>
</div>
