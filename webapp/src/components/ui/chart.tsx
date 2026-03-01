import * as React from "react";
import { Tooltip } from "recharts";
import { ResponsiveContainer } from "recharts";

// --- Types ---

export type ChartConfig = Record<
  string,
  {
    label: string;
    color: string;
  }
>;

// --- Context ---

const ChartContext = React.createContext<ChartConfig | null>(null);

function useChartConfig(): ChartConfig | null {
  return React.useContext(ChartContext);
}

// --- ChartContainer ---

export interface ChartContainerProps
  extends React.HTMLAttributes<HTMLDivElement> {
  config: ChartConfig;
  children: React.ReactElement;
}

export const ChartContainer = React.forwardRef<
  HTMLDivElement,
  ChartContainerProps
>(({ config, children, className, style, ...props }, ref) => {
  const cssVars = Object.entries(config).reduce<Record<string, string>>(
    (acc, [key, value]) => {
      acc[`--color-${key}`] = value.color;
      return acc;
    },
    {},
  );

  return (
    <ChartContext.Provider value={config}>
      <div
        ref={ref}
        className={className}
        style={{ ...cssVars, ...style } as React.CSSProperties}
        {...props}
      >
        <ResponsiveContainer width="100%" height="100%">
          {children}
        </ResponsiveContainer>
      </div>
    </ChartContext.Provider>
  );
});
ChartContainer.displayName = "ChartContainer";

// --- ChartTooltip ---

export const ChartTooltip = Tooltip;

// --- ChartTooltipContent ---

export interface ChartTooltipContentProps {
  active?: boolean;
  payload?: Array<{
    name: string;
    value: number;
    color: string;
    dataKey: string;
    payload: Record<string, unknown>;
  }>;
  label?: string;
  formatter?: (value: number, name: string) => string;
  labelFormatter?: (label: string) => string;
}

export const ChartTooltipContent: React.FC<ChartTooltipContentProps> = ({
  active,
  payload,
  label,
  formatter,
  labelFormatter,
}) => {
  const config = useChartConfig();

  if (!active || !payload?.length) {
    return null;
  }

  const formattedLabel = labelFormatter ? labelFormatter(label ?? "") : label;

  return (
    <div className="rounded-lg border border-border/50 bg-popover px-3 py-2.5 text-sm text-popover-foreground shadow-xl backdrop-blur-sm">
      {formattedLabel && (
        <div className="mb-1.5 text-xs font-medium tracking-wide uppercase text-muted-foreground">
          {formattedLabel}
        </div>
      )}
      <div className="flex flex-col gap-1.5">
        {payload.map((entry, i) => {
          const displayLabel =
            config?.[entry.dataKey]?.label ?? entry.name ?? entry.dataKey;
          const displayValue = formatter
            ? formatter(entry.value, entry.name)
            : entry.value;
          return (
            <div key={i} className="flex items-center gap-2">
              <span
                className="h-2.5 w-2.5 shrink-0 rounded-sm"
                style={{ backgroundColor: entry.color }}
              />
              <span className="text-muted-foreground">{displayLabel}</span>
              <span className="ml-auto font-mono font-medium tabular-nums">
                {displayValue}
              </span>
            </div>
          );
        })}
        {payload.length > 1 && (() => {
          const total = payload.reduce((sum, entry) => sum + (entry.value ?? 0), 0);
          return (
            <div className="mt-1 flex items-center gap-2 border-t border-border/50 pt-1.5">
              <span className="text-muted-foreground">Total</span>
              <span className="ml-auto font-mono font-medium tabular-nums">
                {formatter ? formatter(total, "Total") : total}
              </span>
            </div>
          );
        })()}
      </div>
    </div>
  );
};
