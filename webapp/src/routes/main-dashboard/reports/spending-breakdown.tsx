import React, { useEffect, useState, useContext } from "react";
import { AuthContext } from "contexts";
import { APP_SERVICE_ENDPOINT } from "utils/env-config";

import { Card, CardContent, CardHeader, CardTitle } from "components/ui/card";
import { Alert, AlertTitle, AlertDescription } from "components/ui/alert";
import { MoneyFormatterType } from "components/money";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";
import { ChartTooltipContent } from "components/ui/chart";
import { ShoppingBag } from "lucide-react";

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

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const resp = await fetch(
          `${APP_SERVICE_ENDPOINT}/reports/spending/breakdown/`,
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
        count: entry.transactionCount,
        fill: SPENDING_COLOURS[i % SPENDING_COLOURS.length],
      }))
    : [];

  return (
    <Card className="border-border/50">
      <CardHeader className="pb-2">
        <div className="flex items-center gap-2 text-muted-foreground">
          <ShoppingBag className="h-4 w-4" />
          <CardTitle className="text-sm font-medium tracking-wide uppercase">
            Spending Breakdown
          </CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        {loading || !data ? (
          <div className="skeleton-shimmer h-[300px] rounded" />
        ) : !hasData ? (
          <div className="flex h-[300px] items-center justify-center text-sm text-muted-foreground">
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
