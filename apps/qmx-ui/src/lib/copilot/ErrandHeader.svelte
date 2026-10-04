<script lang="ts">
  /**
   * The top of an errand: what it is for, how far it has got, and the one
   * thing that matters now. Its work (helpers, reports, changes, terminal,
   * browser) opens on request instead of sitting on screen.
   */
  import Users from "@lucide/svelte/icons/users";
  import FileText from "@lucide/svelte/icons/file-text";
  import FileDiff from "@lucide/svelte/icons/file-diff";
  import SquareTerminal from "@lucide/svelte/icons/square-terminal";
  import Globe from "@lucide/svelte/icons/globe";
  import CornerUpLeft from "@lucide/svelte/icons/corner-up-left";
  import { Button } from "$lib/components/ui/button";
  import { cn } from "$lib/utils";
  import type { Block, Session } from "./demo";

  let {
    session,
    blocks,
    parent,
    waiting,
    busy,
    onopen,
    onback,
  }: {
    session: Session;
    blocks: Block[];
    parent?: Session;
    waiting: boolean;
    busy: boolean;
    onopen: (tab: string) => void;
    onback?: () => void;
  } = $props();

  const plan = $derived(
    [...blocks].reverse().find((b) => b.kind === "plan") as
      Extract<Block, { kind: "plan" }> | undefined,
  );
  const now = $derived(
    plan?.steps.find((s) => s.state === "running" || s.state === "waiting"),
  );
  const done = $derived(
    plan?.steps.filter((s) => s.state === "done").length ?? 0,
  );
  const helpers = $derived(
    blocks.reduce((n, b) => n + (b.kind === "agents" ? b.agents.length : 0), 0),
  );
  const reports = $derived(blocks.filter((b) => b.kind === "artifact").length);
  const changes = $derived(
    blocks.reduce(
      (n, b) => n + (b.kind === "changes" ? b.changes.length : 0),
      0,
    ),
  );
  const status = $derived(
    busy
      ? "Writing a reply…"
      : waiting
        ? "Waiting for you"
        : session.status === "running"
          ? `Working · ${session.age}`
          : session.age === "Now"
            ? "New"
            : `Last active ${session.age.toLowerCase()}`,
  );
  const TONE = {
    done: "bg-success",
    running: "bg-info remote-pulse",
    waiting: "bg-warning",
    scheduled: "bg-muted",
  };
</script>

<header class="border-b">
  <div class="mx-auto flex w-full max-w-[46rem] flex-col gap-3 px-8 pt-7 pb-5">
    {#if parent && onback}
      <button
        type="button"
        class="text-muted-foreground hover:text-foreground flex w-fit items-center gap-2 text-sm"
        onclick={onback}
        ><CornerUpLeft class="size-4" />Helper of “{parent.title}”. It sees only
        its task.</button
      >
    {/if}
    <div class="flex items-start gap-4">
      <div class="min-w-0 flex-1">
        <h2 class="text-2xl leading-tight font-semibold">{session.title}</h2>
        {#if session.goal}<p
            class="text-muted-foreground mt-1.5 leading-relaxed"
          >
            {session.goal}
          </p>{/if}
      </div>
      <span
        class={cn(
          "mt-1 shrink-0 rounded-full px-3 py-1 text-sm",
          waiting
            ? "bg-warning/15 text-warning"
            : busy || session.status === "running"
              ? "bg-info/15 text-info"
              : "bg-muted text-muted-foreground",
        )}>{status}</span
      >
    </div>

    {#if plan}
      <div>
        <div
          class="flex gap-1.5"
          aria-label={`${done} of ${plan.steps.length} steps done`}
        >
          {#each plan.steps as s, i (i)}
            <span
              class={cn("h-1.5 flex-1 rounded-full", TONE[s.state])}
              title={s.text}
            ></span>
          {/each}
        </div>
        <p class="mt-2 text-sm">
          <span class="text-muted-foreground"
            >Step {Math.min(done + 1, plan.steps.length)} of {plan.steps
              .length}:</span
          >
          {now?.text ?? "All steps done"}
        </p>
      </div>
    {/if}

    {#if helpers || reports || changes}
      <div class="flex flex-wrap gap-2">
        {#if helpers}<Button
            size="sm"
            variant="outline"
            onclick={() => onopen("activity")}
            ><Users />{helpers} helpers</Button
          >{/if}
        {#if reports}<Button
            size="sm"
            variant="outline"
            onclick={() => onopen("preview")}
            ><FileText />{reports}
            {reports === 1 ? "report" : "reports"}</Button
          >{/if}
        {#if changes}<Button
            size="sm"
            variant="outline"
            onclick={() => onopen("diff")}><FileDiff />{changes} changes</Button
          >{/if}
        <Button size="sm" variant="ghost" onclick={() => onopen("terminal")}
          ><SquareTerminal />Terminal</Button
        >
        <Button size="sm" variant="ghost" onclick={() => onopen("browser")}
          ><Globe />Browser</Button
        >
      </div>
    {/if}
  </div>
</header>
