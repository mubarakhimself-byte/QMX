<script lang="ts">
  /**
   * CodeMirror 6 editor themed from QMX tokens. Edits stay local until the
   * draft is saved through the daemon (save_editor_draft).
   */
  import { onMount } from "svelte";
  import { EditorView, basicSetup } from "codemirror";
  import { EditorState } from "@codemirror/state";
  import { python } from "@codemirror/lang-python";

  let {
    value,
    onchange,
    readonly = false,
    label = "Code",
  }: {
    value: string;
    onchange?: (v: string) => void;
    readonly?: boolean;
    label?: string;
  } = $props();

  let el: HTMLDivElement;
  let view: EditorView | undefined;

  const theme = EditorView.theme({
    "&": {
      height: "100%",
      fontSize: "13px",
      backgroundColor: "transparent",
      color: "var(--foreground)",
    },
    ".cm-scroller": {
      fontFamily: '"JetBrains Mono Variable", ui-monospace, monospace',
      lineHeight: "1.65",
    },
    ".cm-gutters": {
      backgroundColor: "transparent",
      color: "var(--muted-foreground)",
      border: "none",
    },
    ".cm-activeLine, .cm-activeLineGutter": {
      backgroundColor: "color-mix(in oklab, var(--foreground) 5%, transparent)",
    },
    ".cm-cursor": { borderLeftColor: "var(--primary)" },
    "&.cm-focused .cm-selectionBackground, .cm-selectionBackground, ::selection":
      {
        backgroundColor:
          "color-mix(in oklab, var(--primary) 30%, transparent) !important",
      },
    "&.cm-focused": { outline: "none" },
  });

  onMount(() => {
    view = new EditorView({
      parent: el,
      state: EditorState.create({
        doc: value,
        extensions: [
          basicSetup,
          python(),
          theme,
          EditorState.readOnly.of(readonly),
          EditorView.contentAttributes.of({ "aria-label": label }),
          EditorView.updateListener.of((u) => {
            if (u.docChanged) onchange?.(u.state.doc.toString());
          }),
        ],
      }),
    });
    return () => view?.destroy();
  });

  // Swap the document when a different step is opened.
  $effect(() => {
    const next = value;
    if (view && view.state.doc.toString() !== next) {
      view.dispatch({
        changes: { from: 0, to: view.state.doc.length, insert: next },
      });
    }
  });
</script>

<div bind:this={el} class="h-full min-h-0 overflow-hidden"></div>
