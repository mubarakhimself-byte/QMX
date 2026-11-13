<script lang="ts">
  import * as Menu from "$lib/components/ui/dropdown-menu";
  import Icon from "$lib/qmx/Icon.svelte";
  import { shell, type At } from "./state.svelte";
  import { things } from "./things.svelte";

  // The top left says where you are and leads back: Back (Esc), the place,
  // then each page opened from it. A deep trail keeps its first and last two
  // steps; the middle folds into "…". A widget opened in its own tab is a
  // step too, with a close button.
  const placeName = $derived(shell.place.startsWith("app:") ? (things.guest(shell.place.slice(4))?.name ?? "Mini app") : shell.current.name);
  const listName = (l: string) => shell.places.find((p) => p.id === l)?.name ?? l;
  const label = (a: At) => {
    const o = things.get(a.id);
    if (a.sub) return o?.sections?.find((s) => s.id === a.sub)?.title ?? a.sub;
    return o?.name ?? "Not found";
  };
  type Step = { label: string; go: () => void };
  // A page opened from a list the place is not shows that list as the step before it.
  const steps = $derived(
    shell.stack.flatMap((a, i): Step[] => {
      const prev = shell.stack[i - 1];
      const listStep = a.list && a.list !== shell.current.list && prev?.list !== a.list;
      return [...(listStep ? [{ label: listName(a.list!), go: () => shell.go(a.list!) }] : []), { label: label(a), go: () => shell.jump(i) }];
    }),
  );
  const d = $derived(shell.activeDetail);
  const others = $derived(shell.details.filter((x) => x.place === shell.place && x.id !== shell.detail));
  const hidden = $derived(steps.length > 2 ? steps.slice(0, -2) : []);
  const tail = $derived(steps.length > 2 ? steps.slice(-2) : steps);
  const deep = $derived(steps.length > 0 || !!d);
</script>

<nav class="flex min-w-0 items-center gap-1" aria-label="Where you are">
  {#if shell.canBack}
    <button class="press size-9 shrink-0" aria-label="Back (Esc)" title="Back (Esc)" onclick={() => shell.back()}><Icon name="arrow-left" /></button>
  {/if}
  <button
    class="display min-w-[3rem] shrink-0 truncate rounded-md px-1.5 py-0.5 text-left text-xl font-semibold whitespace-nowrap {deep ? 'text-muted-foreground hover:text-foreground max-w-[12rem] transition-colors duration-150' : 'max-w-[16rem]'}"
    title={placeName}
    aria-current={deep ? undefined : "page"}
    onclick={() => shell.jump(-1)}
  >
    {placeName}
  </button>
  {#if d}
    <Icon name="chevron-right" class="text-muted-foreground size-3.5 shrink-0" />
    <span class="key h-8 min-w-0 shrink gap-1.5 pr-1 pl-2.5" data-on="true">
      <Icon name={d.panel.icon} class="size-3.5 shrink-0" />
      <span class="max-w-48 truncate" title={d.panel.title}>{d.panel.title}</span>
      <button class="grid size-5 shrink-0 place-items-center rounded opacity-60 hover:opacity-100" aria-label="Close {d.panel.title}" onclick={() => shell.closeDetail(d.id)}>
        <Icon name="x" class="size-3" />
      </button>
    </span>
  {/if}
  {#if others.length && !steps.length}
    <Menu.Root>
      <Menu.Trigger>
        {#snippet child({ props })}
          <button {...props} class="key num h-8 shrink-0 px-2 text-sm" title="Widgets open in a tab">+{others.length}</button>
        {/snippet}
      </Menu.Trigger>
      <Menu.Content align="start" class="w-64">
        {#each others as x (x.id)}
          <Menu.Item onclick={() => shell.openDetail(x.id)}><Icon name={x.panel.icon} /><span class="truncate">{x.panel.title}</span></Menu.Item>
        {/each}
      </Menu.Content>
    </Menu.Root>
  {/if}
  {#if hidden.length}
    <Icon name="chevron-right" class="text-muted-foreground size-3.5 shrink-0" />
    <Menu.Root>
      <Menu.Trigger>
        {#snippet child({ props })}
          <button {...props} class="press h-8 shrink-0 px-2" aria-label="{hidden.length} more steps back" title="{hidden.length} more steps back">…</button>
        {/snippet}
      </Menu.Trigger>
      <Menu.Content align="start" class="w-80">
        {#each hidden as t, n (n)}
          <Menu.Item onclick={t.go}><span class="truncate">{t.label}</span></Menu.Item>
        {/each}
      </Menu.Content>
    </Menu.Root>
  {/if}
  {#each tail as t, n (n)}
    {@const last = n === tail.length - 1}
    <Icon name="chevron-right" class="text-muted-foreground size-3.5 shrink-0" />
    <button
      class="min-w-0 truncate rounded-md px-2 py-1 text-left transition-colors duration-150 {last ? 'text-foreground max-w-[26rem] shrink font-medium' : 'text-muted-foreground hover:text-foreground hover:bg-accent max-w-[11rem] min-w-[4rem] shrink-[3]'}"
      title={t.label}
      aria-current={last ? "page" : undefined}
      onclick={t.go}
    >
      {t.label}
    </button>
  {/each}
</nav>
