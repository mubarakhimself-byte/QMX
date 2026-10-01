<script lang="ts">
  import { Button } from "$lib/components/ui/button";
  import * as Card from "$lib/components/ui/card";
  import { Badge } from "$lib/components/ui/badge";
  import { Separator } from "$lib/components/ui/separator";
  import PageHeader from "$lib/workbench/PageHeader.svelte";
  import { cn } from "$lib/utils";
  import { workbench, type Theme } from "$lib/workbench/workbench.svelte";

  const THEME_CHOICES: {
    id: Theme;
    label: string;
    note: string;
    swatch: string[];
  }[] = [
    {
      id: "ink",
      label: "Ink",
      note: "Charcoal and old gold",
      swatch: ["#0d0e10", "#e0b062", "#9fd8d0"],
    },
    {
      id: "cobalt",
      label: "Cobalt",
      note: "Electric blue",
      swatch: ["#05082e", "#6f7bff", "#7ee2ff"],
    },
    {
      id: "ember",
      label: "Ember",
      note: "Dark red and orange",
      swatch: ["#120a08", "#ff9a62", "#ffd28a"],
    },
    {
      id: "plain",
      label: "Plain",
      note: "No background, solid panels",
      swatch: ["#252525", "#e5e5e5", "#8a8a8a"],
    },
  ];

  // Settings scopes (UI EXPERIENCE §7): global, app, session, instance.
  const SCOPES = [
    { id: "connection", label: "Connection" },
    { id: "appearance", label: "Appearance" },
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
        {:else if scope === "appearance"}
          <Card.Root size="sm">
            <Card.Header>
              <Card.Title>Theme</Card.Title>
              <Card.Description>
                Glass panels over an ink map of fractal price paths. Trading
                screens always use a plain background.
              </Card.Description>
            </Card.Header>
            <Card.Content>
              <div
                class="grid grid-cols-2 gap-2"
                role="radiogroup"
                aria-label="Theme"
              >
                {#each THEME_CHOICES as t (t.id)}
                  <button
                    type="button"
                    role="radio"
                    aria-checked={workbench.theme === t.id}
                    class={cn(
                      "hover:bg-muted flex items-center gap-3 rounded-lg border p-3 text-left",
                      workbench.theme === t.id && "border-ring bg-muted",
                    )}
                    onclick={() => workbench.setTheme(t.id)}
                  >
                    <span class="flex -space-x-1.5">
                      {#each t.swatch as c (c)}
                        <span
                          class="ring-background size-5 rounded-full ring-2"
                          style="background: {c}"
                        ></span>
                      {/each}
                    </span>
                    <span>
                      <span class="block text-sm font-medium">{t.label}</span>
                      <span class="text-muted-foreground block text-xs"
                        >{t.note}</span
                      >
                    </span>
                  </button>
                {/each}
              </div>
            </Card.Content>
          </Card.Root>
        {:else if scope === "developer"}
          <Card.Root size="sm">
            <Card.Header>
              <Card.Title>Demo mode</Card.Title>
              <Card.Description>
                Shows a labelled sample Research app, workflow, Library and
                conversation for design review. Sample data only; nothing is
                saved or run.
              </Card.Description>
            </Card.Header>
            <Card.Footer>
              <Button
                size="sm"
                variant={workbench.demoMode ? "secondary" : "outline"}
                aria-pressed={workbench.demoMode}
                onclick={() => (workbench.demoMode = !workbench.demoMode)}
              >
                {workbench.demoMode
                  ? "Demo mode is on: turn off"
                  : "Turn on demo mode"}
              </Button>
            </Card.Footer>
          </Card.Root>
          <Card.Root size="sm">
            <Card.Header>
              <Card.Title>Component library</Card.Title>
              <Card.Description>
                Every QMX building block rendered live, with the spec the
                copilot uses to compose mini apps. For design review. Uses
                sample content, not live data.
              </Card.Description>
            </Card.Header>
            <Card.Footer>
              <Button size="sm" variant="outline" href="/gallery"
                >Open library</Button
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
