<script lang="ts">
  /**
   * One app, told in the order you'd judge it: what it can touch and so
   * how it goes live; how far it has got and what each step proved; what
   * it gives you; the box it runs in (budget, network, circuit breaker);
   * and the last lines of its log. Actions fit its kind and state.
   */
  import Check from "@lucide/svelte/icons/check";
  import Lock from "@lucide/svelte/icons/lock";
  import Play from "@lucide/svelte/icons/play";
  import Pause from "@lucide/svelte/icons/pause";
  import RotateCcw from "@lucide/svelte/icons/rotate-ccw";
  import AppWindow from "@lucide/svelte/icons/app-window";
  import MessagesSquare from "@lucide/svelte/icons/messages-square";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import X from "@lucide/svelte/icons/x";
  import { resolve } from "$app/paths";
  import { Button } from "$lib/components/ui/button";
  import { Switch } from "$lib/components/ui/switch";
  import { cn } from "$lib/utils";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { KIND, RISK, STEPS, apps, type MiniApp } from "./apps.svelte";

  let { app, onclose }: { app: MiniApp; onclose: () => void } = $props();

  const mine = $derived(apps.mine.some((a) => a.id === app.id));
  const ask = (q: string) =>
    resolve("/copilot") + "?ask=" + encodeURIComponent(q);
  const need = (what: string) => workbench.notify(`${what} needs the daemon.`);
</script>

