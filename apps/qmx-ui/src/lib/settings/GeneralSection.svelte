<script lang="ts">
  import { Input } from "$lib/components/ui/input";
  import { Switch } from "$lib/components/ui/switch";
  import { Button } from "$lib/components/ui/button";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import Choice from "./Choice.svelte";
  import Group from "./Group.svelte";
  import Row from "./Row.svelte";
  import { ALERTS, settings } from "./settings.svelte";

  const g = settings.general;
  const ZONES = [
    "UTC",
    "Europe/London",
    "Europe/Berlin",
    "Africa/Lagos",
    "Asia/Dubai",
    "Asia/Singapore",
    "Asia/Tokyo",
    "America/New_York",
    "America/Chicago",
    "Australia/Sydney",
  ];
  const zones = $derived(
    ZONES.includes(g.timeZone) ? ZONES : [g.timeZone, ...ZONES],
  );
  const START = [
    { value: "home", label: "Home" },
    { value: "copilot", label: "Copilot" },
    { value: "lab", label: "Lab" },
    { value: "portfolio", label: "Portfolio" },
    { value: "library", label: "Library" },
    { value: "apps", label: "Apps" },
  ];
</script>

<div class="grid items-start gap-group 2xl:grid-cols-2">
  <Group title="You">
    <Row label="Your name">
      <Input
        class="h-8 w-56"
        placeholder="What the copilots call you"
        maxlength={40}
        bind:value={g.name}
        aria-label="Your name"
      />
    </Row>
    <Row label="Time zone">
      <Choice label="Time zone" bind:value={g.timeZone} options={zones} />
    </Row>
    <Row label="Currency" tip="Every figure in QMX is shown in this currency.">
      <Choice
        label="Currency"
        bind:value={g.currency}
        options={["USD", "EUR", "GBP"]}
      />
    </Row>
    <Row label="Open QMX on">
      <Choice label="Start screen" bind:value={g.start} options={START} />
    </Row>
    <Row label="Week starts on">
      <Choice
        label="Week starts on"
        bind:value={g.weekStart}
        options={[
          { value: "mon", label: "Monday" },
          { value: "sun", label: "Sunday" },
        ]}
      />
    </Row>
    <Row label="Numbers">
      <Choice
        label="Number format"
        bind:value={g.numbers}
        options={["1,234.56", "1.234,56", "1 234,56"]}
      />
    </Row>
  </Group>

  <div class="flex flex-col gap-group">
    <Group title="Alert me when">
      {#each ALERTS as a (a.id)}
        <Row label={a.label}>
          <Switch bind:checked={g.alerts[a.id]} aria-label={a.label} />
        </Row>
      {/each}
      <Row
        label="Quiet hours"
        tip="Alerts wait until the end of quiet hours. The kill switch and risk stops always alert."
      >
        <Input
          type="time"
          class="h-8 w-32"
          bind:value={g.quietFrom}
          disabled={!g.quietOn}
          aria-label="Quiet from"
        />
        <span class="text-muted-foreground">to</span>
        <Input
          type="time"
          class="h-8 w-32"
          bind:value={g.quietTo}
          disabled={!g.quietOn}
          aria-label="Quiet until"
        />
        <Switch bind:checked={g.quietOn} aria-label="Quiet hours" />
      </Row>
    </Group>

    <Group title="Updates">
      <Row label="New versions">
        <Choice
          label="Updates"
          bind:value={g.updates}
          options={[
            { value: "auto", label: "Install by themselves" },
            { value: "ask", label: "Ask me" },
            { value: "off", label: "Off" },
          ]}
        />
      </Row>
      <Row label="Channel">
        <Choice
          label="Update channel"
          bind:value={g.channel}
          options={[
            { value: "stable", label: "Stable" },
            { value: "beta", label: "Beta" },
          ]}
        />
        <Button
          size="sm"
          variant="outline"
          onclick={() =>
            workbench.notify("Checking for updates needs the daemon.")}
          >Check now</Button
        >
      </Row>
    </Group>
  </div>
</div>
