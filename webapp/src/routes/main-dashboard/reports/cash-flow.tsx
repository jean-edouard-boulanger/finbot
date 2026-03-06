import React, { useEffect, useState, useContext } from "react";
import { AuthContext } from "contexts";
import { APP_SERVICE_ENDPOINT } from "utils/env-config";

import { Card, CardContent, CardHeader, CardTitle } from "components/ui/card";
import { Alert, AlertTitle, AlertDescription } from "components/ui/alert";
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
} from "recharts";
import { ChartTooltipContent } from "components/ui/chart";
import { TrendingUp } from "lucide-react";

interface CashFlowTimeSeriesEntry {
  period: string;
  income: number;
  expense: number;
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
}

export const CashFlowPanel: React.FC<CashFlowPanelProps> = (props) => {
  const { userAccountId, locale, moneyFormatter } = props;
  const { accessToken } = useContext(AuthContext);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<CashFlowTimeSeries | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const resp = await fetch(
          `${APP_SERVICE_ENDPOINT}/reports/cash-flow/time-series/?frequency=monthly`,
          {
            headers: {
              Authorization: `Bearer ${accessToken}`,
            },
          },
        );
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const json = await resp.json();
        setData(json.report);
      } catch (e) {
        setError(`${e}`);
      }
      setLoading(false);
    };
    fetchData();
  }, [accessToken, userAccountId]);

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
      <CardHeader className="pb-2">
        <div className="flex items-center gap-2 text-muted-foreground">
          <TrendingUp className="h-4 w-4" />
          <CardTitle className="text-sm font-medium tracking-wide uppercase">
            Cash Flow
          </CardTitle>
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
                dataKey="income"
                name="Income"
                fill="hsl(var(--gain))"
                radius={[2, 2, 0, 0]}
                maxBarSize={40}
              />
              <Bar
                dataKey="expense"
                name="Expense"
                fill="hsl(var(--loss))"
                radius={[2, 2, 0, 0]}
                maxBarSize={40}
              />
            </BarChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
};
