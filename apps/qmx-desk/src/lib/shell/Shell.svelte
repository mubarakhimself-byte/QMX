<script lang="ts">
  import { shell } from "./state.svelte";
  import { things } from "./things.svelte";
  import * as Tooltip from "$lib/components/ui/tooltip";
  import Icon from "$lib/qmx/Icon.svelte";
  import IconButton from "$lib/qmx/IconButton.svelte";
  import Board from "$lib/qmx/Board.svelte";
  import Page from "$lib/pages/Page.svelte";
  import ListView from "$lib/pages/ListView.svelte";
  import AppPage from "$lib/pages/AppPage.svelte";
  import Trail from "./Trail.svelte";
  import CopilotDock from "./CopilotDock.svelte";
  import StatusBar from "./StatusBar.svelte";
  import Command from "./Command.svelte";
  import Pills from "./nav/Pills.svelte";

  // One job per element in the top bar. Left: where you are and the way
  // back. Centre: the command field reaches everything. Right: your AI
  // usage, settings, the copilot, the window. Below: the two pills, then
  // either a board of widgets, a list of his things, or a thing's page.
  const place = $derived(shell.current);
  const first = $derived(shell.fixture === "first");
  const app = $derived(place.kind === "app" ? things.guest(place.id.slice(4)) : undefined);

  // Esc goes back: out of "Edit page" first, then one step up the trail.
  $effect(() => {
    const onkey = (e: KeyboardEvent) => {
      const t = e.target as HTMLElement;
      if (/^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName) || t.isContentEditable) return;
      if (document.querySelector("[role=menu], [role=dialog]")) return;
      if (e.key === "Escape" || (e.altKey && e.key === "ArrowLeft")) {
        if (things.editing) return things.setEditing(false);
        if (shell.canBack) shell.back();
      }
    };
    window.addEventListener("keydown", onkey);
    return () => window.removeEventListener("keydown", onkey);
  });
</script>

{#snippet windowControls()}
  <div class="text-muted-foreground ml-1 flex shrink-0 items-center" aria-hidden="true">
    <span class="grid h-9 w-10 place-items-center"><Icon name="minus" class="size-3.5" /></span>
    <span class="grid h-9 w-10 place-items-center"><Icon name="square" class="size-3" /></span>
    <span class="grid h-9 w-10 place-items-center"><Icon name="x" class="size-4" /></span>
  </div>
{/snippet}

<div class="app flex h-full min-h-0 flex-col" data-look="night">
  <header class="border-border flex h-14 shrink-0 items-center gap-3 border-b pr-1 pl-3">
    <div class="flex min-w-0 flex-1 items-center"><Trail /></div>
    <div class="flex w-[min(36rem,38%)] min-w-[13rem] shrink-0 justify-center"><Command primary /></div>
    <div class="flex shrink-0 items-center justify-end gap-1">
      <Tooltip.Root>
        <Tooltip.Trigger>
          {#snippet child({ props })}
            <button {...props} class="press h-9 shrink-0 gap-1.5 px-2.5" data-on={shell.place === "usage"} aria-label="AI usage" onclick={() => shell.go("usage")}>
              <Icon name="gauge" />
              {#if !first}<span class="num text-foreground text-sm">62%</span>{/if}
            </button>
          {/snippet}
        </Tooltip.Trigger>
        <Tooltip.Content>{first ? "AI usage · no provider connected" : "AI usage · Claude Max, 5-hour window"}</Tooltip.Content>
      </Tooltip.Root>
      <IconButton icon="settings" label="Settings" size="size-9" on={shell.place === "settings"} onclick={() => shell.go("settings")} />
      <button class="press ml-1 h-9 shrink-0 gap-2 px-3" data-on={shell.dock} onclick={() => shell.toggleDock()}>
        <Icon name="sparkles" />Copilot
      </button>
      {@render windowControls()}
    </div>
  </header>

  <div class="relative flex min-h-0 flex-1">
    <div class="flex min-w-0 flex-1 overflow-hidden pl-[4.25rem]">
      <main class="relative min-w-0 flex-1 overflow-hidden">
        {#if shell.page && !first}
          <div class="sheet h-full p-[var(--gap)]"><div class="surface h-full overflow-hidden"><Page /></div></div>
        {:else if place.kind === "list"}
          <div class="sheet h-full p-[var(--gap)]"><div class="surface h-full overflow-hidden"><ListView list={place.list!} /></div></div>
        {:else if place.kind === "app"}
          <div class="sheet h-full p-[var(--gap)]">
            <div class="surface h-full overflow-hidden">
              {#if app && !first}<AppPage id={app.id} />{:else}<p class="text-muted-foreground p-6">This mini app is not installed.</p>{/if}
            </div>
          </div>
        {:else}
          <Board />
        {/if}

        {#if shell.toast}
          {@const t = shell.toast}
          <div class="toast bg-popover border-border absolute bottom-4 left-1/2 z-40 flex max-w-[min(36rem,90%)] -translate-x-1/2 items-center gap-3 rounded-lg border py-2 pr-2 pl-4 shadow-2xl shadow-black" role="status">
            <span class="dot text-up shrink-0"></span>
            <span class="min-w-0 truncate" title={t.text}>{t.text}</span>
            {#if t.undo}<button class="press h-8 shrink-0 gap-1.5 px-3 font-medium" onclick={() => (t.undo?.(), shell.hush())}><Icon name="undo" class="size-3.5" />Undo</button>{/if}
            <button class="press size-8 shrink-0" aria-label="Dismiss" onclick={() => shell.hush()}><Icon name="x" /></button>
          </div>
        {/if}
      </main>
    </div>
    <Pills />
    {#if shell.dock}<CopilotDock />{/if}
  </div>
  <StatusBar />
</div>

<style>
  .toast {
    transition:
      opacity 180ms cubic-bezier(0.23, 1, 0.32, 1),
      transform 180ms cubic-bezier(0.23, 1, 0.32, 1);
    @starting-style {
      opacity: 0;
      transform: translate(-50%, 0.5rem);
    }
  }
</style>
