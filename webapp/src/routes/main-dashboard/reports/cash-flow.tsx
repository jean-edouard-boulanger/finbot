import React, { useEffect, useState, useContext } from "react";
import { AuthContext } from "contexts";
import { APP_SERVICE_ENDPOINT } from "utils/env-config";

import { Card, CardContent, CardHeader } from "components/ui/card";
import { Alert, AlertTitle, AlertDescription } from "components/ui/alert";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "components/ui/dropdown-menu";
import { Button } from "components/ui/button";
import { MoneyFormatterType } from "components/money";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  CartesianGrid,
  Cell,
} from "recharts";
import { ChartTooltipContent } from "components/ui/chart";
import { ChevronDown } from "lucide-react";
import { DateTime } from "luxon";
import { lastItem } from "utils/array";

interface TimeRange {
  from_time?: DateTime;
  to_time?: DateTime;
}

interface TimeRangeChoiceType {
  label: string;
  makeRange(now: DateTime): TimeRange;
}

const TIME_RANGES: Array<TimeRangeChoiceType> = [
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
    label: "2Y",
    makeRange: (now) => ({ from_time: now.minus({ year: 2 }) }),
  },
  {
    label: "5Y",
    makeRange: (now) => ({ from_time: now.minus({ year: 5 }) }),
  },
  {
    label: "LAST YEAR",
    makeRange: (now) => ({
      from_time: DateTime.fromObject({ year: now.year - 1, month: 1, day: 1 }),
      to_time: DateTime.fromObject({
        year: now.year - 1,
        month: 12,
        day: 31,
        hour: 23,
        minute: 59,
      }),
    }),
  },
  {
    label: "THIS YEAR",
    makeRange: (now) => ({
      from_time: DateTime.fromObject({ year: now.year, month: 1, day: 1 }),
    }),
  },
  {
    label: "ALL DATA",
    makeRange: () => ({}),
  },
];

const DEFAULT_TIME_RANGE = lastItem(TIME_RANGES)!;

interface CashFlowTimeSeriesEntry {
  period: string;
  net: number;
}

interface CashFlowTimeSeries {
  valuation_ccy: string;
  entries: CashFlowTimeSeriesEntry[];
}

export interface CashFlowPanelProps {
  userAccountId: number;
  locale: string;
  moneyFormatter: MoneyFormatterType;
  linkedAccountId?: number;
}

const FREQUENCIES = ["Daily", "Weekly", "Monthly"] as const;
type Frequency = Lowercase<(typeof FREQUENCIES)[number]>;

const DEFAULT_FREQUENCY = FREQUENCIES[2];

export const CashFlowPanel: React.FC<CashFlowPanelProps> = (props) => {
  const { userAccountId, locale, moneyFormatter, linkedAccountId } = props;
  const { accessToken } = useContext(AuthContext);
  const [now] = useState<DateTime>(DateTime.now());
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<CashFlowTimeSeries | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedFrequency, setSelectedFrequency] =
    useState<(typeof FREQUENCIES)[number]>(DEFAULT_FREQUENCY);
  const [selectedTimeRange, setSelectedTimeRange] =
    useState<TimeRangeChoiceType>(DEFAULT_TIME_RANGE);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const frequency = selectedFrequency.toLowerCase() as Frequency;
        const range = selectedTimeRange.makeRange(now);
        let url = `${APP_SERVICE_ENDPOINT}/reports/cash-flow/time-series/?frequency=${frequency}`;
        if (range.from_time) {
          url += `&from_time=${range.from_time.toISO()}`;
        }
        if (range.to_time) {
          url += `&to_time=${range.to_time.toISO()}`;
        }
        if (linkedAccountId !== undefined) {
          url += `&linked_account_id=${linkedAccountId}`;
        }
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
  }, [
    accessToken,
    userAccountId,
    linkedAccountId,
    selectedFrequency,
    selectedTimeRange,
    now,
  ]);

  if (error) {
    return (
      <Card className="border-border/50">
        <CardContent className="pt-6">
          <Alert variant="destructive">
            <AlertTitle>Failed to load cash flow data</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  const hasData = data && data.entries.length > 0;

  return (
    <Card className="border-border/50">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <span className="text-sm font-medium tracking-wide uppercase text-muted-foreground">
          Cash Flow
        </span>
        <div className="flex gap-1">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="outline"
                size="xs"
                className="border-border/50 bg-secondary/50 text-xs font-medium tracking-wide text-muted-foreground hover:text-foreground"
              >
                {selectedFrequency.toUpperCase()}{" "}
                <ChevronDown className="ml-1 h-3 w-3" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent>
              {FREQUENCIES.map((f) => (
                <DropdownMenuItem
                  key={f}
                  className={
                    selectedFrequency === f ? "bg-accent text-primary" : ""
                  }
                  onClick={() => setSelectedFrequency(f)}
                >
                  {f.toUpperCase()}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="outline"
                size="xs"
                className="border-border/50 bg-secondary/50 text-xs font-medium tracking-wide text-muted-foreground hover:text-foreground"
              >
                {selectedTimeRange.label}{" "}
                <ChevronDown className="ml-1 h-3 w-3" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent>
              {TIME_RANGES.map((r) => (
                <DropdownMenuItem
                  key={r.label}
                  className={
                    selectedTimeRange.label === r.label
                      ? "bg-accent text-primary"
                      : ""
                  }
                  onClick={() => setSelectedTimeRange(r)}
                >
                  {r.label}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </CardHeader>
      <CardContent>
        {loading || !data ? (
          <div className="skeleton-shimmer h-[300px] rounded" />
        ) : !hasData ? (
          <div className="flex h-[300px] items-center justify-center text-sm text-muted-foreground">
            No cash flow data available yet.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart
              data={data.entries}
              margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="hsl(var(--border))"
                opacity={0.3}
              />
              <XAxis
                dataKey="period"
                tick={{ fontSize: 11 }}
                stroke="hsl(var(--muted-foreground))"
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                tick={{ fontSize: 11 }}
                stroke="hsl(var(--muted-foreground))"
                tickLine={false}
                axisLine={false}
                tickFormatter={(v: number) =>
                  moneyFormatter(v, locale, data.valuation_ccy)
                }
              />
              <Tooltip
                content={<ChartTooltipContent />}
                cursor={{ fill: "hsl(var(--muted))", opacity: 0.3 }}
              />
              <ReferenceLine y={0} stroke="hsl(var(--border))" />
              <Bar
                dataKey="net"
                name="Net"
                radius={[2, 2, 0, 0]}
                maxBarSize={40}
              >
                {data.entries.map((entry, index) => (
                  <Cell
                    key={index}
                    fill={
                      entry.net >= 0 ? "hsl(var(--gain))" : "hsl(var(--loss))"
                    }
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
};
