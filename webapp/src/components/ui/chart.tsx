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
    <div className="bg-background text-foreground border-border/50 rounded-md border px-3 py-2 text-sm shadow-md">
      {formattedLabel && (
        <div className="mb-1 font-medium">{formattedLabel}</div>
      )}
      <div className="flex flex-col gap-1">
        {payload.map((entry, i) => {
          const displayLabel =
            config?.[entry.dataKey]?.label ?? entry.name ?? entry.dataKey;
          const displayValue = formatter
            ? formatter(entry.value, entry.name)
            : entry.value;
          return (
            <div key={i} className="flex items-center gap-2">
              <span
                className="h-2.5 w-2.5 shrink-0 rounded-full"
                style={{ backgroundColor: entry.color }}
              />
              <span className="text-muted-foreground">{displayLabel}</span>
              <span className="ml-auto font-medium">{displayValue}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
