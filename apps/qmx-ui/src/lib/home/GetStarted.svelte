<script lang="ts">
  /**
   * First run (demo off): four steps, each one click to the screen that does
   * it, with why it matters behind an info tip. A step ticks off once opened
   * (kept in this browser). Home shows these in place of its board until all
   * four are done or hidden.
   */
  import Check from "@lucide/svelte/icons/check";
  import Landmark from "@lucide/svelte/icons/landmark";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import Database from "@lucide/svelte/icons/database";
  import FlaskConical from "@lucide/svelte/icons/flask-conical";
  import { goto } from "$app/navigation";
  import { resolve } from "$app/paths";
  import { Button } from "$lib/components/ui/button";
  import InfoTip from "$lib/workbench/InfoTip.svelte";
  import { cn } from "$lib/utils";
  import { GET_STARTED, type StepId } from "$lib/workbench/day-one";
  import { home } from "./home.svelte";

  const ICON: Record<StepId, typeof Check> = {
    broker: Landmark,
    model: Sparkles,
    source: Database,
    start: FlaskConical,
  };
  const done = $derived(GET_STARTED.filter((s) => home.started.includes(s.id)));
  const next = $derived(GET_STARTED.find((s) => !home.started.includes(s.id)));

  function open(id: string, href: string) {
    home.markStarted(id);
    const [path, query] = href.split("?");
    // eslint-disable-next-line svelte/no-navigation-without-resolve -- resolved path plus a query string
    goto(`${resolve(path as "/")}${query ? `?${query}` : ""}`);
  }
</script>

<div class="flex flex-col gap-3">
  <div class="flex items-center gap-3">
    <span class="text-muted-foreground text-sm"
      >{done.length} of {GET_STARTED.length} done</span
    >
    <div
      class="bg-muted h-1.5 w-40 overflow-hidden rounded-full"
      aria-hidden="true"
    >
      <div
        class="bg-success h-full rounded-full transition-[width]"
        style="width: {(done.length / GET_STARTED.length) * 100}%"
      ></div>
    </div>
    <Button
      variant="ghost"
      size="sm"
      class="text-muted-foreground ml-auto"
      onclick={() => GET_STARTED.forEach((s) => home.markStarted(s.id))}
      >Hide these steps</Button
    >
  </div>
  <ol
    class="grid grid-cols-[repeat(auto-fit,minmax(14rem,1fr))] gap-3"
    aria-label="Steps"
  >
    {#each GET_STARTED as s, i (s.id)}
      {@const ok = home.started.includes(s.id)}
      {@const Icon = ICON[s.id]}
      <li
        class={cn(
          "solid-backing flex flex-col gap-4 rounded-xl border p-panel",
          next?.id === s.id && "border-primary/50",
          ok && "opacity-70",
        )}
      >
        <div class="flex items-start justify-between gap-2">
          <span
            class="bg-primary/12 text-primary flex size-11 items-center justify-center rounded-xl"
            ><Icon class="size-5" /></span
          >
          <span
            class={cn(
              "num text-muted-foreground flex size-7 shrink-0 items-center justify-center rounded-full border text-sm",
              ok && "bg-success/20 text-success border-transparent",
            )}
            >{#if ok}<Check class="size-4" /><span class="sr-only">Done</span
              >{:else}{i + 1}{/if}</span
          >
        </div>
        <div class="flex min-h-14 items-start gap-1">
          <h3 class="min-w-0 text-lg leading-snug font-medium">{s.title}</h3>
          <InfoTip label={`Why: ${s.title}`} text={s.why} />
        </div>
        <Button
          class="mt-auto w-full"
          variant={ok ? "ghost" : next?.id === s.id ? "default" : "outline"}
          onclick={() => open(s.id, s.href)}>{s.label}</Button
        >
      </li>
    {/each}
  </ol>
</div>
