import React, { useMemo } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { ChartTooltipContent } from "components/ui/chart";
import type { RichBlock } from "./types";

type ChartBlockType = Extract<RichBlock, { kind: "chart" }>;

// Chat-drawer-friendly palette — matches the violet/indigo accent used elsewhere in the drawer.
const SERIES_COLOURS = ["#8b5cf6", "#06b6d4", "#22c55e", "#f59e0b", "#ec4899"];

// Three-letter ISO code → currency symbol cheap path; falls back to the code itself.
const CCY_SYMBOLS: Record<string, string> = {
  GBP: "£",
  USD: "$",
  EUR: "€",
  JPY: "¥",
  CHF: "CHF ",
  CAD: "C$",
  AUD: "A$",
};

function isCurrency(unit: string | null | undefined): boolean {
  return !!unit && unit !== "%" && unit.length <= 4;
}

function makeAxisFormatter(
  unit: string | null | undefined,
): (v: number) => string {
  if (unit === "%") {
    return (v: number) => `${v.toFixed(0)}%`;
  }
  if (isCurrency(unit)) {
    const symbol = CCY_SYMBOLS[unit!.toUpperCase()] ?? `${unit} `;
    return (v: number) => {
      const abs = Math.abs(v);
      if (abs >= 1_000_000) return `${symbol}${(v / 1_000_000).toFixed(1)}M`;
      if (abs >= 1_000) return `${symbol}${(v / 1_000).toFixed(1)}k`;
      return `${symbol}${v.toFixed(0)}`;
    };
  }
  return (v: number) => v.toLocaleString();
}

function makeTooltipFormatter(
  unit: string | null | undefined,
): (v: number) => string {
  if (unit === "%") {
    return (v: number) => `${v.toFixed(2)}%`;
  }
  if (isCurrency(unit)) {
    const symbol = CCY_SYMBOLS[unit!.toUpperCase()] ?? `${unit} `;
    return (v: number) =>
      `${symbol}${v.toLocaleString(undefined, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })}`;
  }
  return (v: number) => v.toLocaleString();
}

export function ChartBlockView({
  block,
}: {
  block: ChartBlockType;
}): React.JSX.Element {
  const data = useMemo(() => {
    return block.x_axis_labels.map((label, i) => {
      const row: Record<string, number | string | null> = { label };
      for (const s of block.series) {
        row[s.name] = s.data[i] ?? null;
      }
      return row;
    });
  }, [block]);

  const axisFmt = useMemo(
    () => makeAxisFormatter(block.y_unit),
    [block.y_unit],
  );
  const tooltipFmt = useMemo(
    () => makeTooltipFormatter(block.y_unit),
    [block.y_unit],
  );

  const ChartCmp =
    block.chart_type === "bar"
      ? BarChart
      : block.chart_type === "area"
        ? AreaChart
        : LineChart;

  return (
    <div className="mt-3 overflow-hidden rounded-lg border border-border/60 bg-card/50">
      <div className="border-b border-border/60 bg-muted/30 px-3 py-1.5 text-xs font-medium text-muted-foreground">
        {block.title}
      </div>
      <div className="h-48 w-full px-2 py-3">
        <ResponsiveContainer width="100%" height="100%">
          <ChartCmp
            data={data}
            margin={{ top: 8, right: 12, left: 0, bottom: 0 }}
          >
            <CartesianGrid
              stroke="currentColor"
              strokeOpacity={0.08}
              vertical={false}
            />
            <XAxis
              dataKey="label"
              tick={{ fontSize: 10, fill: "currentColor", fillOpacity: 0.65 }}
              tickLine={false}
              axisLine={false}
              minTickGap={16}
            />
            <YAxis
              tick={{ fontSize: 10, fill: "currentColor", fillOpacity: 0.65 }}
              tickLine={false}
              axisLine={false}
              tickFormatter={axisFmt}
              width={48}
            />
            <Tooltip
              cursor={{
                stroke: "currentColor",
                strokeOpacity: 0.15,
                strokeWidth: 1,
              }}
              content={<ChartTooltipContent formatter={tooltipFmt} />}
            />
            {block.series.map((s, i) => {
              const colour = SERIES_COLOURS[i % SERIES_COLOURS.length];
              if (block.chart_type === "bar") {
                return (
                  <Bar
                    key={s.name}
                    dataKey={s.name}
                    fill={colour}
                    radius={[3, 3, 0, 0]}
                  />
                );
              }
              if (block.chart_type === "area") {
                return (
                  <Area
                    key={s.name}
                    type="monotone"
                    dataKey={s.name}
                    stroke={colour}
                    fill={colour}
                    fillOpacity={0.15}
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 3 }}
                  />
                );
              }
              return (
                <Line
                  key={s.name}
                  type="monotone"
                  dataKey={s.name}
                  stroke={colour}
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 3 }}
                />
              );
            })}
          </ChartCmp>
        </ResponsiveContainer>
      </div>
      {block.footer && (
        <div className="border-t border-border/40 bg-muted/20 px-3 py-1.5 text-xs italic text-muted-foreground">
          {block.footer}
        </div>
      )}
    </div>
  );
}
