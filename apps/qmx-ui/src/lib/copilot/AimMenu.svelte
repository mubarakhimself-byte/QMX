<script lang="ts">
  /** The reach-and-answerer chip in the main composer. No modes: skills come through "/". */
  import ChevronDown from "@lucide/svelte/icons/chevron-down";
  import Lock from "@lucide/svelte/icons/lock";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu";
  import { ANSWERERS, REACH, aim } from "./aim.svelte";

  const answerer = $derived(ANSWERERS.find((a) => a.id === aim.answerer)!);
  const summary = $derived(`${aim.reach.length} of ${REACH.length} areas`);
</script>

<DropdownMenu.Root>
  <DropdownMenu.Trigger
    class="text-muted-foreground hover:text-foreground hover:bg-muted data-[state=open]:bg-muted flex h-7 shrink-0 items-center gap-1.5 rounded-md px-2 text-sm whitespace-nowrap"
    aria-label={`May touch ${summary}, answered by ${answerer.label}`}
    title="What it may touch and who answers"
  >
    <span>{summary}</span>
    {#if aim.answerer !== "main"}<span class="max-w-28 truncate"
        >· {answerer.label}</span
      >{/if}
    <ChevronDown class="size-3.5" />
  </DropdownMenu.Trigger>
  <DropdownMenu.Content align="start" class="w-80">
    <DropdownMenu.Label>What may it touch?</DropdownMenu.Label>
    {#each REACH as r (r.id)}
      <DropdownMenu.CheckboxItem
        checked={aim.reach.includes(r.id)}
        onCheckedChange={() => aim.toggle(r.id)}
        closeOnSelect={false}
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