<article class="solid-backing flex h-full flex-col overflow-hidden">
  <header class="flex items-start gap-3 border-b px-6 py-5">
    <div class="min-w-0 flex-1">
      <h2 class="text-2xl font-semibold">{app.name}</h2>
      <p class="text-muted-foreground mt-1 text-lg">{app.summary}</p>
      <p class="text-muted-foreground mt-2">
        {KIND[app.kind]} · Built by {app.builtBy}
      </p>
    </div>
    <Switch
      checked={app.on && !apps.safe}
      disabled={apps.safe}
      onCheckedChange={(v) => apps.toggle(app.id, v)}
      aria-label={`Turn ${app.name} on`}
    />
    <Button
      variant="ghost"
      size="icon"
      aria-label="Close details"
      onclick={onclose}><X /></Button
    >
  </header>

  <div class="flex min-h-0 flex-1 flex-col gap-7 overflow-auto px-6 py-6">
    <section
      class={cn(
        "flex items-start gap-3 rounded-2xl border p-4",
        app.risk === "money" && "border-warning/60",
      )}
    >
      {#if app.risk === "money"}<Lock
          class="text-warning mt-0.5 size-5 shrink-0"
        />{/if}
      <div>
        <p class="font-semibold">{RISK[app.risk].label}</p>
        <p class="text-muted-foreground">{RISK[app.risk].rule}</p>
      </div>
    </section>

    {#if app.health === "tripped"}
      <section class="border-destructive/60 rounded-2xl border p-4">
        <p class="text-destructive font-semibold">It stopped itself</p>
        <p class="mt-1">
          {app.stopped} Nothing else was affected.
        </p>
        <div class="mt-3 flex flex-wrap gap-2">
          <Button onclick={() => need(`Restarting ${app.name}`)}
            ><RotateCcw />Restart it</Button
          >
          <!-- eslint-disable svelte/no-navigation-without-resolve -->
          <Button
            variant="outline"
            href={ask(
              `Why did ${app.name} stop itself, and is it safe to restart?`,
            )}><MessagesSquare />Ask the copilot why</Button
          >
          <!-- eslint-enable svelte/no-navigation-without-resolve -->
        </div>
      </section>
    {/if}

    <section>
      <h3 class="mb-3 text-lg font-semibold">Road to live</h3>
      <ol class="flex flex-col">
        {#each STEPS as s, k (s)}
          {@const done = k < app.stage || (k === 4 && app.stage === 4)}
          {@const now = k === app.stage && app.stage < 4}
          <li class="flex gap-4">
            <span class="flex flex-col items-center">
              <span
                class={cn(
                  "flex size-7 shrink-0 items-center justify-center rounded-full border-2",
                  done && "border-success bg-success/15 text-success",
                  now && "border-info text-info",
                  !done && !now && "text-muted-foreground",
                )}
                >{#if done}<Check class="size-4" />{:else}<span class="text-sm"
                    >{k + 1}</span
                  >{/if}</span
              >
              {#if k < STEPS.length - 1}<span
                  class={cn(
                    "my-1 w-0.5 flex-1",
                    k < app.stage ? "bg-success/60" : "bg-border",
                  )}
                ></span>{/if}
            </span>
            <span class="min-w-0 pb-4">
              <span
                class={cn(
                  "block font-medium",
                  !done && !now && "text-muted-foreground",
                )}>{s}</span
              >
              {#if app.evidence[k]}<span class="text-muted-foreground block"
                  >{app.evidence[k]}</span
                >{:else if now || (k === 4 && app.stage === 4)}<span
                  class="text-info block">{app.stageNote}</span
                >{/if}
            </span>
          </li>
        {/each}
      </ol>
    </section>

    <section>
      <h3 class="mb-2 text-lg font-semibold">What it gives you</h3>
      <ul class="flex flex-col gap-1">
        {#each app.provides as p (p)}<li>{p}</li>{/each}
      </ul>
      {#if app.feeds?.length}
        <p class="text-muted-foreground mt-2">
          Feeds {app.feeds
            .map((f) => apps.byId(f)?.name)
            .filter(Boolean)
            .join(", ")}
        </p>
      {/if}
      {#if app.schedule}<p class="text-muted-foreground mt-2">
          Runs {app.schedule.toLowerCase()}
        </p>{/if}
    </section>

    <section>
      <h3 class="mb-3 text-lg font-semibold">Its box</h3>
      <dl class="grid gap-x-6 gap-y-3 sm:grid-cols-[9rem_1fr]">
        <dt class="text-muted-foreground">Runs on</dt>
        <dd>{app.runsOn}</dd>
        <dt class="text-muted-foreground">Budget</dt>
        <dd>
          {app.budget}
          <span class="mt-1.5 flex items-center gap-3">
            <span class="bg-muted h-2 flex-1 overflow-hidden rounded-full"
              ><span
                class={cn(
                  "block h-full",
                  app.budgetUsed > 0.8 ? "bg-warning" : "bg-success",
                )}
                style="width:{Math.round(app.budgetUsed * 100)}%"
              ></span></span
            >
            <span class="text-muted-foreground num text-sm"
              >{Math.round(app.budgetUsed * 100)}% used today</span
            >
          </span>
        </dd>
        <dt class="text-muted-foreground">Network</dt>
        <dd>{app.network}</dd>
        <dt class="text-muted-foreground">Circuit breaker</dt>
        <dd>{app.breaker}</dd>
        {#if app.ops.length}
          <dt class="text-muted-foreground">May call</dt>
          <dd class="font-mono text-sm">{app.ops.join(", ")}</dd>
        {/if}
      </dl>
    </section>

    <section>
      <h3 class="mb-2 text-lg font-semibold">Latest from its log</h3>
      <ul class="well rounded-xl px-4 py-3 font-mono text-sm">
        {#each app.log as l, i (i)}<li class="py-0.5">{l}</li>{/each}
      </ul>
    </section>
  </div>

  <footer class="flex flex-wrap gap-2 border-t px-6 py-4">
    {#if app.panels?.length}
      <Button href={resolve("/apps/[id]", { id: app.id })}
        ><AppWindow />Open it</Button
      >
    {/if}
    {#if app.kind !== "screens" && app.stage === 4 && app.health !== "tripped"}
      <Button variant="outline" onclick={() => need(`Running ${app.name}`)}
        ><Play />Run now</Button
      >
      <Button variant="outline" onclick={() => need(`Pausing ${app.name}`)}
        ><Pause />Pause</Button
      >
    {/if}
    <!-- eslint-disable svelte/no-navigation-without-resolve -->
    <Button
      variant="outline"
      href={ask(
        app.stage < 4
          ? `What is left before ${app.name} can go live?`
          : `Change ${app.name}: `,
      )}><MessagesSquare />Ask the copilot</Button
    >
    <!-- eslint-enable svelte/no-navigation-without-resolve -->
    {#if mine}
      <Button
        variant="ghost"
        class="ml-auto"
        onclick={() => apps.remove(app.id)}><Trash2 />Remove</Button
      >
    {/if}
  </footer>
</article>
