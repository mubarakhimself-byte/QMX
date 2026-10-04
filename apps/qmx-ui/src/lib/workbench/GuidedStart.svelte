<script lang="ts">
  /**
   * A copilot-led start (operator, 2026-10-03): instead of a form, the main
   * copilot asks a few multiple-choice questions, one at a time, then
   * proposes a plan and walks the Lab through it, switching layouts as it
   * goes. Demo script; with the daemon wired the copilot asks through the
   * same question card and acts through its skills and tools.
   */
  import { goto } from "$app/navigation";
  import { resolve } from "$app/paths";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import Check from "@lucide/svelte/icons/check";
  import { Button } from "$lib/components/ui/button";
  import { cn } from "$lib/utils";
  import { GUIDES } from "$lib/lab/guides";
  import { workbench } from "./workbench.svelte";

  let { kind }: { kind: "import" | "train" | "workflow" } = $props();

  type Q = { header: string; q: string; options: [string, string][] };
  const SCRIPT: Record<typeof kind, { intro: string; qs: Q[] }> = {
    import: {
      intro:
        "Let's bring it in. Three quick questions so I set the Lab up the right way.",
      qs: [
        {
          header: "Source",
          q: "What are you bringing in?",
          options: [
            ["Code folder", "A repo Claude Code or Codex wrote"],
            ["Notebook", "Cells become steps you can see"],
            ["Model file", "ONNX, pickle or joblib"],
          ],
        },
        {
          header: "Becomes",
          q: "What should it become in QMX?",
          options: [
            ["A new bot", "Its own code, tests and evidence"],
            ["A step", "Added to one of your workflows"],
            ["A model in a slot", "Feeds an existing bot"],
          ],
        },
        {
          header: "First test",
          q: "Where should the first test run?",
          options: [
            ["This laptop", "Can count as evidence"],
            ["Research VPS", "Faster, exploration only"],
            ["Colab", "GPU, exploration only"],
          ],
        },
      ],
    },
    train: {
      intro: "A model it is. Three questions and I'll lay out the training.",
      qs: [
        {
          header: "Predicts",
          q: "What should the model predict?",
          options: [
            ["Entry signal", "Whether a setup is worth taking"],
            ["Regime", "Trending, ranging or volatile"],
            ["Position size", "How much to risk (new scope)"],
          ],
        },
        {
          header: "Data",
          q: "Which data does it learn from?",
          options: [
            ["FX majors M1", "Dukascopy, 2015 to 2026"],
            ["Calendar events", "Forex Factory, daily"],
            ["Upload new data", "CSV, Excel or Parquet"],
          ],
        },
        {
          header: "Machine",
          q: "Where should it train?",
          options: [
            ["This laptop", "Quadro T2000, slow but local"],
            ["Colab", "T4 GPU, about 1.8 units an hour"],
            ["AWS GPU", "A10G, offline right now"],
          ],
        },
      ],
    },
    workflow: {
      intro: "Your own workflow. Tell me what it's for and I'll draft it.",
      qs: [
        {
          header: "Job",
          q: "What should the workflow do?",
          options: [
            ["Retrain on a schedule", "Keep a model fresh"],
            ["Test a hypothesis weekly", "Re-run evidence as data grows"],
            ["Watch and report", "Tell me when something changes"],
          ],
        },
        {
          header: "Trigger",
          q: "What starts it?",
          options: [
            ["A schedule", "Every night, every Monday…"],
            ["New data", "When a dataset updates"],
            ["A news event", "High-impact calendar items"],
          ],
        },
        {
          header: "Machine",
          q: "Where does it run?",
          options: [
            ["This laptop", "Only while it's on"],
            ["Research VPS", "Always on"],
          ],
        },
      ],
    },
  };

  const s = $derived(SCRIPT[kind]);
  let answers = $state<string[]>([]);
  let other = $state("");
  const at = $derived(answers.length);
  const done = $derived(at >= s.qs.length);

  function answer(v: string) {
    if (!v.trim()) return;
    answers = [...answers, v.trim()];
    other = "";
  }
