<script lang="ts">
  import { Button } from "$lib/components/ui/button";
  import * as Card from "$lib/components/ui/card";
  import { Badge } from "$lib/components/ui/badge";
  import { Separator } from "$lib/components/ui/separator";
  import PageHeader from "$lib/workbench/PageHeader.svelte";
  import { cn } from "$lib/utils";

  // Settings scopes (UI EXPERIENCE §7): global, app, session, instance.
  const SCOPES = [
    { id: "connection", label: "Connection" },
    { id: "global", label: "General" },
    { id: "apps", label: "Apps" },
    { id: "sessions", label: "Copilot sessions" },
    { id: "developer", label: "Developer" },
  ] as const;
  let scope = $state<string>("connection");

  // Readiness axes are reported by the daemon; nothing is checked yet.
  const AXES = [
    "Daemon reachable",
    "Paired with this window",
    "Model provider",
    "Market data",
    "Trading node",
  ];
</script>

<div class="flex h-full flex-col">
  <PageHeader title="Settings" />

  <div class="flex min-h-0 flex-1">
    <nav
      aria-label="Settings sections"
      class="bg-panel w-52 shrink-0 border-r p-2"
    >
      <ul class="flex flex-col gap-0.5">
        {#each SCOPES as s (s.id)}
          <li>
            <button
              type="button"
              class={cn(
                "hover:bg-muted w-full rounded-lg px-3 py-1.5 text-left text-sm",
                scope === s.id
                  ? "bg-muted text-foreground"
                  : "text-muted-foreground",
              )}
              aria-current={scope === s.id ? "true" : undefined}
              onclick={() => (scope = s.id)}
            >
              {s.label}
            </button>
          </li>
        {/each}
      </ul>
    </nav>

    <div class="min-h-0 flex-1 overflow-auto p-6">
      <div class="mx-auto flex max-w-2xl flex-col gap-4">
        {#if scope === "connection"}
          <Card.Root size="sm">
            <Card.Header>
              <Card.Title>Readiness</Card.Title>
              <Card.Description>
                Start the QMX daemon on this machine, then pair this window with
                it.
              </Card.Description>
            </Card.Header>
            <Card.Content class="flex flex-col">
              {#each AXES as axis, i (axis)}
                {#if i > 0}<Separator />{/if}
                <div class="flex items-center justify-between py-2.5 text-sm">
                  <span>{axis}</span>
                  <Badge variant="outline" class="text-muted-foreground"
                    >Not checked</Badge
                  >
                </div>
              {/each}
            </Card.Content>
            <Card.Footer class="gap-2">
              <Button size="sm" disabled>Pair</Button>
              <Button size="sm" variant="outline" disabled>Check again</Button>
            </Card.Footer>
          </Card.Root>
        {:else if scope === "developer"}
          <Card.Root size="sm">
            <Card.Header>
              <Card.Title>Component gallery</Card.Title>
              <Card.Description>
                Every widget state and a sample mini-app layout, for design
                review. Uses sample content, not live data.
              </Card.Description>
            </Card.Header>
            <Card.Footer>
              <Button size="sm" variant="outline" href="/gallery"
                >Open gallery</Button
              >
            </Card.Footer>
          </Card.Root>
        {:else}
          <p class="text-muted-foreground text-sm">
            These settings are stored by the daemon and appear once it is
            connected.
          </p>
        {/if}
      </div>
    </div>
  </div>
</div>
