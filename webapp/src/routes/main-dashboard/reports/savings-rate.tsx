import React, { useEffect, useState, useContext, useMemo } from "react";
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
import { PiggyBank, ChevronDown, TrendingUp, TrendingDown } from "lucide-react";
import { DateTime } from "luxon";

interface MonthlySavingsEntry {
  month: string;
  income: number;
  expenses: number;
  savings: number;
  savings_rate: number | null;
  projected_income: number | null;
  projected_expenses: number | null;
  projected_savings: number | null;
  projected_savings_rate: number | null;
}

interface SavingsRateReport {
  valuation_ccy: string;
  current_month: MonthlySavingsEntry;
  comparison_month: MonthlySavingsEntry;
}

function buildMonthChoices(): { value: string; label: string }[] {
  const now = DateTime.now();
  const choices: { value: string; label: string }[] = [];
  for (let i = 1; i <= 12; i++) {
    const dt = now.minus({ months: i });
    choices.push({
      value: dt.toFormat("yyyy-MM"),
      label: dt.toFormat("LLL yyyy"),
    });
  }
  return choices;
}

function formatRate(rate: number | null): string {
  if (rate === null) return "N/A";
  return `${(rate * 100).toFixed(1)}%`;
}

function formatMonth(month: string): string {
  const dt = DateTime.fromFormat(month, "yyyy-MM");
  return dt.isValid ? dt.toFormat("LLL yyyy") : month;
}

function MonthColumn({
  entry,
  label,
  ccy,
  locale,
  moneyFormatter,
  showProjection,
}: {
  entry: MonthlySavingsEntry;
  label: string;
  ccy: string;
  locale: string;
  moneyFormatter: MoneyFormatterType;
  showProjection: boolean;
}) {
  const hasProjection = showProjection && entry.projected_savings_rate !== null;

  return (
    <div className="flex-1 space-y-3">
      <div className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
        {label}
      </div>
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Income</span>
          <span className="font-mono tabular-nums">
            {moneyFormatter(entry.income, locale, ccy)}
          </span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Expenses</span>
          <span className="font-mono tabular-nums">
            {moneyFormatter(entry.expenses, locale, ccy)}
          </span>
        </div>
        <div className="border-t border-border/50 pt-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Savings</span>
            <span
              className={`font-mono tabular-nums font-medium ${entry.savings >= 0 ? "text-gain" : "text-loss"}`}
            >
              {moneyFormatter(entry.savings, locale, ccy)}
            </span>
          </div>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Rate</span>
          <span
            className={`font-mono tabular-nums font-semibold ${
              entry.savings_rate === null
                ? "text-muted-foreground"
                : entry.savings_rate >= 0
                  ? "text-gain"
                  : "text-loss"
            }`}
          >
            {formatRate(entry.savings_rate)}
          </span>
        </div>
        {hasProjection && (
          <div className="border-t border-dashed border-border/50 pt-2 space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground/70 italic">
                Proj. savings
              </span>
              <span className="font-mono tabular-nums text-muted-foreground/70 italic">
                {entry.projected_savings !== null
                  ? moneyFormatter(entry.projected_savings, locale, ccy)
                  : "N/A"}
              </span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground/70 italic">
                Proj. expenses
              </span>
              <span className="font-mono tabular-nums text-muted-foreground/70 italic">
                {entry.projected_expenses !== null
                  ? moneyFormatter(entry.projected_expenses, locale, ccy)
                  : "N/A"}
              </span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground/70 italic">
                Proj. rate
              </span>
              <span className="font-mono tabular-nums text-muted-foreground/70 italic">
                {formatRate(entry.projected_savings_rate)}
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export interface SavingsRatePanelProps {
  userAccountId: number;
  locale: string;
  moneyFormatter: MoneyFormatterType;
}

export const SavingsRatePanel: React.FC<SavingsRatePanelProps> = (props) => {
  const { userAccountId, locale, moneyFormatter } = props;
  const { accessToken } = useContext(AuthContext);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<SavingsRateReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  const monthChoices = useMemo(() => buildMonthChoices(), []);
  const [comparisonMonth, setComparisonMonth] = useState<string>(
    monthChoices[0].value,
  );

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        const url = `${APP_SERVICE_ENDPOINT}/reports/savings-rate/?comparison_month=${comparisonMonth}`;
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
  }, [accessToken, userAccountId, comparisonMonth]);

  if (error) {
    return (
      <Card className="border-border/50">
        <CardContent className="pt-6">
          <Alert variant="destructive">
            <AlertTitle>Failed to load savings rate</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  const delta =
    data &&
    data.current_month.savings_rate !== null &&
    data.comparison_month.savings_rate !== null
      ? data.current_month.savings_rate - data.comparison_month.savings_rate
      : null;

  return (
    <Card className="border-border/50 flex flex-col h-full">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="flex items-center gap-2 text-muted-foreground">
          <PiggyBank className="h-4 w-4" />
          <CardTitle className="text-sm font-medium tracking-wide uppercase">
            Savings Rate
          </CardTitle>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="outline"
              size="xs"
              className="border-border/50 bg-secondary/50 text-xs font-medium tracking-wide text-muted-foreground hover:text-foreground"
            >
              vs{" "}
              {monthChoices.find((c) => c.value === comparisonMonth)?.label ??
                comparisonMonth}{" "}
              <ChevronDown className="ml-1 h-3 w-3" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            {monthChoices.map((choice) => (
              <DropdownMenuItem
                key={choice.value}
                className={
                  comparisonMonth === choice.value
                    ? "bg-accent text-primary"
                    : ""
                }
                onClick={() => setComparisonMonth(choice.value)}
              >
                {choice.label}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col">
        {loading || !data ? (
          <div className="skeleton-shimmer h-[300px] rounded flex-1" />
        ) : (
          <div className="flex gap-6 flex-1">
            <MonthColumn
              entry={data.comparison_month}
              label={formatMonth(data.comparison_month.month)}
              ccy={data.valuation_ccy}
              locale={locale}
              moneyFormatter={moneyFormatter}
              showProjection={false}
            />
            <div className="flex flex-col items-center justify-center gap-1">
              <div className="h-full w-px bg-border/50" />
              {delta !== null && (
                <div
                  className={`flex items-center gap-0.5 rounded-full border px-2 py-0.5 font-mono text-xs tabular-nums ${
                    delta >= 0
                      ? "border-gain/30 bg-gain/10 text-gain"
                      : "border-loss/30 bg-loss/10 text-loss"
                  }`}
                >
                  {delta >= 0 ? (
                    <TrendingUp className="h-3 w-3" />
                  ) : (
                    <TrendingDown className="h-3 w-3" />
                  )}
                  {delta >= 0 ? "+" : ""}
                  {(delta * 100).toFixed(1)}pp
                </div>
              )}
              <div className="h-full w-px bg-border/50" />
            </div>
            <MonthColumn
              entry={data.current_month}
              label={formatMonth(data.current_month.month)}
              ccy={data.valuation_ccy}
              locale={locale}
              moneyFormatter={moneyFormatter}
              showProjection={true}
            />
          </div>
        )}
      </CardContent>
    </Card>
  );
};
