<script lang="ts">
  import { goto } from "$app/navigation";
  import { resolve } from "$app/paths";
  import Paperclip from "@lucide/svelte/icons/paperclip";
  import ArrowUp from "@lucide/svelte/icons/arrow-up";
  import Wrench from "@lucide/svelte/icons/wrench";
  import WifiOff from "@lucide/svelte/icons/wifi-off";
  import X from "@lucide/svelte/icons/x";
  import ChevronDown from "@lucide/svelte/icons/chevron-down";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import LibraryBig from "@lucide/svelte/icons/library-big";
  import Upload from "@lucide/svelte/icons/upload";
  import LayoutPanelTop from "@lucide/svelte/icons/layout-panel-top";
  import AtSign from "@lucide/svelte/icons/at-sign";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu";
  import { Button } from "$lib/components/ui/button";
  import { workbench, MODELS, TOOLS, TARGETS } from "./workbench.svelte";
  import { cn } from "$lib/utils";

  let {
    placeholder = "Ask the copilot…",
    label = "Message",
    refs = [],
    onremoveref,
    size = "md",
  }: {
    placeholder?: string;
    label?: string;
    /** Context chips added from widgets (message-only, not durable refs). */
    refs?: string[];
    onremoveref?: (ref: string) => void;
    size?: "md" | "lg";
  } = $props();

  let draft = $state("");
  // Send goes through dispatchChat once a transport is bound; never faked.
  const online = $derived(workbench.connection === "connected");
  const model = $derived(
    MODELS.find((m) => m.id === workbench.model) ?? MODELS[0],
  );
  const toolCount = $derived(workbench.tools.length);
  const target = $derived(TARGETS.find((t) => t.id === workbench.target));
  const AXES = [
    "published",
    "configured",
    "granted",
    "reachable",
    "healthy",
  ] as const;
  /** Where a target falls short, in plain words. */
  function gap(t: (typeof TARGETS)[number]): string | null {
    const missing = AXES.find((a) => !t.axes[a]);
    return missing ? `not ${missing}` : null;
  }
  const chip =
    "text-muted-foreground hover:text-foreground hover:bg-muted data-[state=open]:bg-muted flex h-7 shrink-0 items-center gap-1.5 rounded-md px-2 text-[13px] whitespace-nowrap";
</script>

<form
  class="surface focus-within:border-ring/50 flex flex-col rounded-xl transition-colors"
  onsubmit={(e) => e.preventDefault()}
