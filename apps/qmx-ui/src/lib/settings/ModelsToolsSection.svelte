<script lang="ts">
  /**
   * Model providers and MCP servers on one page, one row style: on/off,
   * which copilots may use it, remove. Keys go to the credential store
   * through the daemon; nothing here calls a provider.
   */
  import Plus from "@lucide/svelte/icons/plus";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import Users from "@lucide/svelte/icons/users";
  import { Button } from "$lib/components/ui/button";
  import { Input } from "$lib/components/ui/input";
  import { Switch } from "$lib/components/ui/switch";
  import * as Popover from "$lib/components/ui/popover";
  import InfoTip from "$lib/workbench/InfoTip.svelte";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import Group from "./Group.svelte";
  import { settings } from "./settings.svelte";

  type Kind = "providers" | "mcp";
  let adding = $state<Kind | null>(null);
  let newName = $state("");
  let newWhere = $state("");

  type Item = {
    id: string;
    name: string;
    paid: boolean;
    on: boolean;
    sub: string;
    tip: string;
  };
  const rows = $derived<Record<Kind, Item[]>>({
    providers: settings.providers.map((p) => ({
      ...p,
      sub: p.models.join(", "),
      tip: p.how,
    })),
    mcp: settings.mcp.map((m) => ({ ...m, sub: "", tip: m.note })),
  });

  function setOn(kind: Kind, id: string, on: boolean) {
    const item = settings[kind].find((x) => x.id === id);
    if (!item) return;
    item.on = on;
    if (on && item.paid)
      workbench.notify(`${item.name} is paid: every call asks you first.`);
  }

  function remove(kind: Kind, id: string) {
    const item = settings[kind].find((x) => x.id === id);
    if (kind === "providers")
      settings.providers = settings.providers.filter((x) => x.id !== id);
    else settings.mcp = settings.mcp.filter((x) => x.id !== id);
    for (const c of settings.usersOf(id)) settings.setUse(c.id, id, false);
    if (item) workbench.notify(`Removed ${item.name}.`);
  }

  function add(kind: Kind) {
    const name = newName.trim();
    if (!name) return;
    const id = `${kind}-${Date.now().toString(36)}`;
    if (kind === "providers")
      settings.providers.push({
        id,
        name,
        how: newWhere || "OpenAI-compatible endpoint",
        models: ["Models listed after it connects"],
        paid: true,
        on: false,
      });
    else
      settings.mcp.push({
        id,
        name,
        note: newWhere || "Added by you",
        paid: false,
        on: false,
      });
    settings.setUse("main", id, true);
    workbench.notify(`Added ${name}. It connects when the daemon is running.`);
    newName = "";
    newWhere = "";
    adding = null;
  }

  const GROUPS: { kind: Kind; title: string; tip: string; add: string }[] = [
    {
      kind: "providers",
      title: "Model providers",
      tip: "Where the copilots' models come from. Each copilot picks its model under Copilots, from the providers it may use here.",
      add: "Add provider",
    },
    {
      kind: "mcp",
      title: "MCP servers",
      tip: "Outside tools the copilots can call. Paid ones stay off until you switch them on, and ask before every call.",
      add: "Add MCP server",
    },
  ];
</script>

<div class="grid items-start gap-group 2xl:grid-cols-2">
  {#each GROUPS as grp (grp.kind)}
    {@const list = rows[grp.kind]}
    <Group
      title={grp.title}
      tip={grp.tip}
      meta={`${list.filter((x) => x.on).length} of ${list.length} on`}
    >
      {#snippet actions()}
        <Button
          size="sm"
          variant="outline"
          onclick={() => (adding = adding === grp.kind ? null : grp.kind)}
          ><Plus />{grp.add}</Button
        >
      {/snippet}
      {#if adding === grp.kind}
        <form
          class="bg-muted/40 mb-row flex flex-wrap items-center gap-2 rounded-xl p-tile"
          onsubmit={(e) => {
            e.preventDefault();
            add(grp.kind);
          }}
        >
          <Input
            class="h-8 w-48"
            placeholder="Name"
            bind:value={newName}
            aria-label={`New ${grp.kind === "mcp" ? "MCP server" : "provider"} name`}
          />
          <Input
            class="h-8 min-w-48 flex-1"
            placeholder={grp.kind === "mcp" ? "Command or URL" : "Endpoint URL"}
            bind:value={newWhere}
            aria-label="Where it runs"
          />
          <Button size="sm" type="submit" disabled={!newName.trim()}>Add</Button
          >
          <Button size="sm" variant="ghost" onclick={() => (adding = null)}
            >Cancel</Button
          >
        </form>
      {/if}
      <ul class="flex flex-col">
        {#each list as it (it.id)}
          {@const users = settings.usersOf(it.id)}
          <li
            class="flex min-h-12 items-center gap-3 border-t py-row first:border-t-0"
          >
            <span
              class={it.on
                ? "bg-success size-2 shrink-0 rounded-full"
                : "bg-muted-foreground/40 size-2 shrink-0 rounded-full"}
            ></span>
            <span class="min-w-0 flex-1">
              <span class="flex items-center gap-1 font-medium">
                <span class="truncate">{it.name}</span>
                {#if it.paid}<span class="text-warning text-sm font-normal"
                    >Paid</span
                  >{/if}
                <InfoTip label={`About ${it.name}`} text={it.tip} />
              </span>
              {#if it.sub}<span
                  class="text-muted-foreground block truncate text-sm"
                  >{it.sub}</span
                >{/if}
            </span>
            <Popover.Root>
              <Popover.Trigger
                class="hover:bg-muted flex h-8 shrink-0 items-center gap-1.5 rounded-lg px-2 text-sm"
                aria-label={`Copilots that may use ${it.name}`}
              >
                <Users class="text-muted-foreground size-4" />
                <span class="num">{users.length}</span>
                <span class="text-muted-foreground hidden xl:inline"
                  >{users.length === 1 ? "copilot" : "copilots"}</span
                >
              </Popover.Trigger>
              <Popover.Content align="end" class="w-64">
                <p class="mb-2 text-sm font-medium">May use {it.name}</p>
                <ul class="flex max-h-72 flex-col overflow-auto">
                  {#each settings.copilots as c (c.id)}
                    <li>
                      <label
                        class="hover:bg-muted flex items-center justify-between gap-3 rounded-md px-2 py-row text-sm"
                      >
                        <span class="truncate">{c.name}</span>
                        <Switch
                          size="sm"
                          checked={settings.copilot(c.id).uses.includes(it.id)}
                          onCheckedChange={(v) =>
                            settings.setUse(c.id, it.id, v)}
                          aria-label={`${c.name} may use ${it.name}`}
                        />
                      </label>
                    </li>
                  {/each}
                </ul>
              </Popover.Content>
            </Popover.Root>
            <Switch
              checked={it.on}
              onCheckedChange={(v) => setOn(grp.kind, it.id, v)}
              aria-label={`Use ${it.name}`}
            />
            <Button
              size="icon-sm"
              variant="ghost"
              aria-label={`Remove ${it.name}`}
              onclick={() => remove(grp.kind, it.id)}
              ><Trash2 class="size-4" /></Button
            >
          </li>
        {/each}
      </ul>
    </Group>
  {/each}
</div>
