<script lang="ts">
  import type { Place } from "$lib/shell/data";
  import { shell } from "$lib/shell/state.svelte";
  import { Button } from "$lib/components/ui/button";
  import Icon from "./Icon.svelte";
  import Sessions from "./Sessions.svelte";

  // Day one. A desk before the open: the markets are already moving, and
  // there is a short checklist between you and your first unit on paper.
  // Other boards say what will show up there.
  let { place, onstart }: { place: Place; onstart?: () => void } = $props();
  const overview = $derived(place.id === "overview");
  const today = new Intl.DateTimeFormat("en-GB", { weekday: "long", day: "numeric", month: "long" }).format(new Date());
</script>

{#if overview}
  <div class="mx-auto flex h-full max-w-[84rem] min-h-0 flex-col gap-10 overflow-y-auto p-10 [justify-content:safe_center]">
    <div class="grid items-end gap-x-12 gap-y-6 [grid-template-columns:repeat(auto-fit,minmax(min(100%,24rem),1fr))]">
      <div>
        <p class="num text-muted-foreground mb-4 flex items-center gap-2 text-sm tracking-wide uppercase">
          <Icon name={place.icon} class="size-4" />{today}
        </p>
        <h2 class="display text-5xl leading-[1.02] font-semibold text-balance">{place.first.title}</h2>
        <p class="text-muted-foreground mt-4 max-w-[38rem] text-lg text-pretty">{place.first.line}</p>
      </div>
      <Sessions />
    </div>

    <ol class="grid gap-[var(--gap)] [grid-template-columns:repeat(auto-fit,minmax(min(100%,12rem),1fr))]">
      {#each place.first.steps as step, i (step)}
        <li class="surface flex min-w-0 {i === 0 ? '' : 'opacity-60'}">
          <svelte:element
            this={i === 0 ? "button" : "div"}
            class="flex w-full min-w-0 flex-col gap-6 p-4 text-left {i === 0 ? 'rounded-[inherit] transition-colors duration-150 hover:bg-white/[0.03] active:scale-[0.99]' : ''}"
            onclick={i === 0 ? () => shell.go("usage") : undefined}
            role={i === 0 ? undefined : "presentation"}
          >
            <span class="flex items-center justify-between">
              <span class="num text-muted-foreground text-sm">{String(i + 1).padStart(2, "0")}</span>
              <span class="num text-xs tracking-wide uppercase {i === 0 ? 'text-needs' : 'text-idle'}">{i === 0 ? "Next" : "To do"}</span>
            </span>
            <span class="text-lg leading-snug font-medium text-pretty">{step}</span>
          </svelte:element>
        </li>
      {/each}
    </ol>

    <div class="flex flex-wrap items-center gap-4">
      <Button size="lg" class="h-11 px-5 text-base" onclick={onstart}>{place.first.action}</Button>
      <Button size="lg" variant="ghost" class="h-11 px-4 text-base" onclick={() => shell.setFixture("demo")}>Look around with demo data</Button>
    </div>
  </div>
{:else}
  <div class="flex h-full flex-col items-start justify-center gap-3 px-10">
    <p class="num text-muted-foreground flex items-center gap-2 text-sm tracking-wide uppercase"><Icon name={place.icon} class="size-4" />{place.name}</p>
    <h2 class="display text-4xl font-semibold">{place.first.title}</h2>
    <p class="text-muted-foreground text-lg">{place.first.line}</p>
    {#if place.first.action}
      <button class="bg-foreground text-background mt-2 h-11 rounded-md px-5 font-semibold transition-transform duration-100 active:scale-[0.97]" onclick={() => shell.say(`Demo: "${place.first.action}" starts a guided flow`)}>{place.first.action}</button>
    {/if}
  </div>
{/if}
