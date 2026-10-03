<script lang="ts">
  /**
   * A new session starts here: a greeting and "How do I…" (operator's help
   * idea: "how do I train something new"). Some start a guided walk with
   * question cards; others draft the message for you.
   */
  import GraduationCap from "@lucide/svelte/icons/graduation-cap";
  import Upload from "@lucide/svelte/icons/upload";
  import Workflow from "@lucide/svelte/icons/workflow";
  import Layers2 from "@lucide/svelte/icons/layers-2";
  import BookOpen from "@lucide/svelte/icons/book-open";
  import Eye from "@lucide/svelte/icons/eye";
  import { HOW_DO_I } from "./demo";

  let {
    onstart,
    onask,
  }: {
    onstart: (kind: "train" | "import" | "workflow") => void;
    onask: (text: string) => void;
  } = $props();

  const ICONS = [GraduationCap, Upload, Workflow, Layers2, BookOpen, Eye];
  const hour = new Date().getHours();
  const hello =
    hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";
</script>

<div class="mx-auto flex max-w-3xl flex-col gap-6 px-6 py-10">
  <div>
    <h2 class="text-2xl font-semibold">{hello}. What shall we do?</h2>
    <p class="text-muted-foreground mt-1 text-sm">
      Ask anything below, type / for shortcuts, or start with one of these. Long
      jobs keep running on your servers after you close QMX.
    </p>
  </div>
  <div>
    <p class="text-muted-foreground mb-2 text-xs font-semibold">How do I…</p>
    <ul class="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
      {#each HOW_DO_I as h, i (h.q)}
        {@const Icon = ICONS[i]}
        <li>
          <button
            type="button"
            class="hover:border-ring/60 hover:bg-muted/40 flex h-full w-full flex-col gap-1 rounded-xl border p-3 text-left"
            onclick={() =>
              h.start
                ? onstart(h.start as "train" | "import" | "workflow")
                : onask(h.ask ?? "")}
          >
            <Icon class="text-primary size-5" />
            <span class="text-sm font-medium">{h.q}</span>
            <span class="text-muted-foreground text-xs">{h.note}</span>
          </button>
        </li>
      {/each}
    </ul>
  </div>
</div>
