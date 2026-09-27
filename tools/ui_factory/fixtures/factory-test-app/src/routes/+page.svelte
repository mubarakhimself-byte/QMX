<script lang="ts">
  import { resolve } from "$app/paths";
  import { onMount } from "svelte";
  import { STORAGE_KEY, readNote, writeNote } from "$lib/persist";
  import "$lib/tokens.css";

  let draft = $state("");
  let saved = $state("");
  let revision = $state("factory-test");

  onMount(() => {
    saved = readNote(window.localStorage.getItem(STORAGE_KEY));
    draft = saved;
    const meta = document.querySelector('meta[name="qmx-revision"]');
    if (meta) {
      revision = meta.getAttribute("content") ?? revision;
    }
  });

  function save() {
    const next = writeNote(draft);
    window.localStorage.setItem(STORAGE_KEY, next);
    saved = next;
  }

  function dead() {
    // FACTORY-TEST: intentionally does nothing so Playwright can catch it.
  }
</script>

<main>
  <p data-testid="label">FACTORY-TEST host (not product chrome)</p>
  <p data-testid="revision">{revision}</p>
  <label>
    Note
    <input data-testid="note" bind:value={draft} />
  </label>
  <button type="button" data-testid="save" onclick={save}>Save</button>
  <button type="button" data-testid="dead" onclick={dead}>Dead</button>
  <p data-testid="saved">{saved}</p>
  <a href={resolve("/catalog")}>Catalog</a>
</main>
