"use client";

import { createChart, ColorType, type IChartApi, type UTCTimestamp } from "lightweight-charts";
import { useEffect, useRef } from "react";
import type { Bar } from "@/lib/types";

export function PriceChart({ bars }: { bars: Bar[] }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const chart: IChartApi = createChart(el, {
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "rgb(151,160,177)",
        fontFamily: "var(--font-mono), monospace",
        fontSize: 11,
      },
      grid: {
        vertLines: { color: "rgba(33,39,53,0.5)" },
        horzLines: { color: "rgba(33,39,53,0.5)" },
      },
      rightPriceScale: { borderColor: "rgba(33,39,53,0.8)" },
      timeScale: { borderColor: "rgba(33,39,53,0.8)", timeVisible: false },
      crosshair: {
        vertLine: { color: "rgba(214,178,122,0.4)", labelBackgroundColor: "#1a1f2b" },
        horzLine: { color: "rgba(214,178,122,0.4)", labelBackgroundColor: "#1a1f2b" },
      },
      height: 360,
      autoSize: true,
    });

    const series = chart.addCandlestickSeries({
      upColor: "rgb(56,201,138)",
      downColor: "rgb(244,100,110)",
      borderVisible: false,
      wickUpColor: "rgba(56,201,138,0.7)",
      wickDownColor: "rgba(244,100,110,0.7)",
    });
    series.setData(
      bars.map((b) => ({
        time: (Date.parse(b.time) / 1000) as UTCTimestamp,
        open: b.open,
        high: b.high,
        low: b.low,
        close: b.close,
      })),
    );
    chart.timeScale().fitContent();

    return () => chart.remove();
  }, [bars]);

  return <div ref={ref} className="h-[360px] w-full" />;
}
