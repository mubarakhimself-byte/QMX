<script lang="ts">
  /**
   * When the copilot is waiting on you, the answer takes over the message
   * box (T3 Code's pending-approval panel; DeepSeek Harness's approvals that
   * say no unless allowed). You can still choose to write instead.
   */
  import CircleHelp from "@lucide/svelte/icons/circle-help";
  import ShieldCheck from "@lucide/svelte/icons/shield-check";
  import { Button } from "$lib/components/ui/button";
  import type { Block } from "./demo";

  let {
    block,
    onanswer,
    onwrite,
  }: {
    block: Block;
    onanswer: (value: string) => void;
    onwrite: () => void;
  } = $props();
</script>

<div
  class="surface border-primary/50 flex flex-col gap-2 rounded-xl border p-3"
>
  {#if block.kind === "ask"}
    <p class="flex items-center gap-2 text-sm font-medium">
      <CircleHelp class="text-warning size-4" />{block.question}
    </p>
    <div class="flex flex-wrap gap-1.5">
      {#each block.options as o (o.label)}
        <Button
          size="sm"
          variant={o.recommended ? "default" : "outline"}
          title={o.note}
          onclick={() => onanswer(o.label)}>{o.label}</Button
        >
      {/each}
      <Button size="sm" variant="ghost" class="ml-auto" onclick={onwrite}
        >Write an answer</Button
      >
    </div>
  {:else if block.kind === "permission"}
    <p class="flex items-center gap-2 text-sm font-medium">
      <ShieldCheck class="text-primary size-4" />Needs your yes: {block.action}
    </p>
    <p class="text-muted-foreground text-[13px]">{block.guard}</p>
    <div class="flex flex-wrap gap-1.5">
      <Button size="sm" onclick={() => onanswer("Allowed once")}>Allow</Button>
      <Button
        size="sm"
        variant="outline"
        onclick={() => onanswer("Allowed for the rest of this session")}
        >Allow for this session</Button
      >
      <Button
        size="sm"
        variant="ghost"
        onclick={() => onanswer("Not now; it will ask again later")}
        >Not now</Button
      >
      <Button size="sm" variant="ghost" class="ml-auto" onclick={onwrite}
        >Write instead</Button
      >
    </div>
  {/if}
</div>
