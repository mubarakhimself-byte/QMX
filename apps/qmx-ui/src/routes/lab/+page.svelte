<script lang="ts">
  /**
   * The Lab (operator ruling 2026-10-02): Authoring, Backtest lab and ML Studio
   * in one permanent section. A tiling board with saved layouts (Build, Test,
   * Train, Compare, and your own), linked tiles, a dock for minimised tiles,
   * and a Lab copilot. Docs still call this destination Authoring (DEC-0470);
   * the rename is flagged for Codex.
   */
  import DemoChip from "$lib/workbench/DemoChip.svelte";
  import { page } from "$app/state";
  import { resolve } from "$app/paths";
  import FlaskConical from "@lucide/svelte/icons/flask-conical";
  import Layers2 from "@lucide/svelte/icons/layers-2";
  import ChevronDown from "@lucide/svelte/icons/chevron-down";
  import Play from "@lucide/svelte/icons/play";
  import Plus from "@lucide/svelte/icons/plus";
  import Pencil from "@lucide/svelte/icons/pencil";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import RotateCcw from "@lucide/svelte/icons/rotate-ccw";
  import Save from "@lucide/svelte/icons/save";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import { Button } from "$lib/components/ui/button";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu";
  import * as Resizable from "$lib/components/ui/resizable";
  import * as Dialog from "$lib/components/ui/dialog";
  import { Input } from "$lib/components/ui/input";
  import { cn } from "$lib/utils";
  import TileBoard from "$lib/workbench/tiles/TileBoard.svelte";
  import { addPane, pane } from "$lib/workbench/tiles/tiles";
  import CopilotColumn from "$lib/workbench/CopilotColumn.svelte";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { LAB_PANELS } from "$lib/lab/catalog";
  import { lab } from "$lib/lab/lab.svelte";
  import { ASSETS, ENVIRONMENTS, activity } from "$lib/lab/demo";
  import EnvChip from "$lib/lab/EnvChip.svelte";
  import { LAB_CONTEXT } from "$lib/lab/copilot";
  import StartDialog from "$lib/lab/StartDialog.svelte";
  import MachinePicker from "$lib/lab/MachinePicker.svelte";
  import MachineEmpty from "$lib/lab/MachineEmpty.svelte";
  import LabStrips from "$lib/lab/LabStrips.svelte";
  import { GUIDES } from "$lib/lab/guides";
  import { LAB_PODS, POD_TEMPLATES, STAGE_LABEL } from "$lib/lab/pods";
  import { FIRST } from "$lib/workbench/day-one";

  // Old links to the four pod tabs land on the Pods bench's three.
  const OLD: Record<string, string> = {
    pods: "pod-design",
    podtest: "pod-test",
    podcompare: "pod-test",
    allocate: "pod-test",
  };
  const asked = page.url.searchParams.get("layout");
  const fromUrl = asked ? (OLD[asked] ?? asked) : null;
  if (fromUrl && lab.layouts.some((l) => l.id === fromUrl))
    lab.activeId = fromUrl;
  const BENCHES = [
    { id: "strategies", label: "Strategies", icon: FlaskConical },
    { id: "pods", label: "Pods", icon: Layers2 },
  ];
  const pod = $derived(LAB_PODS.find((p) => p.id === lab.labPod)!);

  const SUBJECTS = ASSETS.filter((a) =>
    ["bot", "template", "model"].includes(a.kind),
  );
  let subject = $state(SUBJECTS.find((s) => s.id === "bot-gbm")!);
  const guideId = page.url.searchParams.get("guide");
  if (guideId && GUIDES[guideId]) lab.startGuide(GUIDES[guideId]);

  const catalog = Object.fromEntries(
    Object.entries(LAB_PANELS).map(([id, p]) => [
      id,
      { title: p.title, icon: p.icon, note: p.note },
    ]),
  );

  function addPanel(id: string) {
    const l = lab.active;
    const tileId = `${id}-${Date.now().toString(36)}`;
    lab.update({ ...l, root: addPane(l.root, pane(tileId, id)) });
    workbench.notify(`${LAB_PANELS[id].title} added to ${l.name}.`);
  }
  let saving = $state(false);
  let starting = $state(false);
  let layoutName = $state("");
  function openSave() {
    layoutName = `${lab.active.name} (mine)`;
    saving = true;
  }
  function saveLayout(e: SubmitEvent) {
    e.preventDefault();
    const l = lab.saveAs(layoutName);
    saving = false;
    workbench.notify(`Saved layout: ${l.name}`);
  }
  function run() {
    const env = ENVIRONMENTS.find((e) => e.id === (lab.machine ?? "local"))!;
    if (lab.bench === "pods") {
      if (lab.activeId !== "pod-test") lab.activeId = "pod-test";
      workbench.notify(
        `Testing needs the daemon. It would replay ${lab.botsTicked.length} bots through ${lab.podsTicked.length} pods and ${lab.stressTicked.length} stress scenarios on ${env.name}.`,
      );
      return;
    }
    workbench.notify(
      `Running needs the daemon. It would run the published version of ${subject.name} on ${env.name}.`,
    );
  }
