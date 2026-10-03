<script lang="ts">
  /**
   * Requests from agents (QMA approval_request). Separate from promotion:
   * approving admits or applies something, it never promotes (DEC-0345).
   * Anything touching money rules arrives with a field-by-field diff.
   */
  import Bot from "@lucide/svelte/icons/bot";
  import { Button } from "$lib/components/ui/button";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { APPROVALS } from "../demo";
</script>

<ul class="h-full overflow-auto">
  {#each APPROVALS as a (a.id)}
    <li class="border-b border-border/50 px-3 py-2.5">
      <div class="flex items-start gap-2">
        <Bot class="text-muted-foreground mt-0.5 size-4 shrink-0" />
        <div class="min-w-0 flex-1">
          <p class="text-sm">{a.what}</p>
          <p class="text-muted-foreground text-xs">
            {a.from} · {a.when}{a.moneyPath ? " · touches money rules" : ""}
          </p>
        </div>
      </div>
      {#if a.diff}
        <table class="mt-2 ml-6 text-xs">
          <tbody>
            {#each a.diff as [field, from, to] (field)}
              <tr>
                <td class="text-muted-foreground pr-3">{field}</td>
                <td class="num text-destructive pr-2 line-through">{from}</td>
                <td class="num text-success">{to}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      {/if}
      <div class="mt-2 ml-6 flex gap-1.5">
        <Button
          size="sm"
          class="h-7"
          onclick={() =>
            workbench.notify(
              "Approving needs the daemon. If it changes money rules, the new version still needs a demo run and your signature before live.",
            )}>Approve</Button
        >
        <Button
          size="sm"
          variant="ghost"
          class="h-7"
          onclick={() => workbench.notify("Declined. The agent is told why.")}
          >Decline</Button
        >
        <Button
          size="sm"
          variant="ghost"
          class="h-7"
          onclick={() => workbench.addRef(a.what)}>Ask the copilot</Button
        >
      </div>
    </li>
  {/each}
</ul>
