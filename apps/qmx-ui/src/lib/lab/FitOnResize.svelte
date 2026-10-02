<script lang="ts">
  /** Refit the graph when its tile is resized, swapped or the copilot opens. */
  import { useSvelteFlow } from "@xyflow/svelte";

  let { target }: { target: HTMLElement | null } = $props();
  const { fitView } = useSvelteFlow();

  $effect(() => {
    if (!target) return;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const ro = new ResizeObserver(() => {
      clearTimeout(timer);
      timer = setTimeout(() => fitView({ padding: 0.08, maxZoom: 1.6 }), 120);
    });
    ro.observe(target);
    return () => {
      clearTimeout(timer);
      ro.disconnect();
    };
  });
</script>
