<script lang="ts">
  import { resolve } from "$app/paths";
  import { Button } from "$lib/components/ui/button";
</script>

<svelte:head>
  <title>Home</title>
</svelte:head>

<main
  class="flex flex-col gap-4 p-6"
  data-testid="destination-home"
  data-profile="authoring"
>
  <p class="text-muted-foreground text-xs tracking-wide uppercase">Home</p>
  <h1 class="text-xl font-medium">Work / attention / resume</h1>
  <p data-testid="home-purpose">
    Independent of Copilot. Profile authoring. No third ProductSessionProfile.
    Observation is not a fourth product.
  </p>
  <section
    class="bg-surface border-border flex flex-col gap-3 rounded-lg border p-4"
    data-testid="home-empty"
    data-state="empty"
  >
    <p data-testid="home-empty-action">
      No running work. One action to start Copilot or Authoring.
    </p>
    <div class="flex flex-wrap gap-2">
      <Button href={resolve("/copilot")} data-testid="home-start-copilot"
        >Start Copilot</Button
      >
      <Button
        href={resolve("/authoring")}
        variant="outline"
        data-testid="home-start-authoring">Start Authoring</Button
      >
    </div>
  </section>
  <p
    class="text-muted-foreground text-sm"
    data-testid="disconnected-vs-attention"
  >
    Disconnected vs attention stay distinct. A reconnecting badge is not failed
    attention.
  </p>
</main>