>
  {#if refs.length}
    <ul class="flex flex-wrap gap-1.5 px-3 pt-3" aria-label="Context">
      {#each refs as ref (ref)}
        <li
          class="bg-muted flex h-7 items-center gap-1.5 rounded-md pr-1 pl-2 text-[13px]"
        >
          <LayoutPanelTop class="text-muted-foreground size-3.5" />
          <span class="max-w-64 truncate">{ref}</span>
          <button
            type="button"
            class="hover:bg-background/50 rounded-sm p-0.5"
            aria-label={`Remove ${ref}`}
            onclick={() => onremoveref?.(ref)}
          >
            <X class="size-3.5" />
          </button>
        </li>
      {/each}
    </ul>
  {/if}
  <label class="sr-only" for="composer-input">{label}</label>
  <textarea
    id="composer-input"
    bind:value={draft}
    rows={1}
    {placeholder}
    onkeydown={(e) => {
      // Enter sends, Shift+Enter adds a line (send is gated while offline).
      if (e.key === "Enter" && !e.shiftKey) e.preventDefault();
    }}
    class={cn(
      // Grows with its content up to a cap, then scrolls; the form owns focus styling.
      "placeholder:text-muted-foreground field-sizing-content resize-none overflow-y-auto bg-transparent px-3.5 pt-3 outline-none focus-visible:ring-0 focus-visible:ring-offset-0",
      size === "lg"
        ? "max-h-80 min-h-20 text-base"
        : "max-h-56 min-h-12 text-[15px]",
    )}></textarea>
  <div class="flex items-center gap-0.5 px-2 pb-2">
    <DropdownMenu.Root>
      <DropdownMenu.Trigger class={chip} aria-label="Attach">
        <Paperclip class="size-4" /> Attach
      </DropdownMenu.Trigger>
      <DropdownMenu.Content align="start" class="w-60">
        <DropdownMenu.Item onclick={() => goto(resolve("/library"))}>
          <LibraryBig /> From Library…
        </DropdownMenu.Item>
        <DropdownMenu.Item disabled>
          <Upload /> Upload a file
          <span class="text-muted-foreground ml-auto text-xs">needs daemon</span
          >
        </DropdownMenu.Item>
        <DropdownMenu.Separator />
        <DropdownMenu.Label class="text-muted-foreground text-xs font-normal">
          Use the message-plus icon on any widget to attach it.
        </DropdownMenu.Label>
      </DropdownMenu.Content>
    </DropdownMenu.Root>

    <DropdownMenu.Root>
      <DropdownMenu.Trigger
        class={chip}
        aria-label={`Target: ${target?.name ?? "copilot decides"}`}
      >
        <AtSign class="size-4" />
        {target?.name ?? "Target"}
      </DropdownMenu.Trigger>
      <DropdownMenu.Content align="start" class="w-80">
        <DropdownMenu.Label>Aim this message at</DropdownMenu.Label>
        <DropdownMenu.RadioGroup
          value={workbench.target ?? ""}
          onValueChange={(v) =>
            (workbench.target = (v || null) as typeof workbench.target)}
        >
          <DropdownMenu.RadioItem value="" closeOnSelect>
            <span class="flex flex-col"
              ><span>Let the copilot decide</span><span
                class="text-muted-foreground text-xs"
                >It picks from what you have granted</span
              ></span
            >
          </DropdownMenu.RadioItem>
          {#each TARGETS as t (t.id)}
            {@const g = gap(t)}
            <DropdownMenu.RadioItem
              value={t.id}
              closeOnSelect
              disabled={!!g && g !== "not granted"}
            >
              <span class="flex min-w-0 flex-col">
                <span class="flex items-center gap-2"
                  >{t.name}<span class="text-muted-foreground text-xs"
                    >{t.kind}</span
                  ></span
                >
                <span
                  class="text-muted-foreground truncate font-mono text-[11px]"
                  >{t.ops.join(" · ")}</span
                >
                <span class={cn("text-xs", g ? "text-warning" : "text-success")}
                  >{g ? `Can't use: ${g}` : "Ready"}</span
                >
              </span>
            </DropdownMenu.RadioItem>
          {/each}
        </DropdownMenu.RadioGroup>
      </DropdownMenu.Content>
    </DropdownMenu.Root>

    <DropdownMenu.Root>
      <DropdownMenu.Trigger class={chip} aria-label={`Tools, ${toolCount} on`}>
        <Wrench class="size-4" /> Tools
        <span class="num text-xs opacity-70">{toolCount}</span>
      </DropdownMenu.Trigger>
      <DropdownMenu.Content align="start" class="w-64">
        <DropdownMenu.Label>Tools the copilot may use</DropdownMenu.Label>
        {#each TOOLS as t (t.id)}
          <DropdownMenu.CheckboxItem
            checked={workbench.tools.includes(t.id)}
            onCheckedChange={() => workbench.toggleTool(t.id)}
            closeOnSelect={false}
          >
            <span class="flex flex-col">
              <span class="font-mono text-[13px]">{t.id}</span>
              <span class="text-muted-foreground text-xs">{t.note}</span>
            </span>
          </DropdownMenu.CheckboxItem>
        {/each}
      </DropdownMenu.Content>
    </DropdownMenu.Root>

    <div class="ml-auto flex items-center gap-1">
      {#if !online}
        <span
          class="text-muted-foreground flex items-center gap-1 px-1 text-xs"
          title="Sending needs a connection to the QMX daemon."
        >
          <WifiOff class="size-3.5" /> Offline
        </span>
      {/if}
      <DropdownMenu.Root>
        <DropdownMenu.Trigger class={chip} aria-label={`Model: ${model.label}`}>
          <Sparkles class="size-4" />
          {model.label}
          <ChevronDown class="size-3.5" />
        </DropdownMenu.Trigger>
        <DropdownMenu.Content align="end" class="w-64">
          <DropdownMenu.Label>Model</DropdownMenu.Label>
          <DropdownMenu.RadioGroup
            value={workbench.model}
            onValueChange={(v) => (workbench.model = v)}
          >
            {#each MODELS as m (m.id)}
              <DropdownMenu.RadioItem value={m.id} closeOnSelect>
                <span class="flex flex-col">
                  <span>{m.label}</span>
                  <span class="text-muted-foreground text-xs">{m.note}</span>
                </span>
              </DropdownMenu.RadioItem>
            {/each}
          </DropdownMenu.RadioGroup>
          <DropdownMenu.Separator />
          <DropdownMenu.Label class="text-muted-foreground text-xs font-normal">
            Providers are configured by the daemon.
          </DropdownMenu.Label>
        </DropdownMenu.Content>
      </DropdownMenu.Root>
      <Button
        type="submit"
        size="icon-sm"
        aria-label={online ? "Send" : "Send (offline)"}
        disabled={!online || !draft.trim()}
      >
        <ArrowUp />
      </Button>
    </div>
  </div>
</form>
