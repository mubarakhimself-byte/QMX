<script lang="ts">
  /**
   * Servers and data on one page. Machines: every trading server, Lab
   * machine and store with its status and what runs there. Data: the
   * sources the Library, widgets and workflows read, each with a schedule.
   * Paid sources (Firecrawl) stay off until you approve them.
   */
  import Plus from "@lucide/svelte/icons/plus";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import Lock from "@lucide/svelte/icons/lock";
  import { Button } from "$lib/components/ui/button";
  import { Input } from "$lib/components/ui/input";
  import { Switch } from "$lib/components/ui/switch";
  import * as Dialog from "$lib/components/ui/dialog";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu";
  import { cn } from "$lib/utils";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { ACCOUNTS, NODES } from "$lib/portfolio/demo";
  import { ENVIRONMENTS, STORAGE } from "$lib/lab/demo";
  import { thisLaptop } from "$lib/lab/this-laptop";
  import Choice from "./Choice.svelte";
  import Group from "./Group.svelte";
  import {
    SCHEDULES,
    SOURCES,
    SOURCE_KINDS,
    settings,
    type SourceKind,
  } from "./settings.svelte";

  const TONE: Record<string, string> = {
    up: "bg-success",
    ready: "bg-success",
    busy: "bg-info",
    degraded: "bg-warning",
    offline: "bg-muted-foreground",
    down: "bg-destructive",
  };
  const ALL = [
    ...NODES.map((n) => ({
      id: n.id,
      name: n.name,
      role: "Trading",
      status: n.status,
      where: n.where,
      runs:
        ACCOUNTS.filter((a) => a.node === n.id)
          .map((a) => a.name)
          .join(", ") || "Nothing yet",
      load: `CPU ${n.cpu}%`,
    })),
    ...ENVIRONMENTS.map((e) => ({
      id: e.id,
      name: e.name,
      role: "Lab",
      status: e.status,
      where: e.where,
      runs: `${e.slots[0]} of ${e.slots[1]} job slots busy`,
      load: e.hardware,
    })),
    ...STORAGE.map((s) => ({
      id: s.id,
      name: s.name,
      role: "Storage",
      status: "up",
      where: s.where,
      runs: "Data, models and reports",
      load: s.used,
    })),
  ];
  /** One row per machine: this laptop trades, tests and stores. */
  const MACHINES = [...new Set(ALL.map((m) => m.name))].map((name) => {
    const parts = ALL.filter((m) => m.name === name);
    return {
      ...parts[0],
      role: parts.map((m) => m.role).join(", "),
      runs: parts.map((m) => m.runs).join(" · "),
    };
  });
  // Day one (demo off): this laptop only, and only the sources you added.
  const local = thisLaptop();
  const machines = $derived(
    workbench.demoMode
      ? MACHINES
      : [
          {
            id: local.id,
            name: local.name,
            role: "Lab, Storage",
            status: "ready",
            where: "Here",
            runs: "Nothing yet",
            load: local.hardware,
          },
        ],
  );
  const BUILT_IN = new Set(SOURCES.map((s) => s.id));
  const sources = $derived(
    workbench.demoMode
      ? settings.sources
      : settings.sources.filter((s) => !BUILT_IN.has(s.id)),
  );
  const need = (what: string) => workbench.notify(`${what} needs the daemon.`);

  // Add a source
  const HOW: { kind: SourceKind; label: string }[] = [
    { kind: "upload", label: "Upload a file" },
    { kind: "api", label: "API provider" },
    { kind: "scrape", label: "Scrape a site" },
    { kind: "feed", label: "Feed (RSS)" },
  ];
  let open = $state(false);
  let how = $state<SourceKind>("upload");
  let name = $state("");
  let where = $state("");
  let file = $state<File | null>(null);
  let schedule = $state<string>("Daily");
  let viaFirecrawl = $state(false);

  function reset() {
    how = "upload";
    name = "";
    where = "";
    file = null;
    schedule = "Daily";
    viaFirecrawl = false;
  }

  const canAdd = $derived(
    how === "upload" ? !!file : name.trim() !== "" && where.trim() !== "",
  );

  function addSource() {
    const paid = how === "scrape" && viaFirecrawl;
    const label =
      how === "upload" ? name.trim() || (file?.name ?? "File") : name.trim();
    settings.sources.push({
      id: `src-${Date.now().toString(36)}`,
      name: label,
      kind: how,
      detail:
        how === "upload"
          ? (file?.name ?? "")
          : paid
            ? `${where.trim()} via Firecrawl`
            : where.trim(),
      schedule: how === "upload" ? "On request" : schedule,
      on: !paid,
      paid,
      approved: !paid,
    });
    workbench.notify(
      paid
        ? `Added ${label}, off until you approve Firecrawl.`
        : `Added ${label}. It fetches once the daemon runs.`,
    );
    open = false;
    reset();
  }

  function removeSource(id: string) {
    const s = settings.sources.find((x) => x.id === id);
    settings.sources = settings.sources.filter((x) => x.id !== id);
    if (s) workbench.notify(`Removed ${s.name}.`);
  }
