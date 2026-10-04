<script lang="ts">
  /**
   * Model providers and MCP servers: where the copilots' thinking comes
   * from, and the outside tools they may use. Keys live in the system
   * credential store; paid services stay off until you switch them on.
   */
  import Plus from "@lucide/svelte/icons/plus";
  import { Button } from "$lib/components/ui/button";
  import { Switch } from "$lib/components/ui/switch";
  import { workbench } from "$lib/workbench/workbench.svelte";

  let { part }: { part: "providers" | "mcp" } = $props();

  /** How each provider connects: a key in the credential store, your
   * Claude plan through the Claude Code CLI on this laptop (no key), or a
   * model running locally. */
  const PROVIDERS = [
    {
      name: "Claude through your plan",
      how: "Claude Code on this laptop · no key, uses your Claude plan",
      models: "Opus 5.5 (daily driver), Sonnet 5.5, Haiku 4.5",
      state: "Signed in",
    },
    {
      name: "Anthropic API",
      how: "API key in the credential store · billed per use",
      models: "Opus 5.5, Sonnet 5.5, Haiku 4.5",
      state: "Key set",
    },
    {
      name: "OpenAI",
      how: "API key",
      models: "GPT models",
      state: "Not set",
    },
    {
      name: "Google Gemini",
      how: "API key",
      models: "Gemini models",
      state: "Not set",
    },
    {
      name: "OpenRouter",
      how: "API key · one key for many models",
      models: "DeepSeek, Qwen, Grok and others",
      state: "Not set",
    },
    {
      name: "Local models",
      how: "Ollama on this laptop · free, private, slower",
      models: "qwen, llama",
      state: "Found 2",
    },
  ];
  let mcp = $state([
    {
      name: "Firecrawl",
      note: "Web search and scraping; Alexandria data providers",
      paid: true,
      on: false,
      copilots: "Main, Library",
    },
    {
      name: "Exchange data",
      note: "Prices, order books and funding from your exchanges",
      paid: false,
      on: true,
      copilots: "All",
    },
    {
      name: "Files",
      note: "Read and write inside the QMX data folder only",
      paid: false,
      on: true,
      copilots: "Main, Lab",
    },
    {
      name: "GitHub",
      note: "Read strategy repositories",
      paid: false,
      on: false,
      copilots: "Lab",
    },
  ]);
  const need = (what: string) => workbench.notify(`${what} needs the daemon.`);
</script>

{#if part === "providers"}
  <div class="flex flex-col gap-4">
    <p class="text-muted-foreground max-w-2xl">
      Which models the copilots can use. Pick each copilot's model under
      Copilots.
    </p>
    <div class="grid gap-4 xl:grid-cols-2">
      {#each PROVIDERS as p (p.name)}
        <section
          class="solid-backing flex flex-col gap-1 rounded-2xl border p-5"
        >
          <div class="flex items-center gap-3">
            <h3 class="text-lg font-semibold">{p.name}</h3>
            <span
              class={p.state === "Not set"
                ? "text-muted-foreground ml-auto"
                : "text-success ml-auto"}>{p.state}</span
            >
          </div>
          <p>{p.models}</p>
          <p class="text-muted-foreground text-sm">{p.how}</p>
          <Button
            variant="outline"
            size="sm"
            class="mt-3 w-fit"
            onclick={() => need(`Setting up ${p.name}`)}
            >{p.state === "Not set" ? "Connect" : "Manage"}</Button
          >
        </section>
      {/each}
    </div>
    <Button
      variant="outline"
      class="w-fit"
      onclick={() => need("Adding an OpenAI-compatible endpoint")}
      ><Plus />Add any OpenAI-compatible endpoint</Button
    >
  </div>
{:else}
  <div class="flex flex-col gap-4">
    <p class="text-muted-foreground max-w-2xl">
      Outside tools the copilots can call. Paid ones stay off until you switch
      them on, and you choose which copilots may use each.
    </p>
    {#each mcp as m, i (m.name)}
      <section
        class="solid-backing flex flex-wrap items-center gap-4 rounded-2xl border p-5"
      >
        <div class="min-w-0 flex-1">
          <h3 class="text-lg font-semibold">
            {m.name}{#if m.paid}<span
                class="text-warning ml-2 text-sm font-normal">Paid</span
              >{/if}
          </h3>
          <p class="text-muted-foreground">{m.note}</p>
          <p class="text-muted-foreground mt-1 text-sm">
            Used by: {m.copilots}
          </p>
        </div>
        <Switch
          checked={m.on}
          onCheckedChange={(v) => {
            mcp[i].on = v;
            if (v && m.paid)
              workbench.notify(
                `${m.name} is a paid service: calls cost money once the daemon connects it.`,
              );
          }}
          aria-label={`Use ${m.name}`}
        />
      </section>
    {/each}
    <Button
      variant="outline"
      class="w-fit"
      onclick={() => need("Adding an MCP server")}
      ><Plus />Add an MCP server</Button
    >
  </div>
{/if}
