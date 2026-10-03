<script lang="ts">
  import { goto } from "$app/navigation";
  import { resolve } from "$app/paths";
  import Paperclip from "@lucide/svelte/icons/paperclip";
  import ArrowUp from "@lucide/svelte/icons/arrow-up";
  import Wrench from "@lucide/svelte/icons/wrench";
  import X from "@lucide/svelte/icons/x";
  import ChevronDown from "@lucide/svelte/icons/chevron-down";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import LayoutPanelTop from "@lucide/svelte/icons/layout-panel-top";
  import AtSign from "@lucide/svelte/icons/at-sign";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu";
  import { Button } from "$lib/components/ui/button";
  import { workbench, MODELS } from "./workbench.svelte";
  import { MAIN_CONTEXT, type CopilotContext } from "./copilot-context";
  import { cn } from "$lib/utils";
  import LibraryPicker from "$lib/library/LibraryPicker.svelte";
  import AimMenu from "$lib/copilot/AimMenu.svelte";
  import { COMMANDS } from "$lib/copilot/demo";

  let {
    placeholder = "Ask the copilot…",
    label = "Message",
    refs = [],
    onremoveref,
    size = "md",
    context = MAIN_CONTEXT,
    seed = "",
  }: {
    placeholder?: string;
    label?: string;
    /** Context chips added from widgets (message-only, not durable refs). */
    refs?: string[];
    onremoveref?: (ref: string) => void;
    size?: "md" | "lg";
    /** Tools, targets and attach sources for this surface. */
    context?: CopilotContext;
    /** Text placed in the box when a suggestion is picked. */
    seed?: string;
  } = $props();

  let draft = $state("");
  let picking = $state(false);
  $effect(() => {
    if (seed) draft = seed;
  });
  // Send goes through dispatchChat once a transport is bound; never faked.
  const online = $derived(workbench.connection === "connected");
  const model = $derived(
    MODELS.find((m) => m.id === workbench.model) ?? MODELS[0],
  );
  const isMain = $derived(context.id === "main");
  // The main copilot keeps its choices in the workbench; other surfaces keep their own.
  // svelte-ignore state_referenced_locally
  let localTools = $state<string[]>([...context.defaultTools]);
  let localTarget = $state<string | null>(null);
  const tools = $derived(isMain ? workbench.tools : localTools);
  const targetId = $derived(isMain ? workbench.target : localTarget);
  const target = $derived(context.targets?.find((t) => t.id === targetId));
  function toggleTool(id: string) {
    if (isMain) workbench.toggleTool(id);
    else
      localTools = localTools.includes(id)
        ? localTools.filter((t) => t !== id)
        : [...localTools, id];
  }
  function setTarget(id: string | null) {
    if (isMain) workbench.target = id as typeof workbench.target;
    else localTarget = id;
  }
  // Typing "/" offers the commands.
  const slash = $derived(
    /^\/\w*$/.test(draft)
      ? COMMANDS.filter((c) => c.cmd.startsWith(draft.toLowerCase()))
      : [],
  );
  const groups = $derived([
    ...new Set(context.tools.map((t) => t.group ?? "")),
  ]);
  const iconChip =
    "text-muted-foreground hover:text-foreground hover:bg-muted data-[state=open]:bg-muted relative flex size-7 shrink-0 items-center justify-center rounded-md";
  const badge =
    "bg-primary text-primary-foreground num absolute -top-0.5 -right-0.5 flex h-3.5 min-w-3.5 items-center justify-center rounded-full px-0.5 text-[9px] leading-none";
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
  {#if slash.length}
    <ul class="border-b px-1.5 py-1.5" role="listbox" aria-label="Commands">
      {#each slash as c (c.cmd)}
        <li>
          <button
            type="button"
            role="option"
            aria-selected="false"
            class="hover:bg-muted flex w-full items-baseline gap-3 rounded-md px-2 py-1 text-left"
            onclick={() => (draft = `${c.cmd} `)}
          >
            <span class="font-mono text-[13px]">{c.cmd}</span>
            <span class="text-muted-foreground text-xs">{c.note}</span>
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
    {#if context.attach}
      <DropdownMenu.Root>
        <DropdownMenu.Trigger
          class={iconChip}
          aria-label={`Attach${refs.length ? `, ${refs.length} attached` : ""}`}
          title="Attach"
        >
          <Paperclip class="size-4" />
          {#if refs.length}<span class={badge}>{refs.length}</span>{/if}
        </DropdownMenu.Trigger>
        <DropdownMenu.Content align="start" class="w-64">
          {#each context.attach as a (a.id)}
            <DropdownMenu.Item
              disabled={!!a.needs}
              onclick={() => {
                if (a.id === "library") picking = true;
                else if (a.href) goto(resolve(a.href as "/library"));
                else
                  workbench.notify(
                    `${a.label}: pick it on screen; it joins this message.`,
                  );
              }}
            >
              <a.icon />
              <span class="flex min-w-0 flex-col">
                <span>{a.label}</span>
                {#if a.note}<span class="text-muted-foreground text-xs"
                    >{a.note}</span
                  >{/if}
              </span>
              {#if a.needs}<span
                  class="text-muted-foreground ml-auto text-xs whitespace-nowrap"
                  >{a.needs}</span
                >{/if}
            </DropdownMenu.Item>
          {/each}
        </DropdownMenu.Content>
      </DropdownMenu.Root>
    {/if}

    {#if isMain}
      <AimMenu />
    {:else if context.targets}
      <DropdownMenu.Root>
        <DropdownMenu.Trigger
          class={target ? chip : iconChip}
          aria-label={`Target: ${target?.name ?? "copilot decides"}`}
          title="Aim this message at"
        >
          <AtSign class="size-4" />
          {#if target}<span class="max-w-24 truncate">{target.name}</span>{/if}
        </DropdownMenu.Trigger>
        <DropdownMenu.Content align="start" class="w-80">
          <DropdownMenu.Label>Aim this message at</DropdownMenu.Label>
          <DropdownMenu.RadioGroup
            value={targetId ?? ""}
            onValueChange={(v) => setTarget(v || null)}
          >
            <DropdownMenu.RadioItem value="" closeOnSelect>
              <span class="flex flex-col"
                ><span>Let the copilot decide</span><span
                  class="text-muted-foreground text-xs"
                  >It picks from what you have granted</span
                ></span
              >
            </DropdownMenu.RadioItem>
            {#each context.targets as t (t.id)}
              <DropdownMenu.RadioItem
                value={t.id}
                closeOnSelect
                disabled={!!t.blocked && t.blocked !== "not granted"}
              >
                <span class="flex min-w-0 flex-col">
                  <span class="flex items-center gap-2"
                    >{t.name}<span class="text-muted-foreground text-xs"
                      >{t.kind}</span
                    ></span
                  >
                  <span class="text-muted-foreground truncate text-xs"
                    >{t.note}</span
                  >
                  <span
                    class={cn(
                      "text-xs",
                      t.blocked ? "text-warning" : "text-success",
                    )}>{t.blocked ? `Can't use: ${t.blocked}` : "Ready"}</span
                  >
                </span>
              </DropdownMenu.RadioItem>
            {/each}
          </DropdownMenu.RadioGroup>
        </DropdownMenu.Content>
      </DropdownMenu.Root>
    {/if}

    <DropdownMenu.Root>
      <DropdownMenu.Trigger
        class={iconChip}
        aria-label={`Tools, ${tools.length} on`}
        title="Tools"
      >
        <Wrench class="size-4" />
        <span class={badge}>{tools.length}</span>
      </DropdownMenu.Trigger>
      <DropdownMenu.Content align="start" class="max-h-96 w-72 overflow-auto">
        <DropdownMenu.Label>Tools the copilot may use here</DropdownMenu.Label>
        {#each groups as g (g)}
          {#if g}<DropdownMenu.Label
              class="text-muted-foreground pt-2 text-xs font-normal"
              >{g}</DropdownMenu.Label
            >{/if}
          {#each context.tools.filter((t) => (t.group ?? "") === g) as t (t.id)}
            <DropdownMenu.CheckboxItem
              checked={tools.includes(t.id)}
              onCheckedChange={() => toggleTool(t.id)}
              closeOnSelect={false}
            >
              <span class="flex flex-col">
                <span class="font-mono text-[13px]"
                  >{t.id}{#if t.scope === "new"}<span
                      class="text-muted-foreground ml-1.5 font-sans text-[11px]"
                      >new scope</span
                    >{/if}</span
                >
                <span class="text-muted-foreground text-xs">{t.note}</span>
              </span>
            </DropdownMenu.CheckboxItem>
          {/each}
        {/each}
      </DropdownMenu.Content>
    </DropdownMenu.Root>

    <div class="ml-auto flex items-center gap-1">
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
        aria-label={online ? "Send" : "Send (needs the daemon)"}
        title={online ? "Send" : "Sending needs a connection to the QMX daemon"}
        disabled={!online || !draft.trim()}
      >
        <ArrowUp />
      </Button>
    </div>
  </div>
</form>

<LibraryPicker
  bind:open={picking}
  onpick={(name) => workbench.addRef(name, true)}
/>
