<script lang="ts">
  /**
   * About this app, one level below the tiles: where it is on its road to
   * live, the box it runs in, who signs for it, and its latest log lines.
   * Opens for whichever app `apps.selected` names.
   */
  import AppWindow from "@lucide/svelte/icons/app-window";
  import MessagesSquare from "@lucide/svelte/icons/messages-square";
  import Play from "@lucide/svelte/icons/play";
  import RotateCcw from "@lucide/svelte/icons/rotate-ccw";
  import Star from "@lucide/svelte/icons/star";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import { resolve } from "$app/paths";
  import * as Dialog from "$lib/components/ui/dialog";
  import { Button } from "$lib/components/ui/button";
  import { Switch } from "$lib/components/ui/switch";
  import { cn } from "$lib/utils";
  import InfoTip from "$lib/workbench/InfoTip.svelte";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { RISK, STATUS, STEPS, apps } from "./apps.svelte";
  import { ICONS } from "./icons";
  import { GROUP_TINT } from "./tint";

  /** True on the app's own screen, where Open would go nowhere. */
  let { opened = false }: { opened?: boolean } = $props();

  const app = $derived(apps.byId(apps.selected));
  const mine = $derived(apps.mine.some((a) => a.id === app?.id));
  const ask = (q: string) =>
    resolve("/copilot") + "?ask=" + encodeURIComponent(q);
</script>

<Dialog.Root
  open={Boolean(app)}
  onOpenChange={(o) => {
    if (!o) apps.selected = null;
  }}
>
  <Dialog.Content
    class="data-open:slide-in-from-right-8 top-0 right-0 left-auto flex h-full max-h-none w-[min(34rem,100vw)] max-w-none translate-x-0 translate-y-0 flex-col gap-0 rounded-none p-0 text-base sm:max-w-none"
  >
    {#if app}
      {@const status = apps.status(app)}
      {@const Icon = ICONS[app.icon]}
      {@const pinned = apps.pinned(app.id)}
      <header class="flex items-center gap-4 border-b px-6 py-5 pr-16">
        <span
          class={cn(
            "flex size-12 shrink-0 items-center justify-center rounded-2xl",
            GROUP_TINT[app.group],
          )}><Icon class="size-6" /></span
        >
        <div class="min-w-0 flex-1">
          <Dialog.Title class="truncate text-2xl font-semibold"
            >{app.name}</Dialog.Title
          >
          <Dialog.Description
            class="text-muted-foreground flex items-center gap-1.5 text-base"
          >
            <span class={cn("size-2 shrink-0 rounded-full", STATUS[status].dot)}
            ></span>
            <span class="truncate"
              >{status === "off" ? STATUS.off.label : app.stageNote}</span
            >
          </Dialog.Description>
        </div>
        <Switch
          checked={app.on && !apps.safe}
          disabled={apps.safe}
          onCheckedChange={(v) => apps.toggle(app.id, v)}
          aria-label={`Turn ${app.name} on`}
        />
      </header>

      <div class="flex min-h-0 flex-1 flex-col gap-group overflow-auto p-6">
        {#if status === "stopped"}
          <section class="border-destructive/50 rounded-2xl border p-panel">
            <p>{app.stopped}</p>
            <div class="mt-3 flex flex-wrap gap-2">
              <Button onclick={() => apps.restart(app.id)}
                ><RotateCcw />Restart</Button
              >
              <!-- eslint-disable svelte/no-navigation-without-resolve -->
              <Button
                variant="outline"
                href={ask(`Why did ${app.name} stop itself?`)}
                ><MessagesSquare />Ask why</Button
              >
              <!-- eslint-enable svelte/no-navigation-without-resolve -->
            </div>
          </section>
        {/if}

        <section>
          <div class="mb-3 flex items-center gap-1">
            <h3 class="text-lg font-semibold">Road to live</h3>
            <InfoTip label="What each step proved">
              <ol class="flex flex-col gap-1">
                {#each STEPS as s, k (s)}
                  <li>
                    <span class="font-medium">{s}:</span>
                    {app.evidence[k] ?? "not yet"}
                  </li>
                {/each}
              </ol>
            </InfoTip>
          </div>
          <ol class="grid grid-cols-5 gap-1.5">
            {#each STEPS as s, k (s)}
              {@const done = k < app.stage || app.stage === 4}
              {@const now = k === app.stage && app.stage < 4}
              <li class="flex min-w-0 flex-col gap-1.5">
                <span
                  class={cn(
                    "h-1.5 rounded-full",
                    done ? "bg-success" : now ? "bg-info" : "bg-muted",
                  )}
                ></span>
                <span
                  class={cn(
                    "text-sm leading-tight",
                    !done && !now && "text-muted-foreground",
                    now && "font-medium",
                  )}>{s}</span
                >
              </li>
            {/each}
          </ol>
        </section>

        <section>
          <h3 class="mb-2 text-lg font-semibold">Its box</h3>
          <dl class="grid grid-cols-[8.5rem_1fr] gap-x-4">
            <dt class="text-muted-foreground py-row">Runs on</dt>
            <dd class="py-row">{app.runsOn}</dd>
            <dt class="text-muted-foreground py-row">Budget today</dt>
            <dd class="flex items-center gap-3 py-row">
              <span class="bg-muted h-2 flex-1 overflow-hidden rounded-full"
                ><span
                  class={cn(
                    "block h-full",
                    app.budgetUsed > 0.8 ? "bg-warning" : "bg-success",
                  )}
                  style="width:{Math.round(app.budgetUsed * 100)}%"
                ></span></span
              >
              <span class="num text-sm"
                >{Math.round(app.budgetUsed * 100)}%</span
              >
              <InfoTip label="Its budget" text={app.budget} />
            </dd>
            <dt class="text-muted-foreground py-row">Network</dt>
            <dd class="py-row">{app.network}</dd>
            <dt class="text-muted-foreground py-row">Breaker</dt>
            <dd class="py-row">{app.breaker}</dd>
            <dt class="text-muted-foreground py-row">Approval</dt>
            <dd class="flex items-center gap-1 py-row">
              <span class={cn(app.risk === "money" && "text-warning")}
                >{RISK[app.risk].label}</span
              >
              <InfoTip label="How it goes live" text={RISK[app.risk].rule} />
            </dd>
          </dl>
        </section>

        <section>
          <h3 class="mb-2 text-lg font-semibold">Log</h3>
          <ul class="well rounded-xl px-4 py-3 font-mono text-sm">
            {#each app.log.slice(0, 4) as l, i (i)}<li class="py-0.5">
                {l}
              </li>{/each}
          </ul>
        </section>
      </div>

      <footer class="flex flex-wrap gap-2 border-t px-6 py-4">
        {#if app.panels?.length && !opened}
          <Button href={resolve("/apps/[id]", { id: app.id })}
            ><AppWindow />Open</Button
          >
        {/if}
        {#if app.kind !== "screens" && status === "live"}
          <Button
            variant="outline"
            onclick={() =>
              workbench.notify(`Running ${app.name} needs the daemon.`)}
            ><Play />Run now</Button
          >
        {/if}
        <Button
          variant="outline"
          aria-pressed={pinned}
          onclick={() => apps.pin(app.id)}
          ><Star class={cn(pinned && "fill-primary text-primary")} />{pinned
            ? "Pinned"
            : "Pin"}</Button
        >
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
    {/if}
  </Dialog.Content>
</Dialog.Root>