</script>

<div class="flex flex-col gap-group">
  <Group
    title="Machines"
    tip="Trading servers keep trading when this laptop is off. Lab machines run tests, sweeps and training."
    meta={machines.length === 1 ? "1 machine" : `${machines.length} machines`}
  >
    {#snippet actions()}
      <DropdownMenu.Root>
        <DropdownMenu.Trigger>
          {#snippet child({ props })}
            <Button {...props} size="sm" variant="outline"
              ><Plus />Add machine</Button
            >
          {/snippet}
        </DropdownMenu.Trigger>
        <DropdownMenu.Content align="end" class="w-64">
          <DropdownMenu.Item onclick={() => need("Adding a VPS over SSH")}
            >A VPS (over SSH)</DropdownMenu.Item
          >
          <DropdownMenu.Item onclick={() => need("Adding a cloud GPU")}
            >A cloud GPU (AWS, RunPod…)</DropdownMenu.Item
          >
          <DropdownMenu.Item onclick={() => need("Connecting Colab")}
            >Google Colab</DropdownMenu.Item
          >
          <DropdownMenu.Item onclick={() => need("Adding a storage bucket")}
            >A storage bucket</DropdownMenu.Item
          >
        </DropdownMenu.Content>
      </DropdownMenu.Root>
    {/snippet}
    <table class="w-full text-left">
      <thead class="text-muted-foreground text-sm">
        <tr>
          <th class="py-row font-normal">Machine</th>
          <th class="py-row font-normal">Role</th>
          <th class="hidden py-row font-normal xl:table-cell">Where</th>
          <th class="py-row font-normal">Runs</th>
          <th class="hidden py-row font-normal 2xl:table-cell">Load</th>
          <th class="py-row"><span class="sr-only">Actions</span></th>
        </tr>
      </thead>
      <tbody>
        {#each machines as m (m.name)}
          <tr class="border-t">
            <td class="py-row pr-4">
              <span class="flex items-center gap-2 font-medium">
                <span
                  class={cn("size-2 shrink-0 rounded-full", TONE[m.status])}
                  title={m.status}
                ></span>
                {m.name}
                <span class="text-muted-foreground text-sm font-normal"
                  >{m.status}</span
                >
              </span>
            </td>
            <td class="text-muted-foreground py-row pr-4">{m.role}</td>
            <td class="text-muted-foreground hidden py-row pr-4 xl:table-cell"
              >{m.where}</td
            >
            <td class="py-row pr-4">{m.runs}</td>
            <td class="text-muted-foreground hidden py-row pr-4 2xl:table-cell"
              >{m.load}</td
            >
            <td class="py-row text-right">
              <Button
                size="sm"
                variant="ghost"
                onclick={() => need(`Opening ${m.name}`)}>Manage</Button
              >
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  </Group>

  <Group
    title="Data sources"
    tip="What the Library, widgets and workflows can read. Paid sources stay off until you approve them, and ask before every use."
    meta={sources.length
      ? `${sources.filter((s) => s.on).length} of ${sources.length} on`
      : "None added"}
  >
    {#snippet actions()}
      <Button size="sm" variant="outline" onclick={() => (open = true)}
        ><Plus />Add source</Button
      >
    {/snippet}
    {#if !sources.length}
      <p class="text-muted-foreground">No sources yet</p>
    {:else}
      <table class="w-full text-left">
        <thead class="text-muted-foreground text-sm">
          <tr>
            <th class="py-row font-normal">Source</th>
            <th class="py-row font-normal">Type</th>
            <th class="hidden py-row font-normal xl:table-cell">What</th>
            <th class="py-row font-normal">Schedule</th>
            <th class="py-row font-normal">On</th>
            <th class="py-row"><span class="sr-only">Remove</span></th>
          </tr>
        </thead>
        <tbody>
          {#each sources as s (s.id)}
            <tr class="border-t">
              <td class="py-row pr-4 font-medium">
                {s.name}{#if s.paid}<span
                    class="text-warning ml-2 text-sm font-normal">Paid</span
                  >{/if}
              </td>
              <td class="text-muted-foreground py-row pr-4"
                >{SOURCE_KINDS[s.kind]}</td
              >
              <td class="text-muted-foreground hidden py-row pr-4 xl:table-cell"
                >{s.detail}</td
              >
              <td class="py-row pr-4">
                <Choice
                  label={`${s.name} schedule`}
                  bind:value={s.schedule}
                  options={SCHEDULES}
                  class="h-8"
                />
              </td>
              <td class="py-row pr-4">
                {#if s.paid && !s.approved}
                  <Button
                    size="sm"
                    variant="outline"
                    class="text-warning"
                    onclick={() => {
                      s.approved = true;
                      workbench.notify(
                        `${s.name} approved. It stays off until you switch it on, and asks before every call.`,
                      );
                    }}><Lock class="size-3.5" />Approve</Button
                  >
                {:else}
                  <Switch bind:checked={s.on} aria-label={`Use ${s.name}`} />
                {/if}
              </td>
              <td class="py-row text-right">
                <Button
                  size="icon-sm"
                  variant="ghost"
                  aria-label={`Remove ${s.name}`}
                  onclick={() => removeSource(s.id)}
                  ><Trash2 class="size-4" /></Button
                >
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    {/if}
  </Group>
</div>

<Dialog.Root bind:open onOpenChange={(v) => !v && reset()}>
  <Dialog.Content class="sm:max-w-lg">
    <Dialog.Header>
      <Dialog.Title>Add a source</Dialog.Title>
    </Dialog.Header>
    <form
      class="flex flex-col gap-4"
      onsubmit={(e) => {
        e.preventDefault();
        if (canAdd) addSource();
      }}
    >
      <div class="grid grid-cols-2 gap-2" role="radiogroup" aria-label="How">
        {#each HOW as h (h.kind)}
          <button
            type="button"
            role="radio"
            aria-checked={how === h.kind}
            class={cn(
              "rounded-lg border px-3 py-2 text-left",
              how === h.kind
                ? "border-primary bg-primary/12"
                : "hover:bg-muted",
            )}
            onclick={() => (how = h.kind)}>{h.label}</button
          >
        {/each}
      </div>

      {#if how === "upload"}
        <Input
          type="file"
          accept=".csv,.parquet,.json,.pdf,.txt"
          aria-label="File"
          onchange={(e) => (file = e.currentTarget.files?.[0] ?? null)}
        />
        <Input
          placeholder="Name (optional)"
          bind:value={name}
          aria-label="Name"
        />
      {:else}
        <Input placeholder="Name" bind:value={name} aria-label="Name" />
        <Input
          placeholder={how === "api"
            ? "Provider or base URL"
            : how === "scrape"
              ? "Site URL"
              : "Feed URL"}
          bind:value={where}
          aria-label={how === "scrape" ? "Site URL" : "Where"}
        />
        {#if how === "scrape"}
          <label class="flex items-center justify-between gap-3">
            <span
              >Use Firecrawl <span class="text-warning text-sm">Paid</span
              ></span
            >
            <Switch bind:checked={viaFirecrawl} aria-label="Use Firecrawl" />
          </label>
        {/if}
        <label class="flex items-center justify-between gap-3">
          <span>Schedule</span>
          <Choice label="Schedule" bind:value={schedule} options={SCHEDULES} />
        </label>
      {/if}

      <Dialog.Footer>
        <Button variant="ghost" onclick={() => (open = false)}>Cancel</Button>
        <Button type="submit" disabled={!canAdd}>Add source</Button>
      </Dialog.Footer>
    </form>
  </Dialog.Content>
</Dialog.Root>
