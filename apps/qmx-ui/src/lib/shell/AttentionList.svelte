<script lang="ts">
  import { resolve } from "$app/paths";
  import { Badge } from "$lib/components/ui/badge";
  import { Button } from "$lib/components/ui/button";
  import { Skeleton } from "$lib/components/ui/skeleton";
  import type { AttentionRow, HomeChromeState } from "$lib/screens/homeState";

  let {
    chromeState,
    rows,
    copy,
    onResume,
    onCancel,
  }: {
    chromeState: HomeChromeState;
    rows: AttentionRow[];
    copy: string;
    onResume: (target: string) => void;
    onCancel: (row: AttentionRow) => void;
  } = $props();
</script>

<section
  class="bg-surface border-border flex flex-col gap-3 rounded-lg border p-4"
  data-testid="home-attention-list"
  data-state={chromeState}
>
  {#if chromeState === "loading"}
    <Skeleton class="h-4 w-2/3" data-testid="home-attention-skeleton" />
    <Skeleton class="h-4 w-1/2" />
    <p data-testid="home-copy">{copy}</p>
  {:else if chromeState === "empty"}
    <div data-testid="home-empty" data-state="empty">
      <p data-testid="home-empty-action">{copy}</p>
      <div class="mt-3 flex flex-wrap gap-2">
        <Button href={resolve("/copilot")} data-testid="home-start-copilot"
          >Start Copilot</Button
        >
        <Button
          href={resolve("/authoring")}
          variant="outline"
          data-testid="home-start-authoring">Start Authoring</Button
        >
      </div>
    </div>
  {:else if chromeState === "unavailable"}
    <div data-testid="home-unavailable">
      <p class="text-sm font-medium">Home</p>
      <p data-testid="home-copy">{copy}</p>
    </div>
  {:else}
    {#if chromeState === "stale"}
      <Badge variant="outline" data-testid="home-stale-badge">stale</Badge>
    {/if}
    {#if chromeState === "reconnecting"}
      <Badge variant="secondary" data-testid="home-reconnecting-badge"
        >reconnecting</Badge
      >
    {/if}
    {#if chromeState === "unknown"}
      <Badge
        variant="outline"
        data-testid="home-unknown-badge"
        data-painted-as-failed="false">unknown</Badge
      >
    {/if}
    {#if chromeState === "failed"}
      <Badge variant="destructive" data-testid="home-failed">failed</Badge>
    {/if}
    <p data-testid="home-copy">{copy}</p>
    {#each rows as row (row.id)}
      {#if row.kind === "job_handle"}
        <article
          class="border-border flex flex-col gap-2 rounded-md border p-3"
          data-testid="home-job-row"
          data-handle-id={row.id}
          data-job-state={row.jobState}
          data-painted-as-failed={String(row.paintedAsFailed)}
        >
          <div class="flex flex-wrap items-center gap-2">
            <p class="text-sm font-medium">{row.title}</p>
            <Badge
              variant={row.jobState === "failed" ? "destructive" : "outline"}
              data-testid="home-job-state"
              data-state={row.jobState}
            >
              {row.jobState}
            </Badge>
          </div>
          {#if row.refusalText}
            <p class="text-destructive text-sm" data-testid="home-job-refusal">
              {row.refusalText}
            </p>
          {/if}
          <div class="flex flex-wrap gap-2">
            {#if row.resumeTarget}
              <Button
                size="sm"
                variant="outline"
                data-testid="home-resume"
                data-resume-target={row.resumeTarget}
                onclick={() => onResume(row.resumeTarget ?? row.id)}
              >
                Resume
              </Button>
            {/if}
            {#if row.originating_product_session_ref}
              <Button
                size="sm"
                variant="ghost"
                data-testid="home-cancel-job"
                data-emits="cancel_job"
                onclick={() => onCancel(row)}
              >
                Cancel job
              </Button>
            {/if}
          </div>
        </article>
      {:else if row.kind === "resume"}
        <article
          class="border-border flex flex-col gap-2 rounded-md border p-3"
          data-testid="home-resume-row"
          data-resume-target={row.resumeTarget}
        >
          <p class="text-sm font-medium">{row.title}</p>
          <Button
            size="sm"
            data-testid="home-resume"
            data-resume-target={row.resumeTarget}
            onclick={() => onResume(row.resumeTarget)}
          >
            Resume
          </Button>
        </article>
      {:else}
        <article
          class="border-border flex flex-col gap-1 rounded-md border p-3"
          data-testid="home-observation"
          data-fourth-product="false"
          data-cancel-authority="false"
          data-authorizes-live="false"
          data-hot-swap="false"
          data-command-target="false"
          data-auto-retry-unknown-blocked="false"
        >
          <p class="text-sm font-medium">{row.title}</p>
          <p class="text-muted-foreground text-sm">
            Observation only. Listing {row.observation.listingAxis}.
            {row.observation.diagnosis}. {row.observation.fencing}. Not a fourth
            product. Not cancel authority. Not live. Not hot-swap. Not a command
            target. Trading ticket chrome is GAP-0113.
          </p>
        </article>
      {/if}
    {/each}
  {/if}
</section>
