<script lang="ts">
  /** The mode-and-reach chip in the main composer (replaces the old target menu). */
  import ChevronDown from "@lucide/svelte/icons/chevron-down";
  import Lock from "@lucide/svelte/icons/lock";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu";
  import { cn } from "$lib/utils";
  import { ANSWERERS, MODES, REACH, aim } from "./aim.svelte";

  const mode = $derived(MODES.find((m) => m.id === aim.mode)!);
  const answerer = $derived(ANSWERERS.find((a) => a.id === aim.answerer)!);
  const summary = $derived(
    aim.mode === "ask"
      ? "reads only"
      : `${aim.reach.length} of ${REACH.length} areas`,
  );
</script>

<DropdownMenu.Root>
  <DropdownMenu.Trigger
    class="text-muted-foreground hover:text-foreground hover:bg-muted data-[state=open]:bg-muted flex h-7 shrink-0 items-center gap-1.5 rounded-md px-2 text-sm whitespace-nowrap"
    aria-label={`${mode.label}, ${summary}, answered by ${answerer.label}`}
    title="How much it may do, what it may touch, and who answers"
  >
    <span
      class={cn(
        "rounded px-1.5 text-xs font-semibold",
        aim.mode === "do"
          ? "bg-primary text-primary-foreground"
          : aim.mode === "plan"
            ? "bg-info/20 text-info"
            : "bg-muted text-foreground",
      )}>{mode.label}</span
    >
    <span class="hidden sm:inline">{summary}</span>
    {#if aim.answerer !== "main"}<span class="max-w-28 truncate"
        >· {answerer.label}</span
      >{/if}
    <ChevronDown class="size-3.5" />
  </DropdownMenu.Trigger>
  <DropdownMenu.Content align="start" class="w-80">
    <DropdownMenu.Label>How much may it do?</DropdownMenu.Label>
    <div class="grid grid-cols-3 gap-1 px-2 pb-1" role="radiogroup">
      {#each MODES as m (m.id)}
        <button
          type="button"
          role="radio"
          aria-checked={aim.mode === m.id}
          class={cn(
            "rounded-md border px-2 py-1.5 text-sm",
            aim.mode === m.id
              ? "border-primary bg-primary/12 font-medium"
              : "hover:bg-muted",
          )}
          onclick={() => (aim.mode = m.id)}>{m.label}</button
        >
      {/each}
    </div>
    <p class="text-muted-foreground px-2 pb-2 text-xs">{mode.note}</p>
    <DropdownMenu.Separator />
    <DropdownMenu.Label>What may it touch?</DropdownMenu.Label>
    {#each REACH as r (r.id)}
      <DropdownMenu.CheckboxItem
        checked={aim.reach.includes(r.id)}
        onCheckedChange={() => aim.toggle(r.id)}
        closeOnSelect={false}
        disabled={aim.mode === "ask"}
      >
        <span class="flex flex-col"
          ><span>{r.label}</span><span class="text-muted-foreground text-xs"
            >{r.note}</span
          ></span
        >
      </DropdownMenu.CheckboxItem>
    {/each}
    <DropdownMenu.Item disabled class="opacity-100">
      <Lock class="text-muted-foreground" />
      <span class="flex flex-col"
        ><span>Real money</span><span class="text-muted-foreground text-xs"
          >Never: always your signature in Portfolio</span
        ></span
      >
    </DropdownMenu.Item>
    <DropdownMenu.Separator />
    <DropdownMenu.Label>Who answers?</DropdownMenu.Label>
    <DropdownMenu.RadioGroup
      value={aim.answerer}
      onValueChange={(v) => (aim.answerer = v)}
    >
      {#each ANSWERERS as a (a.id)}
        <DropdownMenu.RadioItem value={a.id} closeOnSelect={false}>
          <span class="flex flex-col"
            ><span>{a.label}</span><span class="text-muted-foreground text-xs"
              >{a.note}</span
            ></span
          >
        </DropdownMenu.RadioItem>
      {/each}
    </DropdownMenu.RadioGroup>
  </DropdownMenu.Content>
</DropdownMenu.Root>