</script>

<div
  class="mx-auto flex max-w-3xl flex-col gap-5 px-6 py-6 text-base leading-relaxed"
>
  <div class="flex items-start gap-3">
    <Sparkles class="text-primary mt-1 size-4 shrink-0" />
    <p>{s.intro}</p>
  </div>

  {#each s.qs.slice(0, Math.min(at + 1, s.qs.length)) as q, i (q.header)}
    {#if i < at}
      <div class="flex flex-col gap-1">
        <p class="text-muted-foreground text-sm">{q.q}</p>
        <div class="bg-muted ml-auto max-w-[85%] rounded-md px-3 py-2">
          {answers[i]}
        </div>
      </div>
    {:else}
      <div class="tile rounded-xl p-4" role="group" aria-label={q.q}>
        <div class="mb-3 flex items-center gap-2">
          <span class="bg-primary/15 text-primary rounded px-1.5 py-0.5 text-xs"
            >{q.header}</span
          >
          <span class="font-medium">{q.q}</span>
          <span class="text-muted-foreground ml-auto text-xs"
            >{i + 1} of {s.qs.length}</span
          >
        </div>
        <div class="grid gap-2 sm:grid-cols-3">
          {#each q.options as [label, note] (label)}
            <button
              type="button"
              class="hover:border-ring hover:bg-muted/40 flex flex-col gap-0.5 rounded-lg border p-3 text-left"
              onclick={() => answer(label)}
            >
              <span class="text-sm font-medium">{label}</span>
              <span class="text-muted-foreground text-xs">{note}</span>
            </button>
          {/each}
        </div>
        <form
          class="mt-2 flex gap-2"
          onsubmit={(e) => {
            e.preventDefault();
            answer(other);
          }}
        >
          <input
            bind:value={other}
            placeholder="Something else…"
            aria-label="Other answer"
            class="bg-background/40 h-8 flex-1 rounded-md border px-2.5 text-sm"
          />
          <Button
            type="submit"
            size="sm"
            variant="outline"
            disabled={!other.trim()}>Answer</Button
          >
        </form>
      </div>
    {/if}
  {/each}

  {#if done}
    {@const g = GUIDES[kind]}
    <div class="flex items-start gap-3">
      <Sparkles class="text-primary mt-1 size-4 shrink-0" />
      <div class="flex min-w-0 flex-1 flex-col gap-3">
        <p>
          Here's the plan. I'll open the Lab and take you through it; each step
          switches to the layout it needs.
        </p>
        <ol class="tile grid gap-2 rounded-xl p-4">
          {#each g.steps as st, i (i)}
            <li class="flex items-start gap-3 text-sm">
              <span
                class={cn(
                  "num mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-full border text-xs",
                )}>{i + 1}</span
              >
              <span class="min-w-0">
                <span class="text-muted-foreground mr-1.5 text-xs capitalize"
                  >{st.layout}</span
                >{st.text}
              </span>
            </li>
          {/each}
        </ol>
        <div class="flex flex-wrap gap-2">
          <Button
            onclick={() =>
              // eslint-disable-next-line svelte/no-navigation-without-resolve -- resolved path plus a query string
              goto(`${resolve("/lab")}?guide=${kind}`)}
            ><Check />Open the Lab and walk me through it</Button
          >
          <Button
            variant="ghost"
            onclick={() =>
              workbench.notify(
                "Setting it up needs the daemon. I'd create the steps and runs and tell you when they're ready.",
              )}>Just set it up for me</Button
          >
        </div>
        <p class="text-muted-foreground text-xs">
          Demo: with the daemon connected I do these steps myself and you watch
          the Lab change.
        </p>
      </div>
    </div>
  {/if}
</div>
