<script lang="ts">
  import Icon from "$lib/qmx/Icon.svelte";
  import { tone, stateLabel } from "$lib/qmx/state";
  import { things } from "$lib/shell/things.svelte";
  import { shell } from "$lib/shell/state.svelte";
  import type { Obj, ListKind } from "$lib/shell/model";

  // A thing as one row: its state, its name, where it runs. A click opens
  // its page. Used by every list, every board card and every "Linked" section.
  let { o, list, hint, on = false, slim = false }: { o: Obj; list?: ListKind; hint?: string; on?: boolean; slim?: boolean } = $props();
  const target = $derived(o.target ?? o.id);
</script>

<button
  class="pick group flex w-full min-w-0 items-start gap-3 rounded-md px-2.5 py-2 text-left"
  data-on={on}
  data-id={o.id}
  aria-current={on ? "page" : undefined}
  onclick={() => shell.open({ id: target, list })}
>
  <span class="dot mt-[0.5em] {tone[o.tone]}" title={stateLabel[o.tone]}></span>
  <span class="min-w-0 flex-1">
    <span class="text-foreground line-clamp-2 [overflow-wrap:anywhere]" title={o.name}>{o.name}</span>
    {#if !slim && (o.line || o.where)}
      <span class="text-muted-foreground mt-0.5 flex min-w-0 items-center gap-1.5 text-sm">
        {#if o.where}
          <Icon name={o.where === "This PC" ? "laptop" : "server"} class="size-3.5 shrink-0" />
          <span class="max-w-[50%] shrink-0 truncate" title={o.where}>{o.where}</span>
          {#if o.line}<span aria-hidden="true">·</span>{/if}
        {/if}
        {#if o.line}<span class="min-w-0 truncate" title={o.line}>{o.line}</span>{/if}
      </span>
    {/if}
  </span>
  {#if !slim}
    <span class="flex shrink-0 flex-col items-end gap-0.5 text-sm">
      <span class="{tone[o.tone]} whitespace-nowrap">{hint ?? o.word}</span>
      {#if o.when}<span class="text-muted-foreground num whitespace-nowrap">{o.when}</span>{/if}
    </span>
  {/if}
</button>
