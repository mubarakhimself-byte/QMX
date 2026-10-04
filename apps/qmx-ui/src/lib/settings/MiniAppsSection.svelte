<script lang="ts">
  /**
   * Installed mini apps, each with its own settings: where its code runs
   * (its own sandbox), what it may do, its budget, and its stage on the
   * mini app's road to live. Safe mode turns off everything not shipped
   * with QMX in one switch. Proposal: handoff/MINI-APPS-AND-COPILOT-CONTRACT.md.
   */
  import { Switch } from "$lib/components/ui/switch";
  import { cn } from "$lib/utils";
  import { workbench } from "$lib/workbench/workbench.svelte";

  let safe = $state(false);
  let apps = $state([
    {
      name: "News & sentiment",
      kind: "Headless",
      risk: "Shows things",
      stage: "Live",
      runs: "Its own container on vps-fsn",
      budget: "2 CPU hours a day · network: news sites only",
      ops: ["news.refresh", "news.windows"],
      on: true,
    },
    {
      name: "Research · Crypto",
      kind: "Screens and a copilot",
      risk: "Shows things",
      stage: "Shadow run, day 3 of 7",
      runs: "Its own container on this laptop",
      budget: "1 CPU hour a day · network: exchanges only",
      ops: ["crypto.quote", "crypto.signals", "crypto.correlation"],
      on: true,
    },
  ]);
  const STEPS = ["Build", "Tests", "Sandbox", "Shadow run", "Live"];
  const at = (stage: string) =>
    stage.startsWith("Live") ? 4 : stage.startsWith("Shadow") ? 3 : 2;
</script>

<div class="flex flex-col gap-6">
  <section class="flex items-center gap-4 rounded-2xl border p-5">
    <div class="min-w-0 flex-1">
      <h3 class="text-lg font-semibold">Safe mode</h3>
      <p class="text-muted-foreground">
        Turns off every mini app and add-on that didn't ship with QMX. Use it if
        something misbehaves.
      </p>
    </div>
    <Switch
      checked={safe}
      onCheckedChange={(v) => {
        safe = v;
        workbench.notify(
          v ? "Safe mode on: add-ons are off." : "Safe mode off.",
        );
      }}
      aria-label="Safe mode"
    />
  </section>

  {#each apps as a, i (a.name)}
    <section class={cn("rounded-2xl border p-5", safe && "opacity-50")}>
      <div class="flex items-center gap-3">
        <h3 class="text-lg font-semibold">{a.name}</h3>
        <span class="text-muted-foreground">{a.kind} · {a.risk}</span>
        <Switch
          class="ml-auto"
          checked={a.on && !safe}
          disabled={safe}
          onCheckedChange={(v) => (apps[i].on = v)}
          aria-label={`Turn ${a.name} on`}
        />
      </div>
      <div class="mt-4 flex gap-1.5" aria-label={`Road to live: ${a.stage}`}>
        {#each STEPS as s, k (s)}
          <span class="flex-1">
            <span
              class={cn(
                "block h-1.5 rounded-full",
                k < at(a.stage)
                  ? "bg-success"
                  : k === at(a.stage)
                    ? "bg-info"
                    : "bg-muted",
              )}
            ></span>
            <span class="text-muted-foreground mt-1 block text-sm">{s}</span>
          </span>
        {/each}
      </div>
      <dl class="mt-4 grid gap-x-6 gap-y-2 sm:grid-cols-[10rem_1fr]">
        <dt class="text-muted-foreground">Stage</dt>
        <dd>{a.stage}</dd>
        <dt class="text-muted-foreground">Runs in</dt>
        <dd>{a.runs}</dd>
        <dt class="text-muted-foreground">Budget</dt>
        <dd>{a.budget}</dd>
        <dt class="text-muted-foreground">May do</dt>
        <dd class="font-mono text-sm">{a.ops.join(", ")}</dd>
      </dl>
    </section>
  {/each}
</div>