</script>

<div class="scrim flex h-full flex-col">
  <header class="flex h-12 shrink-0 items-center gap-3 border-b px-3">
    <h1 class="text-base font-semibold">Lab</h1>
    <DemoChip note="Sample runs, models and machines. Nothing here ran." />
    <div
      class="bg-muted flex rounded-lg p-0.5"
      role="radiogroup"
      aria-label="Bench"
    >
      {#each BENCHES as b (b.id)}
        <button
          type="button"
          role="radio"
          aria-checked={lab.bench === b.id}
          class={cn(
            "flex h-7 items-center gap-1.5 rounded-md px-2.5 text-sm",
            lab.bench === b.id
              ? "bg-background text-foreground font-medium shadow-sm"
              : "text-muted-foreground hover:text-foreground",
          )}
          onclick={() => lab.setBench(b.id)}
          ><b.icon class="size-3.5" />{b.label}</button
        >
      {/each}
    </div>
    {#if !workbench.demoMode}
      {@const first = lab.bench === "pods" ? FIRST.pod : FIRST.template}
      {@const [path, query] = first.href.split("?")}
      <!-- eslint-disable svelte/no-navigation-without-resolve -- resolved path plus a query string -->
      <Button
        variant="ghost"
        size="sm"
        href={`${resolve(path as "/")}${query ? `?${query}` : ""}`}
        ><Plus />{first.label}</Button
      >
      <!-- eslint-enable svelte/no-navigation-without-resolve -->
    {:else if lab.bench === "pods"}
      <DropdownMenu.Root>
        <DropdownMenu.Trigger>
          {#snippet child({ props })}
            <Button {...props} variant="ghost" size="sm" class="gap-1.5">
              <span class="text-muted-foreground hidden text-xs 2xl:inline"
                >Working on</span
              >
              <span class="size-2 rounded-full" style="background:{pod.color}"
              ></span>
              {pod.name}
              {pod.version}<ChevronDown class="size-3.5" />
            </Button>
          {/snippet}
        </DropdownMenu.Trigger>
        <DropdownMenu.Content class="w-72">
          {#each LAB_PODS as p (p.id)}
            <DropdownMenu.Item onclick={() => (lab.labPod = p.id)}>
              <span class="size-2 rounded-full" style="background:{p.color}"
              ></span>
              <span class="flex flex-1 flex-col">
                <span>{p.name} {p.version}</span>
                <span class="text-muted-foreground text-xs">{p.template}</span>
              </span>
              <span class="text-muted-foreground text-xs"
                >{STAGE_LABEL[p.stage]}</span
              >
            </DropdownMenu.Item>
          {/each}
          <DropdownMenu.Separator />
          <DropdownMenu.Item
            onclick={() =>
              lab.ask(
                "Build me a new pod for my momentum bots: risk about 0.5% a trade, stop everything at -10%, and slow down on weekends.",
              )}><Sparkles />New pod with the copilot</DropdownMenu.Item
          >
          <DropdownMenu.Sub>
            <DropdownMenu.SubTrigger
              ><Plus />New pod from a template</DropdownMenu.SubTrigger
            >
            <DropdownMenu.SubContent class="w-64">
              {#each POD_TEMPLATES as t (t.id)}
                <DropdownMenu.Item
                  onclick={() =>
                    workbench.notify(
                      `A draft from "${t.name}" opens in Design. Nothing changes until you save it.`,
                    )}
                >
                  <span class="flex flex-col"
                    ><span>{t.name}</span><span
                      class="text-muted-foreground text-xs">{t.note}</span
                    ></span
                  >
                </DropdownMenu.Item>
              {/each}
            </DropdownMenu.SubContent>
          </DropdownMenu.Sub>
        </DropdownMenu.Content>
      </DropdownMenu.Root>
    {:else}
      <DropdownMenu.Root>
        <DropdownMenu.Trigger>
          {#snippet child({ props })}
            <Button {...props} variant="ghost" size="sm" class="gap-1.5">
              <span class="text-muted-foreground hidden text-xs 2xl:inline"
                >Working on</span
              >
              {subject.name}<ChevronDown class="size-3.5" />
            </Button>
          {/snippet}
        </DropdownMenu.Trigger>
        <DropdownMenu.Content class="w-64">
          {#each SUBJECTS as s (s.id)}
            <DropdownMenu.Item onclick={() => (subject = s)}>
              <span class="flex flex-col">
                <span>{s.name}</span>
                <span class="text-muted-foreground text-xs">{s.meta}</span>
              </span>
            </DropdownMenu.Item>
          {/each}
          <DropdownMenu.Separator />
          <DropdownMenu.Item onclick={() => (starting = true)}
            ><Plus />Start something new</DropdownMenu.Item
          >
        </DropdownMenu.Content>
      </DropdownMenu.Root>
    {/if}

    <nav class="flex items-center gap-0.5" aria-label="Layouts">
      {#each lab.benchLayouts as l (l.id)}
        <button
          type="button"
          class={cn(
            "h-7 rounded-md px-3 text-sm whitespace-nowrap",
            lab.activeId === l.id
              ? "bg-muted text-foreground font-medium"
              : "text-muted-foreground hover:text-foreground",
          )}
          aria-current={lab.activeId === l.id ? "page" : undefined}
          onclick={() => (lab.activeId = l.id)}
          >{l.name}{#if lab.isEdited(l.id)}<span
              class="text-muted-foreground"
              title="Changed from the default">*</span
            >{/if}{#if lab.machine && workbench.demoMode}{@const n = activity(
              lab.machine,
              l.id,
            )}<span
              class="num ml-1.5 rounded px-1 text-xs {n
                ? 'bg-info/15 text-info'
                : 'text-muted-foreground/60'}"
              title={`${n} on this machine`}>{n}</span
            >{/if}</button
        >
      {/each}
      <DropdownMenu.Root>
        <DropdownMenu.Trigger>
          {#snippet child({ props })}
            <Button
              {...props}
              variant="ghost"
              size="icon-sm"
              aria-label="Layout options"><ChevronDown /></Button
            >
          {/snippet}
        </DropdownMenu.Trigger>
        <DropdownMenu.Content>
          <DropdownMenu.Item onclick={openSave}
            ><Save />Save as a new layout</DropdownMenu.Item
          >
          {#if lab.isBuiltin(lab.activeId)}
            <DropdownMenu.Item
              disabled={!lab.isEdited(lab.activeId)}
              onclick={() => lab.reset(lab.activeId)}
              ><RotateCcw />Reset {lab.active.name} to default</DropdownMenu.Item
            >
          {:else}
            <DropdownMenu.Item onclick={() => lab.reset(lab.activeId)}
              ><Trash2 />Delete {lab.active.name}</DropdownMenu.Item
            >
          {/if}
        </DropdownMenu.Content>
      </DropdownMenu.Root>
    </nav>

    <div class="ml-auto flex items-center gap-1.5">
      <Button
        variant={lab.editing ? "secondary" : "ghost"}
        size="sm"
        aria-pressed={lab.editing}
        onclick={() => (lab.editing = !lab.editing)}
        title={lab.editing ? "Done" : "Edit layout"}
        ><Pencil /><span class="hidden 2xl:inline"
          >{lab.editing ? "Done" : "Edit layout"}</span
        ></Button
      >
      <DropdownMenu.Root>
        <DropdownMenu.Trigger>
          {#snippet child({ props })}
            <Button {...props} variant="ghost" size="sm" title="Add a panel"
              ><Plus /><span class="hidden 2xl:inline">Panel</span></Button
            >
          {/snippet}
        </DropdownMenu.Trigger>
        <DropdownMenu.Content align="end" class="w-64">
          {#each Object.entries(LAB_PANELS).filter(([id]) => id !== "pinned") as [id, p] (id)}
            <DropdownMenu.Item onclick={() => addPanel(id)}>
              <p.icon />
              <span class="flex flex-col">
                <span>{p.title}</span>
                <span class="text-muted-foreground text-xs">{p.note}</span>
              </span>
            </DropdownMenu.Item>
          {/each}
          <DropdownMenu.Separator />
          <DropdownMenu.Item
            onclick={() => {
              lab.copilotOpen = true;
              workbench.notify(
                "Describe the panel you want; the Lab copilot builds it from your data.",
              );
            }}><Sparkles />Build a new panel…</DropdownMenu.Item
          >
        </DropdownMenu.Content>
      </DropdownMenu.Root>
      <span class="bg-border mx-1 h-5 w-px"></span>
      <MachinePicker />
      <Button
        size="sm"
        onclick={run}
        disabled={!workbench.demoMode}
        title={workbench.demoMode ? undefined : "Nothing to run yet"}
        ><Play />{lab.bench === "pods" ? "Run test" : "Run"}</Button
      >
      <Button
        variant={lab.copilotOpen ? "secondary" : "ghost"}
        size="icon-sm"
        aria-label="Toggle Lab copilot"
        aria-pressed={lab.copilotOpen}
        onclick={() => (lab.copilotOpen = !lab.copilotOpen)}
        ><Sparkles /></Button
      >
    </div>
  </header>
  <LabStrips />

  <Resizable.PaneGroup direction="horizontal" class="min-h-0 flex-1">
    <Resizable.Pane defaultSize={lab.copilotOpen ? 76 : 100} minSize={50}>
      {#if workbench.demoMode && lab.machine && activity(lab.machine, lab.activeId) === 0}
        <MachineEmpty machine={lab.machine} onstart={() => (starting = true)} />
      {:else}
        <TileBoard
          class="p-1.5"
          layout={lab.active}
          {catalog}
          editing={lab.editing}
          onchange={(next) => lab.update(next)}
        >
          {#snippet panel(p)}
            {@const View = LAB_PANELS[p.panel].view}
            <View link={p.link} tile={p.id} />
          {/snippet}
        </TileBoard>
      {/if}
    </Resizable.Pane>
    {#if lab.copilotOpen}
      <Resizable.Handle />
      <Resizable.Pane defaultSize={24} minSize={16} maxSize={40}>
        <CopilotColumn
          title="Lab copilot"
          profile="lab"
          hint={lab.bench === "pods"
            ? `Knows ${pod.name}, its blocks, every pod test and paper run. Ask it to build a block, a stress scenario or a mix.`
            : `Knows ${subject.name}, the open layout and every run. Ask it to build a step, a panel, a test or a sweep.`}
          placeholder={lab.bench === "pods"
            ? "Make a stress scenario where…"
            : "Sweep this across the top coins on 1h and 4h…"}
          seed={lab.copilotSeed}
          onclose={() => (lab.copilotOpen = false)}
          refs={workbench.copilotRefs}
          onremoveref={(r) => workbench.removeRef(r)}
          context={LAB_CONTEXT}
          origin="Lab"
          starters={lab.bench === "pods"
            ? [
                `Why did ${pod.name} refuse the AVAX entry this morning?`,
                "Build a stress scenario from the March 2020 crash",
                "Make a block that halves size after three losses in a row",
                "Split $20,000 across the ticked pods to keep dips under 8%",
              ]
            : [
                `Sweep ${subject.name} across six markets on 1h and 4h`,
                "Why did the USOIL M15 run fail?",
                "Compare the three ticked runs and say what changed",
                "Build a panel showing drawdown by session",
              ]}
        />
      </Resizable.Pane>
    {/if}
  </Resizable.PaneGroup>
</div>

<Dialog.Root bind:open={saving}>
  <Dialog.Content class="sm:max-w-md">
    <form class="flex flex-col gap-4" onsubmit={saveLayout}>
      <Dialog.Header>
        <Dialog.Title>Save this layout</Dialog.Title>
        <Dialog.Description
          >Keeps the tiles, their sizes, links and what is minimised. It appears
          next to this bench's other layouts.</Dialog.Description
        >
      </Dialog.Header>
      <Input bind:value={layoutName} maxlength={40} aria-label="Layout name" />
      <Dialog.Footer>
        <Button type="button" variant="ghost" onclick={() => (saving = false)}
          >Cancel</Button
        >
        <Button type="submit" disabled={!layoutName.trim()}>Save layout</Button>
      </Dialog.Footer>
    </form>
  </Dialog.Content>
</Dialog.Root>

<StartDialog bind:open={starting} />
