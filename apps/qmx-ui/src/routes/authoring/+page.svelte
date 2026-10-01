<script lang="ts">
  import { Button } from "$lib/components/ui/button";
</script>

<svelte:head>
  <title>Authoring</title>
</svelte:head>

<main
  class="flex flex-col gap-4 p-6"
  data-testid="destination-authoring"
  data-profile="authoring"
>
  <p class="text-muted-foreground text-xs tracking-wide uppercase">Authoring</p>
  <h1 class="text-xl font-medium">Graph / code / detail</h1>
  <p data-testid="authoring-purpose">
    Independently reachable with zero apps open. Profile authoring. Headless
    packs stay first-class and do not acquire a navigation pane here.
  </p>
  <section
    class="bg-surface border-border flex min-h-48 flex-col gap-2 rounded-lg border p-4"
    data-testid="authoring-empty"
    data-state="empty"
  >
    <p>Blank graph. Save creates a daemon-issued id when drafts exist.</p>
    <p
      class="text-muted-foreground text-sm"
      data-testid="authoring-expand-copy"
    >
      Expand/return is WidgetFrame layout, not a fifth rail destination.
    </p>
    <Button size="sm" variant="outline" data-testid="authoring-save" disabled>
      Save draft
    </Button>
  </section>
</main>
