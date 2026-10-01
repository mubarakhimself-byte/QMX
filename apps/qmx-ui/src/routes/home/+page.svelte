<script lang="ts">
  import BellDot from "@lucide/svelte/icons/bell-dot";
  import History from "@lucide/svelte/icons/history";
  import MessagesSquare from "@lucide/svelte/icons/messages-square";
  import Workflow from "@lucide/svelte/icons/workflow";
  import LibraryBig from "@lucide/svelte/icons/library-big";
  import { Button } from "$lib/components/ui/button";
  import * as Card from "$lib/components/ui/card";
  import PageHeader from "$lib/workbench/PageHeader.svelte";
  import EmptyState from "$lib/workbench/EmptyState.svelte";
  import Composer from "$lib/workbench/Composer.svelte";
</script>

<div class="flex h-full flex-col">
  <PageHeader title="Home" subtitle="Work in progress, attention and resume" />

  <div class="min-h-0 flex-1 overflow-auto">
    <div class="mx-auto grid max-w-6xl gap-4 p-4 lg:grid-cols-[1fr_22rem]">
      <div class="flex flex-col gap-4">
        <Card.Root size="sm">
          <Card.Header>
            <Card.Title>Needs attention</Card.Title>
            <Card.Description
              >Failed, unknown and running jobs.</Card.Description
            >
          </Card.Header>
          <Card.Content>
            <EmptyState
              icon={BellDot}
              title="Nothing needs attention"
              description="Jobs appear here once QMX is connected to its daemon."
            />
          </Card.Content>
        </Card.Root>

        <Card.Root size="sm">
          <Card.Header>
            <Card.Title>Resume</Card.Title>
            <Card.Description>Recent sessions and opened apps.</Card.Description
            >
          </Card.Header>
          <Card.Content>
            <EmptyState icon={History} title="No recent work" />
          </Card.Content>
        </Card.Root>
      </div>

      <div class="flex flex-col gap-4">
        <Card.Root size="sm">
          <Card.Header><Card.Title>Start</Card.Title></Card.Header>
          <Card.Content class="flex flex-col gap-2">
            <Button variant="outline" class="justify-start" href="/copilot">
              <MessagesSquare /> Open Copilot
            </Button>
            <Button variant="outline" class="justify-start" href="/authoring">
              <Workflow /> Open Authoring
            </Button>
            <Button variant="outline" class="justify-start" href="/library">
              <LibraryBig /> Browse Library
            </Button>
          </Card.Content>
        </Card.Root>

        <Card.Root size="sm">
          <Card.Header>
            <Card.Title>Quick chat</Card.Title>
            <Card.Description>
              Separate from Copilot sessions. Not tied to any app.
            </Card.Description>
          </Card.Header>
          <Card.Content>
            <Composer placeholder="Ask about your work…" label="Home chat" />
          </Card.Content>
        </Card.Root>
      </div>
    </div>
  </div>
</div>
