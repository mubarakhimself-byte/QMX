<script lang="ts">
  /**
   * The empty desk: what you see before an errand is chosen. No greeting
   * (operator 2026-10-02: "I don't like this thing you've added"). It
   * shows the errands already waiting on you first, then errand templates
   * to start from (Lego vision: templates everywhere). Some templates
   * start a guided walk; others draft the first message for you.
   */
  import GraduationCap from "@lucide/svelte/icons/graduation-cap";
  import Upload from "@lucide/svelte/icons/upload";
  import Workflow from "@lucide/svelte/icons/workflow";
  import Layers2 from "@lucide/svelte/icons/layers-2";
  import BookOpen from "@lucide/svelte/icons/book-open";
  import Eye from "@lucide/svelte/icons/eye";
  import ArrowRight from "@lucide/svelte/icons/arrow-right";
  import { HOW_DO_I } from "./demo";
  import { copilot } from "./store.svelte";

  let {
    onstart,
    onask,
    onopen,
  }: {
    onstart: (kind: "train" | "import" | "workflow") => void;
    onask: (text: string) => void;
    onopen?: (id: string) => void;
  } = $props();

  const ICONS = [GraduationCap, Upload, Workflow, Layers2, BookOpen, Eye];
  const waiting = $derived(
    copilot.sessions.filter((s) => copilot.pending(s.id)).slice(0, 3),
  );
</script>

<div class="mx-auto flex max-w-[46rem] flex-col gap-10 px-8 py-12">
  <div>
    <h2 class="text-3xl font-semibold tracking-tight">A new errand</h2>
    <p class="text-muted-foreground mt-2 text-lg">
      Say what you want done below. An errand can take minutes or days; it keeps
      running on your servers when QMX is closed, and stops to ask you when it
      needs a decision.
    </p>
  </div>

  {#if waiting.length && onopen}
    <section>
      <h3 class="mb-3 text-lg font-semibold">Waiting on you first</h3>
      <ul class="flex flex-col gap-2">
        {#each waiting as s (s.id)}
          <li>
            <button
              type="button"
              class="hover:bg-muted/50 flex w-full items-center gap-4 rounded-2xl border px-5 py-4 text-left"
              onclick={() => onopen(s.id)}
            >
              <span class="bg-warning size-2.5 shrink-0 rounded-full"></span>
              <span class="min-w-0 flex-1">
                <span class="block text-base font-medium">{s.title}</span>
                {#if s.goal}<span class="text-muted-foreground block truncate"
                    >{s.goal}</span
                  >{/if}
              </span>
              <ArrowRight class="text-muted-foreground size-5" />
            </button>
          </li>
        {/each}
      </ul>
    </section>
  {/if}

  <section>
    <h3 class="mb-3 text-lg font-semibold">Start from a template</h3>
    <ul class="grid gap-3 sm:grid-cols-2">
      {#each HOW_DO_I as h, i (h.q)}
        {@const Icon = ICONS[i]}
        <li>
          <button
            type="button"
            class="hover:border-ring/60 hover:bg-muted/40 flex h-full w-full items-start gap-4 rounded-2xl border p-5 text-left"
            onclick={() =>
              h.start
                ? onstart(h.start as "train" | "import" | "workflow")
                : onask(h.ask ?? "")}
          >
            <Icon class="text-primary mt-0.5 size-6 shrink-0" />
            <span>
              <span class="block text-base font-medium">{h.q}</span>
              <span class="text-muted-foreground">{h.note}</span>
            </span>
          </button>
        </li>
      {/each}
    </ul>
  </section>
</div>
