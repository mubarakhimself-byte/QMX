<script lang="ts" module>
  /** Markers drawn on the candles, e.g. agent signals (time = candle date). */
  export type ChartMarker = { time: string; text: string };
</script>

<script lang="ts">
  import { onMount } from "svelte";
  import {
    createChart,
    CandlestickSeries,
    HistogramSeries,
    ColorType,
    createSeriesMarkers,
    type IChartApi,
  } from "lightweight-charts";
  import type { Candle } from "./data";

  let {
    candles,
    markers = [],
    precision = 5,
  }: {
    candles: Candle[];
    markers?: ChartMarker[];
    precision?: number;
  } = $props();
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
      priceFormat: { type: "price", precision, minMove: 1 / 10 ** precision },
    });
    series.setData(candles);
    if (markers.length) {
      const agent = token("--info");
      createSeriesMarkers(
        series,
        markers.map((m) => ({
          time: m.time,
          position: "belowBar" as const,
          color: agent,
          shape: "arrowUp" as const,
          text: m.text,
        })),
      );
    }
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
  class="solid-backing h-full min-h-40 w-full"
  aria-label="Candlestick chart (demo data)"
  role="img"
></div>
