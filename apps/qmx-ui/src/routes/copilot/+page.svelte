<script lang="ts">
  import { Button } from "$lib/components/ui/button";
</script>

<svelte:head>
  <title>Copilot</title>
</svelte:head>

<main class="flex flex-col gap-4 p-6" data-testid="destination-copilot">
  <p class="text-muted-foreground text-xs tracking-wide uppercase">Copilot</p>
  <h1 class="text-xl font-medium">Conversation workspace</h1>
  <p data-testid="copilot-purpose">
    Independent of Home. Distinct from the optional in-app copilot panel
    (profile app-use). Main Copilot is not Authoring.
  </p>
  <section
    class="bg-surface border-border flex flex-col gap-3 rounded-lg border p-4"
    data-testid="copilot-empty"
    data-state="empty"
  >
    <p>No sessions. One action to start.</p>
    <Button data-testid="copilot-start-session">Start a session</Button>
    <p class="text-muted-foreground text-sm">
      SessionList / ConversationPane land later. Histories stay independent of
      Home and of app-use copilot.
    </p>
  </section>
</main>
