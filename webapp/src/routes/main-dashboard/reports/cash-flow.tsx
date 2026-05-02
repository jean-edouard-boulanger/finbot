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
import { DateRangeFilter } from "components/date-range-filter";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  CartesianGrid,
} from "recharts";
import { ChartTooltipContent } from "components/ui/chart";
import { ChevronDown } from "lucide-react";
import { DateTime } from "luxon";

interface CashFlowTimeSeriesEntry {
  period: string;
  inflows: number;
  outflows: number;
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
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<CashFlowTimeSeries | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedFrequency, setSelectedFrequency] =
    useState<(typeof FREQUENCIES)[number]>(DEFAULT_FREQUENCY);
  const [fromDate, setFromDate] = useState<string>("");
  const [toDate, setToDate] = useState<string>("");

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const frequency = selectedFrequency.toLowerCase() as Frequency;
        let url = `${APP_SERVICE_ENDPOINT}/reports/cash-flow/time-series/?frequency=${frequency}`;
        if (fromDate) {
          url += `&from_time=${DateTime.fromISO(fromDate).startOf("day").toISO()}`;
        }
        if (toDate) {
          url += `&to_time=${DateTime.fromISO(toDate).endOf("day").toISO()}`;
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
    fromDate,
    toDate,
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
                {selectedFrequency} <ChevronDown className="ml-1 h-3 w-3" />
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
                  {f}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
          <DateRangeFilter
            fromDate={fromDate}
            toDate={toDate}
            onFromDateChange={setFromDate}
            onToDateChange={setToDate}
            compact
            allowAllTime
          />
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
                dataKey="inflows"
                name="Inflows"
                fill="hsl(var(--gain))"
                radius={[2, 2, 0, 0]}
                maxBarSize={20}
              />
              <Bar
                dataKey="outflows"
                name="Outflows"
                fill="hsl(var(--loss))"
                radius={[0, 0, 2, 2]}
                maxBarSize={20}
              />
            </BarChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
};
