<script lang="ts">
  /**
   * One card per copilot (main, Lab, Portfolio, each mini app): its model,
   * standing instructions, what it may touch, and its skills. No modes:
   * planning and the like are skills, called with "/". The copilot gear icons on each screen open here.
   */
  import { Button } from "$lib/components/ui/button";
  import { Textarea } from "$lib/components/ui/textarea";
  import { cn } from "$lib/utils";
  import { MODELS, workbench } from "$lib/workbench/workbench.svelte";
  import { REACH } from "$lib/copilot/aim.svelte";

  type Copilot = {
    id: string;
    name: string;
    note: string;
    model: string;
    reach: string[];
    skills: string[];
    instructions: string;
  };
  let copilots = $state<Copilot[]>([
    {
      id: "main",
      name: "Main copilot",
      note: "Reaches everything you allow; runs errands for days",
      model: MODELS[0].id,
      reach: ["lab", "portfolio", "library", "servers"],
      skills: [
        "Build a pod",
        "Build a panel",
        "Explain an article",
        "Watch while I'm away",
      ],
      instructions:
        "Answer in plain words. Ask before anything that costs money or can't be undone.",
    },
    {
      id: "lab",
      name: "Lab copilot",
      note: "Lab tools only",
      model: MODELS[0].id,
      reach: ["lab", "library", "servers"],
      skills: ["Sweep", "Walk-forward", "Stress scenario", "Train a model"],
      instructions:
        "Test on CFDs and crypto. Never run on the trading servers.",
    },
    {
      id: "portfolio",
      name: "Portfolio copilot",
      note: "Paper sides and layouts; live money only proposes",
      model: MODELS[0].id,
      reach: ["portfolio", "library"],
      skills: ["Explain a refusal", "Draft a paper wiring"],
      instructions: "Live changes are always proposals for my signature.",
    },
    {
      id: "news",
      name: "News & sentiment (mini app)",
      note: "That mini app's operations only",
      model: MODELS[MODELS.length - 1].id,
      reach: ["apps"],
      skills: ["Score sentiment"],
      instructions: "",
    },
  ]);
  let openId = $state("main");
</script>

<div class="flex flex-col gap-4">
  {#each copilots as c, i (c.id)}
    <section class="solid-backing rounded-2xl border">
      <button
        type="button"
        class="flex w-full items-center gap-3 px-5 py-4 text-left"
        aria-expanded={openId === c.id}
        onclick={() => (openId = openId === c.id ? "" : c.id)}
      >
        <span class="min-w-0 flex-1">
          <span class="block text-lg font-semibold">{c.name}</span>
          <span class="text-muted-foreground">{c.note}</span>
        </span>
        <span class="text-muted-foreground"
          >{MODELS.find((m) => m.id === c.model)?.label}</span
        >
      </button>
      {#if openId === c.id}
        <div class="flex flex-col gap-5 border-t px-5 py-5">
          <div>
            <p class="mb-2 font-medium">Model</p>
            <div class="flex flex-wrap gap-2">
              {#each MODELS as m (m.id)}
                <button
                  type="button"
                  class={cn(
                    "rounded-lg border px-3 py-2",
                    c.model === m.id
                      ? "border-primary bg-primary/12"
                      : "hover:bg-muted",
                  )}
                  onclick={() => (copilots[i].model = m.id)}>{m.label}</button
                >
              {/each}
            </div>
          </div>
          <div>
            <p class="mb-2 font-medium">It may touch</p>
            <div class="flex flex-wrap gap-2">
              {#each REACH as r (r.id)}
                <button
                  type="button"
                  aria-pressed={c.reach.includes(r.id)}
                  class={cn(
                    "rounded-full border px-3 py-1.5",
                    c.reach.includes(r.id)
                      ? "border-primary bg-primary/12"
                      : "text-muted-foreground hover:bg-muted",
                  )}
                  onclick={() =>
                    (copilots[i].reach = c.reach.includes(r.id)
                      ? c.reach.filter((x) => x !== r.id)
                      : [...c.reach, r.id])}>{r.label}</button
                >
              {/each}
              <span class="text-muted-foreground px-1 py-1.5"
                >Real money: never, always your signature</span
              >
            </div>
          </div>
          <div>
            <p class="mb-2 font-medium">Standing instructions</p>
            <Textarea
              rows={3}
              bind:value={copilots[i].instructions}
              placeholder="How it should work for you…"
              aria-label={`${c.name} instructions`}
            />
          </div>
          <div>
            <p class="mb-2 font-medium">Skills</p>
            <div class="flex flex-wrap gap-2">
              {#each c.skills as s (s)}<span
                  class="bg-muted rounded-full px-3 py-1.5">{s}</span
                >{/each}
              <Button
                size="sm"
                variant="outline"
                onclick={() =>
                  workbench.notify(
                    "Skills are added from the Library or written with the copilot (needs the daemon).",
                  )}>Add a skill</Button
              >
            </div>
          </div>
        </div>
      {/if}
    </section>
  {/each}
</div>
