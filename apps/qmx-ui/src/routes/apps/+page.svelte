<script lang="ts">
  /**
   * Apps (mini apps pass 1, 2026-10-04). Every app sits on its road to
   * live, the way a pod does: what's live and working for you, what's
   * still proving itself, and what's being built (often by the copilot
   * overnight). Pick one to see what it proved, what it gives you and the
   * box it runs in. New apps come from a description, from widgets you
   * already have, or from a template. DEMO data.
   */
  import DemoChip from "$lib/workbench/DemoChip.svelte";
  import Plus from "@lucide/svelte/icons/plus";
  import ShieldOff from "@lucide/svelte/icons/shield-off";
  import { goto } from "$app/navigation";
  import { resolve } from "$app/paths";
  import { Button } from "$lib/components/ui/button";
  import { Switch } from "$lib/components/ui/switch";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu";
  import { cn } from "$lib/utils";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import AppDetail from "$lib/apps/AppDetail.svelte";
  import FromWidgets from "$lib/apps/FromWidgets.svelte";
  import {
    RISK,
    STEPS,
    TEMPLATES,
    apps,
    type MiniApp,
  } from "$lib/apps/apps.svelte";

  let widgetsOpen = $state(false);
  const selected = $derived(apps.byId(apps.selected));

  const BANDS = [
    {
      id: "live",
      title: "Live",
      note: "Working for you, each inside its own box",
      test: (a: MiniApp) => a.stage === 4,
    },
    {
      id: "proving",
      title: "Proving itself",
      note: "Tests, then a sandbox on recorded data, then a shadow run on live data that nothing uses yet",
      test: (a: MiniApp) => a.stage > 0 && a.stage < 4,
    },
    {
      id: "building",
      title: "Being built",
      note: "By you or the copilot; nothing runs for real yet",
      test: (a: MiniApp) => a.stage === 0,
    },
  ];
  const order = (a: MiniApp) => (a.health === "tripped" ? 0 : 1);
  const HEALTH: Record<string, string> = {
    ok: "bg-success",
    warn: "bg-warning",
    tripped: "bg-destructive",
    idle: "bg-muted-foreground",
  };

  /* eslint-disable svelte/no-navigation-without-resolve */
  const ask = (q: string) =>
    goto(resolve("/copilot") + "?ask=" + encodeURIComponent(q));
  /* eslint-enable svelte/no-navigation-without-resolve */
</script>

