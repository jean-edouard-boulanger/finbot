import React, { useEffect, useState, useContext } from "react";
import { AuthContext } from "contexts";
import { APP_SERVICE_ENDPOINT } from "utils/env-config";

import { Card, CardContent, CardHeader, CardTitle } from "components/ui/card";
import { Alert, AlertTitle, AlertDescription } from "components/ui/alert";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "components/ui/dropdown-menu";
import { Button } from "components/ui/button";
import { MoneyFormatterType } from "components/money";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";
import { ChartTooltipContent } from "components/ui/chart";
import { ShoppingBag, ChevronDown } from "lucide-react";
import { DateTime } from "luxon";

interface SpendingBreakdownEntry {
  category: string;
  total: number;
  transaction_count: number;
}

interface SpendingBreakdown {
  valuation_ccy: string;
  from_date: string;
  to_date: string;
  entries: SpendingBreakdownEntry[];
}

const SPENDING_COLOURS = [
  "hsl(var(--chart-1))",
  "hsl(var(--chart-2))",
  "hsl(var(--chart-3))",
  "hsl(var(--chart-4))",
  "hsl(var(--chart-5))",
  "hsl(210 60% 55%)",
  "hsl(280 60% 55%)",
  "hsl(30 70% 55%)",
  "hsl(160 50% 45%)",
  "hsl(350 60% 55%)",
];

interface TimeRange {
  from_time?: DateTime;
  to_time?: DateTime;
}

interface TimeRangeChoice {
  label: string;
  makeRange(now: DateTime): TimeRange;
}

const SPENDING_TIME_RANGES: TimeRangeChoice[] = [
  {
    label: "1W",
    makeRange: (now) => ({ from_time: now.minus({ weeks: 1 }) }),
  },
  {
    label: "2W",
    makeRange: (now) => ({ from_time: now.minus({ weeks: 2 }) }),
  },
  {
    label: "1M",
    makeRange: (now) => ({ from_time: now.minus({ month: 1 }) }),
  },
  {
    label: "2M",
    makeRange: (now) => ({ from_time: now.minus({ months: 2 }) }),
  },
  {
    label: "6M",
    makeRange: (now) => ({ from_time: now.minus({ months: 6 }) }),
  },
  {
    label: "1Y",
    makeRange: (now) => ({ from_time: now.minus({ year: 1 }) }),
  },
  {
    label: "THIS YEAR",
    makeRange: (now) => ({
      from_time: DateTime.fromObject({ year: now.year, month: 1, day: 1 }),
    }),
  },
];

const DEFAULT_SPENDING_RANGE = SPENDING_TIME_RANGES[2]; // 1M

function FilterDropdown({
  label,
  items,
  activeKey,
  onSelect,
}: {
  label: string;
  items: { key: string; label: string }[];
  activeKey: string;
  onSelect: (key: string) => void;
}) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          size="xs"
          className="border-border/50 bg-secondary/50 text-xs font-medium tracking-wide text-muted-foreground hover:text-foreground"
        >
          {label} <ChevronDown className="ml-1 h-3 w-3" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent>
        {items.map((item) => (
          <DropdownMenuItem
            key={item.key}
            className={activeKey === item.key ? "bg-accent text-primary" : ""}
            onClick={() => onSelect(item.key)}
          >
            {item.label}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

function formatCategory(raw: string): string {
  return raw
    .replace(/_/g, " ")
    .toLowerCase()
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export interface SpendingBreakdownPanelProps {
  userAccountId: number;
  locale: string;
  moneyFormatter: MoneyFormatterType;
}

export const SpendingBreakdownPanel: React.FC<SpendingBreakdownPanelProps> = (
  props,
) => {
  const { userAccountId, locale, moneyFormatter } = props;
  const { accessToken } = useContext(AuthContext);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<SpendingBreakdown | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [now] = useState<DateTime>(DateTime.now());
  const [selectedTimeRange, setSelectedTimeRange] = useState<TimeRangeChoice>(
    DEFAULT_SPENDING_RANGE,
  );

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        const range = selectedTimeRange.makeRange(now);
        const params = new URLSearchParams();
        if (range.from_time) {
          params.set("from_time", range.from_time.toISO()!);
        }
        if (range.to_time) {
          params.set("to_time", range.to_time.toISO()!);
        }
        const qs = params.toString();
        const url = `${APP_SERVICE_ENDPOINT}/reports/spending/breakdown/${qs ? `?${qs}` : ""}`;
        const resp = await fetch(url, {
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const json = await resp.json();
        setData(json.report);
      } catch (e) {
        setError(`${e}`);
      }
      setLoading(false);
    };
    fetchData();
  }, [accessToken, userAccountId, now, selectedTimeRange]);

  if (error) {
    return (
      <Card className="border-border/50">
        <CardContent className="pt-6">
          <Alert variant="destructive">
            <AlertTitle>Failed to load spending data</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  const hasData = data && data.entries.length > 0;

  const chartData = hasData
    ? data.entries.map((entry, i) => ({
        name: formatCategory(entry.category),
        value: entry.total,
        count: entry.transaction_count,
        fill: SPENDING_COLOURS[i % SPENDING_COLOURS.length],
      }))
    : [];

  return (
    <Card className="border-border/50 flex flex-col h-full">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="flex items-center gap-2 text-muted-foreground">
          <ShoppingBag className="h-4 w-4" />
          <CardTitle className="text-sm font-medium tracking-wide uppercase">
            Spending Breakdown
          </CardTitle>
        </div>
        <FilterDropdown
          label={selectedTimeRange.label}
          items={SPENDING_TIME_RANGES.map((r) => ({
            key: r.label,
            label: r.label,
          }))}
          activeKey={selectedTimeRange.label}
          onSelect={(key) =>
            setSelectedTimeRange(
              SPENDING_TIME_RANGES.find((r) => r.label === key)!,
            )
          }
        />
      </CardHeader>
      <CardContent className="flex-1 flex flex-col">
        {loading || !data ? (
          <div className="skeleton-shimmer h-[300px] rounded flex-1" />
        ) : !hasData ? (
          <div className="flex flex-1 items-center justify-center text-sm text-muted-foreground">
            No spending data available yet.
          </div>
        ) : (
          <div className="flex items-center gap-4">
            <ResponsiveContainer width="60%" height={280}>
              <PieChart>
                <Pie
                  data={chartData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={100}
                  paddingAngle={2}
                  stroke="hsl(var(--background))"
                  strokeWidth={2}
                >
                  {chartData.map((entry, index) => (
                    <Cell key={index} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip content={<ChartTooltipContent />} />
              </PieChart>
            </ResponsiveContainer>
            <div className="flex flex-1 flex-col gap-1.5">
              {chartData.slice(0, 8).map((entry, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between gap-2 text-xs"
                >
                  <div className="flex items-center gap-1.5">
                    <span
                      className="inline-block h-2.5 w-2.5 rounded-sm"
                      style={{ backgroundColor: entry.fill }}
                    />
                    <span className="text-muted-foreground">{entry.name}</span>
                  </div>
                  <span className="font-mono tabular-nums">
                    {moneyFormatter(entry.value, locale, data.valuation_ccy)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
