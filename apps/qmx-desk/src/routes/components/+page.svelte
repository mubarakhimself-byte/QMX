<script lang="ts">
  import { places } from "$lib/shell/data";
  import { shell, type Look } from "$lib/shell/state.svelte";
  import { Button } from "$lib/components/ui/button";
  import Frame from "$lib/qmx/Frame.svelte";
  import Icon, { icons } from "$lib/qmx/Icon.svelte";
  import IconButton from "$lib/qmx/IconButton.svelte";
  import { tone, stateLabel } from "$lib/qmx/state";

  // The component library on one page. Screens and the copilot build from these.
  const pick = (place: string, id: string) => places.find((p) => p.id === place)!.board.flat().find((p) => p.id === id)!;
  const samples = [pick("home", "needs"), pick("home", "units"), pick("library", "inspect"), pick("trading", "live"), pick("home", "going")];
  const looks: Look[] = ["night", "terminal"];
</script>

<div class="app h-full overflow-y-auto p-10" data-look={shell.look}>
  <header class="mb-10 flex items-end gap-6">
    <div>
      <a href="/" class="text-muted-foreground text-sm hover:underline">Back to the app</a>
      <h1 class="display mt-1 text-5xl font-semibold">Components</h1>
    </div>
    <span class="flex-1"></span>
    <div class="flex gap-1.5">
      {#each looks as l (l)}
        <button class="key h-9 px-3 capitalize" data-on={shell.look === l} onclick={() => shell.setLook(l)}>{l}</button>
      {/each}
    </div>
  </header>

  <section class="mb-12">
    <h2 class="display mb-4 text-2xl font-semibold">What each colour means</h2>
    <div class="flex flex-wrap gap-x-8 gap-y-3">
      {#each Object.entries(stateLabel) as [k, label] (k)}
        <span class="flex items-center gap-2"><span class="dot {tone[k]}"></span>{label}</span>
      {/each}
    </div>
  </section>

  <section class="mb-12">
    <h2 class="display mb-4 text-2xl font-semibold">Controls</h2>
    <div class="flex flex-wrap items-center gap-4">
      <Button>Promote to paper</Button>
      <Button variant="outline">Start from a template</Button>
      <Button variant="ghost">Cancel</Button>
      <Button variant="destructive">Stop all trading</Button>
      <button class="key h-9 px-3" data-on="true">Selected</button>
      <button class="key h-9 px-3">Not selected</button>
      <IconButton icon="send" label="Send to the copilot" />
      <IconButton icon="expand" label="Open in a tab" />
      <span class="well bg-panel px-3 py-1.5">A well holds data or typing</span>
    </div>
  </section>

  <section class="mb-12">
    <h2 class="display mb-4 text-2xl font-semibold">The frame and what goes inside it</h2>
    <div class="grid grid-cols-[repeat(auto-fill,minmax(26rem,1fr))] gap-4">
      {#each samples as p (p.id)}
        <div class="flex h-80 flex-col [&>section]:flex-1"><Frame panel={p} /></div>
      {/each}
    </div>
  </section>

  <section>
    <h2 class="display mb-4 text-2xl font-semibold">Icons</h2>
    <div class="text-muted-foreground flex flex-wrap gap-4">
      {#each Object.keys(icons) as name (name)}
        <span class="flex w-28 flex-col items-center gap-1.5 text-center text-xs"><Icon {name} class="text-foreground size-5" />{name}</span>
      {/each}
    </div>
  </section>
</div>
