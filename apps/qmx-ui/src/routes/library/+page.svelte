<script lang="ts">
  import { Button } from "$lib/components/ui/button";
</script>

<svelte:head>
  <title>Library</title>
</svelte:head>

<main class="flex flex-col gap-4 p-6" data-testid="destination-library">
  <p class="text-muted-foreground text-xs tracking-wide uppercase">Library</p>
  <h1 class="text-xl font-medium">Typed hits</h1>
  <p data-testid="library-purpose">
    One chrome over knowledge, artifact, and contribution hits. Must not
    collapse kinds. Reachable with zero opened apps.
  </p>
  <section
    class="bg-surface border-border grid gap-3 rounded-lg border p-4 md:grid-cols-3"
    data-testid="library-empty"
    data-state="empty"
  >
    <div data-testid="library-kind-knowledge">
      <h2 class="text-sm font-medium">Knowledge</h2>
      <p class="text-muted-foreground text-sm">No knowledge hits.</p>
    </div>
    <div data-testid="library-kind-artifact">
      <h2 class="text-sm font-medium">Artifact</h2>
      <p class="text-muted-foreground text-sm">No artifact hits.</p>
    </div>
    <div data-testid="library-kind-contribution">
      <h2 class="text-sm font-medium">Contribution</h2>
      <p class="text-muted-foreground text-sm">No contribution hits.</p>
    </div>
  </section>
  <p data-testid="library-empty-action">
    Empty. One upload or search action.
    <Button size="sm" variant="outline" data-testid="library-search"
      >Search</Button
    >
  </p>
</main>