<div class="flex h-full min-h-0 flex-col">
  <header class="flex flex-wrap items-center gap-4 border-b px-8 py-5">
    <div class="min-w-0 flex-1">
      <div class="flex items-center gap-3">
        <h1 class="text-3xl font-semibold tracking-tight">Apps</h1>
        <DemoChip
          note="Sample apps. Stages, evidence and logs come from the backend once it is wired."
        />
      </div>
      <p class="text-muted-foreground mt-1 text-lg">
        {apps.all.filter((a) => a.stage === 4).length} live ·
        {apps.all.filter((a) => a.stage > 0 && a.stage < 4).length} proving ·
        {apps.all.filter((a) => a.stage === 0).length} being built
      </p>
    </div>
    <label
      class={cn(
        "flex items-center gap-3 rounded-xl border px-4 py-2",
        apps.safe && "border-warning/60",
      )}
    >
      <ShieldOff class="text-muted-foreground size-5" />
      <span>
        <span class="block font-medium">Safe mode</span>
        <span class="text-muted-foreground block text-sm"
          >Turns every app off at once</span
        >
      </span>
      <Switch bind:checked={apps.safe} aria-label="Safe mode" />
    </label>
    <DropdownMenu.Root>
      <DropdownMenu.Trigger>
        {#snippet child({ props })}
          <Button {...props} size="lg"><Plus />New app</Button>
        {/snippet}
      </DropdownMenu.Trigger>
      <DropdownMenu.Content align="end" class="w-80">
        <DropdownMenu.Item
          class="flex-col items-start gap-0.5 py-2"
          onclick={() => ask("Build me an app that ")}
          ><span class="font-medium">Describe it to the copilot</span><span
            class="text-muted-foreground text-sm"
            >It builds it, overnight if needed</span
          ></DropdownMenu.Item
        >
        <DropdownMenu.Item
          class="flex-col items-start gap-0.5 py-2"
          onclick={() => (widgetsOpen = true)}
          ><span class="font-medium">Make it from widgets</span><span
            class="text-muted-foreground text-sm"
            >Pick from Home and Portfolio</span
          ></DropdownMenu.Item
        >
        <DropdownMenu.Item
          class="flex-col items-start gap-0.5 py-2"
          onclick={() =>
            document
              .getElementById("templates")
              ?.scrollIntoView({ behavior: "smooth" })}
          ><span class="font-medium">Start from a template</span><span
            class="text-muted-foreground text-sm">Below the list</span
          ></DropdownMenu.Item
        >
      </DropdownMenu.Content>
    </DropdownMenu.Root>
  </header>

  <div class="flex min-h-0 flex-1">
    <div class="@container min-w-0 flex-1 overflow-auto px-8 py-6">
      {#each BANDS as b (b.id)}
        {@const list = apps.all
          .filter(b.test)
          .sort((x, y) => order(x) - order(y))}
        <section class="mb-9">
          <div class="mb-3 flex flex-wrap items-baseline gap-x-3">
            <h2 class="text-xl font-semibold">{b.title}</h2>
            <span class="text-muted-foreground">{b.note}</span>
          </div>
          {#if list.length}
            <ul
              class="grid gap-3 [grid-template-columns:repeat(auto-fill,minmax(19rem,1fr))]"
            >
              {#each list as a (a.id)}
                <li>
                  <button
                    type="button"
                    aria-pressed={apps.selected === a.id}
                    class={cn(
                      "solid-backing flex h-full w-full flex-col gap-2 rounded-2xl border-2 p-5 text-left transition-colors",
                      apps.selected === a.id
                        ? "border-primary"
                        : "hover:border-ring/60 border-transparent ring-1 ring-border",
                      a.health === "tripped" && "border-destructive/70",
                      (!a.on || apps.safe) && "opacity-55",
                    )}
                    onclick={() => (apps.selected = a.id)}
                  >
                    <span class="flex items-center gap-2">
                      <span
                        class={cn(
                          "size-2.5 shrink-0 rounded-full",
                          HEALTH[a.health],
                        )}
                      ></span>
                      <span class="truncate text-lg font-semibold"
                        >{a.name}</span
                      >
                      <span
                        class={cn(
                          "ml-auto shrink-0 rounded-full px-2.5 py-0.5 text-sm",
                          a.risk === "money"
                            ? "bg-warning/15 text-warning"
                            : "bg-muted",
                        )}>{RISK[a.risk].label}</span
                      >
                    </span>
                    <span class="text-muted-foreground line-clamp-2"
                      >{a.summary}</span
                    >
                    <span class="mt-auto flex gap-1 pt-2" aria-hidden="true">
                      {#each STEPS as s, k (s)}
                        <span
                          class={cn(
                            "h-1.5 flex-1 rounded-full",
                            k < a.stage || a.stage === 4
                              ? "bg-success"
                              : k === a.stage
                                ? "bg-info"
                                : "bg-muted",
                          )}
                        ></span>
                      {/each}
                    </span>
                    <span
                      class={cn(
                        "text-sm",
                        a.health === "tripped"
                          ? "text-destructive"
                          : "text-muted-foreground",
                      )}>{a.stageNote}</span
                    >
                  </button>
                </li>
              {/each}
            </ul>
          {:else}
            <p
              class="text-muted-foreground rounded-2xl border border-dashed p-5"
            >
              Nothing here yet.
            </p>
          {/if}
        </section>
      {/each}

      <section id="templates" class="mb-6">
        <div class="mb-3 flex flex-wrap items-baseline gap-x-3">
          <h2 class="text-xl font-semibold">Start from a template</h2>
          <span class="text-muted-foreground"
            >The copilot fills it in with you, then it starts at Build</span
          >
        </div>
        <ul
          class="grid gap-3 [grid-template-columns:repeat(auto-fill,minmax(15rem,1fr))]"
        >
          {#each TEMPLATES as t (t.name)}
            <li>
              <button
                type="button"
                class="hover:border-ring/60 flex h-full w-full flex-col gap-1 rounded-2xl border border-dashed p-4 text-left"
                onclick={() =>
                  ask(`Build me a "${t.name}" app from the template: `)}
              >
                <span class="font-medium">{t.name}</span>
                <span class="text-muted-foreground">{t.note}</span>
                <span
                  class={cn(
                    "mt-1 text-sm",
                    t.risk === "money"
                      ? "text-warning"
                      : "text-muted-foreground",
                  )}>{RISK[t.risk].label}</span
                >
              </button>
            </li>
          {/each}
          <li>
            <button
              type="button"
              class="hover:border-ring/60 text-muted-foreground flex h-full w-full items-center justify-center gap-2 rounded-2xl border border-dashed p-4"
              onclick={() => (widgetsOpen = true)}
              ><Plus class="size-5" />From widgets you have</button
            >
          </li>
        </ul>
      </section>
    </div>

    {#if selected}
      <aside class="w-[min(34rem,45%)] shrink-0 border-l">
        <AppDetail app={selected} onclose={() => (apps.selected = null)} />
      </aside>
    {/if}
  </div>
</div>

<FromWidgets bind:open={widgetsOpen} />
