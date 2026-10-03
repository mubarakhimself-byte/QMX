<script lang="ts">
  /** Why this size: one trade walked through the pod, a bar per block. */
  import { usd } from "$lib/portfolio/bits";
  import { SIZE_TRAIL } from "../pods";

  const max = SIZE_TRAIL[0].usd;
</script>

<div class="flex h-full flex-col gap-1 overflow-auto p-3">
  <p class="text-muted-foreground mb-1 text-xs">
    BTC breakout · buy at 64,150, stop 63,500
  </p>
  {#each SIZE_TRAIL as s, i (s.step)}
    {@const prev = i ? SIZE_TRAIL[i - 1].usd : s.usd}
    <div class="grid grid-cols-[1fr_5rem] items-center gap-3">
      <div>
        <p class="text-sm">{s.step}</p>
        <div class="bg-muted relative mt-1 h-3 overflow-hidden rounded-sm">
          <span
            class="bg-destructive/30 absolute inset-y-0 left-0"
            style="width:{(prev / max) * 100}%"
          ></span>
          <span
            class="bg-primary absolute inset-y-0 left-0"
            style="width:{(s.usd / max) * 100}%"
          ></span>
        </div>
      </div>
      <span class="num text-right text-lg">{usd(s.usd, s.usd % 1 ? 2 : 0)}</span
      >
    </div>
  {/each}
</div>
