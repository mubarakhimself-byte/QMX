<script lang="ts">
  import { shell, type Fixture } from "./state.svelte";

  // Design-review chrome. Not part of QMX and never shipped. One small pill:
  // which data the app shows, and the text size.
  const fixtures: [Fixture, string][] = [
    ["demo", "Demo"],
    ["worst", "Worst case"],
    ["first", "Day one"],
  ];
  const texts: [string, string][] = [
    ["standard", "A"],
    ["large", "A+"],
    ["larger", "A++"],
  ];
  $effect(() => {
    document.documentElement.dataset.text = shell.text;
  });
</script>

<nav class="proto-picker" data-side="right" aria-label="Review: data and text size">
  {#each fixtures as [id, label] (id)}
    <button class="proto-picker-item" data-active={shell.fixture === id ? "" : undefined} onclick={() => shell.setFixture(id)}>{label}</button>
  {/each}
  <span class="proto-picker-divider" aria-hidden="true"></span>
  {#each texts as [id, label] (id)}
    <button class="proto-picker-item" data-active={shell.text === id ? "" : undefined} onclick={() => shell.setText(id)} aria-label="Text size {id}">{label}</button>
  {/each}
</nav>
