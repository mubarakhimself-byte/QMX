<script lang="ts">
  import { onMount } from "svelte";
  import {
    createChart,
    CandlestickSeries,
    HistogramSeries,
    ColorType,
    type IChartApi,
  } from "lightweight-charts";
  import type { Candle } from "./data";

  let { candles }: { candles: Candle[] } = $props();
  let el: HTMLDivElement;

  /**
   * Resolve a theme token to rgba(). Tokens are oklch, which
   * lightweight-charts cannot parse, so paint one pixel and read it back.
   */
  function token(name: string): string {
    const probe = document.createElement("span");
    probe.style.color = `var(${name})`;
    document.body.appendChild(probe);
    const css = getComputedStyle(probe).color;
    probe.remove();
    const ctx = document.createElement("canvas").getContext("2d");
    if (!ctx) return "#888888";
    ctx.fillStyle = css;
    ctx.fillRect(0, 0, 1, 1);
    const [r, g, b, a] = ctx.getImageData(0, 0, 1, 1).data;
    return `rgba(${r}, ${g}, ${b}, ${(a / 255).toFixed(3)})`;
  }

  onMount(() => {
    const up = token("--success");
    const down = token("--destructive");
    const chart: IChartApi = createChart(el, {
      autoSize: true,
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: token("--muted-foreground"),
        fontSize: 11,
        attributionLogo: false,
      },
      grid: {
        vertLines: { color: token("--border") },
        horzLines: { color: token("--border") },
      },
      rightPriceScale: { borderVisible: false },
      timeScale: { borderVisible: false },
      crosshair: { mode: 1 },
    });
    const series = chart.addSeries(CandlestickSeries, {
      upColor: up,
      downColor: down,
      borderVisible: false,
      wickUpColor: up,
      wickDownColor: down,
      priceFormat: { type: "price", precision: 5, minMove: 0.00001 },
    });
    series.setData(candles);
    const volume = chart.addSeries(HistogramSeries, {
      priceScaleId: "",
      priceFormat: { type: "volume" },
      color: token("--muted"),
    });
    volume
      .priceScale()
      .applyOptions({ scaleMargins: { top: 0.82, bottom: 0 } });
    volume.setData(candles.map((c) => ({ time: c.time, value: c.volume })));
    chart.timeScale().fitContent();
    return () => chart.remove();
  });
</script>

<div
  bind:this={el}
  class="h-full min-h-40 w-full"
  aria-label="Candlestick chart (demo data)"
  role="img"
></div>
