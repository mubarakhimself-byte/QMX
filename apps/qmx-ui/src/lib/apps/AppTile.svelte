<script lang="ts">
  /**
   * One app on the Apps page: its icon, its name and a live glimpse of what it
   * gives you. Apps with a screen open on click; background apps open About.
   * Health is a dot; a stopped app says so calmly and offers Restart. The
   * first tile of a group carries the group's heading above it, so tiles keep
   * one width while the page still reads group by group.
   */
  import Info from "@lucide/svelte/icons/info";
  import RotateCcw from "@lucide/svelte/icons/rotate-ccw";
  import Star from "@lucide/svelte/icons/star";
  import { resolve } from "$app/paths";
  import { Button } from "$lib/components/ui/button";
  import { cn } from "$lib/utils";
  import Preview from "./Preview.svelte";
  import { STATUS, apps, type MiniApp } from "./apps.svelte";
  import { ICONS } from "./icons";
  import { GROUP_TINT } from "./tint";

  let { app, heading }: { app: MiniApp; heading?: string } = $props();

  const status = $derived(apps.status(app));
  const pinned = $derived(apps.pinned(app.id));
  const Icon = $derived(ICONS[app.icon]);
  const opens = $derived(Boolean(app.panels?.length));
  const hover =
    "opacity-0 transition-opacity group-focus-within:opacity-100 group-hover:opacity-100";
</script>

<li class="flex flex-col">
  <div class="mb-3 h-9">
    {#if heading}<h2 class="text-2xl font-semibold">{heading}</h2>{/if}
  </div>
  <div
    class={cn(
      "group solid-backing relative flex min-h-52 flex-1 flex-col gap-4 rounded-3xl p-panel ring-1 ring-border transition-[box-shadow,transform] hover:-translate-y-0.5 hover:shadow-lg hover:ring-ring/50",
      status === "stopped" && "ring-destructive/40",
    )}
  >
    <div class="flex items-center gap-3">
      <span
        class={cn(
          "flex size-11 shrink-0 items-center justify-center rounded-2xl",
          GROUP_TINT[app.group],
        )}><Icon class="size-5.5" /></span
      >
      <span class="min-w-0 flex-1">
        <span class="flex items-center gap-2">
          {#if opens}
            <a
              href={resolve("/apps/[id]", { id: app.id })}
              class="focus-visible:after:ring-ring min-w-0 truncate text-lg font-semibold outline-none after:absolute after:inset-0 after:rounded-3xl focus-visible:after:ring-2"
              >{app.name}</a
            >
          {:else}
            <button
              type="button"
              class="focus-visible:after:ring-ring min-w-0 truncate text-left text-lg font-semibold outline-none after:absolute after:inset-0 after:rounded-3xl focus-visible:after:ring-2"
              onclick={() => (apps.selected = app.id)}>{app.name}</button
            >
          {/if}
          <span
            class={cn("size-2 shrink-0 rounded-full", STATUS[status].dot)}
            title={STATUS[status].label}
            ><span class="sr-only">{STATUS[status].label}</span></span
          >
        </span>
        {#if status !== "live"}
          <span
            class={cn(
              "block text-sm",
              status === "stopped"
                ? "text-destructive"
                : "text-muted-foreground",
            )}>{STATUS[status].label}</span
          >
        {/if}
      </span>
    </div>

    <div class={cn("min-w-0 flex-1", status === "off" && "opacity-45")}>
      {#if app.preview}<Preview preview={app.preview} />{/if}
    </div>

    <div class="flex min-h-9 items-center gap-1">
      {#if status === "stopped"}
        <Button
          variant="outline"
          class="relative z-10"
          onclick={() => apps.restart(app.id)}><RotateCcw />Restart</Button
        >
      {:else if app.next}
        <span class="text-muted-foreground truncate text-sm">{app.next}</span>
      {/if}
      <Button
        variant="ghost"
        size="icon"
        class={cn("relative z-10 ml-auto", !pinned && hover)}
        aria-label={pinned ? `Unpin ${app.name}` : `Pin ${app.name}`}
        aria-pressed={pinned}
        onclick={() => apps.pin(app.id)}
        ><Star class={cn(pinned && "fill-primary text-primary")} /></Button
      >
      <Button
        variant="ghost"
        size="icon"
        class={cn("relative z-10", hover)}
        aria-label={`About ${app.name}`}
        onclick={() => (apps.selected = app.id)}><Info /></Button
      >
    </div>
  </div>
</li>
