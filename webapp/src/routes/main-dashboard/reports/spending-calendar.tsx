import React, { useEffect, useState, useContext, useMemo } from "react";
import { AuthContext } from "contexts";
import { APP_SERVICE_ENDPOINT } from "utils/env-config";

import { Card, CardContent, CardHeader, CardTitle } from "components/ui/card";
import { Alert, AlertTitle, AlertDescription } from "components/ui/alert";
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
  TooltipProvider,
} from "components/ui/tooltip";
import { MoneyFormatterType } from "components/money";
import { CalendarDays, ChevronLeft, ChevronRight } from "lucide-react";
import { DateTime, Info } from "luxon";

interface SpendingCalendarRecurringPayment {
  subscription_id: number;
  merchant_name: string;
  description: string | null;
  currency: string;
  avg_amount: number;
  is_projected: boolean;
}

interface SpendingCalendarDay {
  date: string;
  total_spending: number;
  recurring_payments: SpendingCalendarRecurringPayment[];
}

interface SpendingCalendarReport {
  valuation_ccy: string;
  start_date: string;
  end_date: string;
  max_daily_spending: number;
  days: SpendingCalendarDay[];
}

export interface SpendingCalendarPanelProps {
  userAccountId: number;
  locale: string;
  moneyFormatter: MoneyFormatterType;
}

export const SpendingCalendarPanel: React.FC<SpendingCalendarPanelProps> = (
  props,
) => {
  const { userAccountId, locale, moneyFormatter } = props;
  const { accessToken } = useContext(AuthContext);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<SpendingCalendarReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  const now = DateTime.now();
  const [selectedMonth, setSelectedMonth] = useState(now.toFormat("yyyy-MM"));

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        const url = `${APP_SERVICE_ENDPOINT}/reports/spending-calendar/?month=${selectedMonth}`;
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
  }, [accessToken, userAccountId, selectedMonth]);

  const dayDataMap = useMemo(() => {
    if (!data) return new Map<string, SpendingCalendarDay>();
    const map = new Map<string, SpendingCalendarDay>();
    for (const day of data.days) {
      map.set(day.date, day);
    }
    return map;
  }, [data]);

  const maxSpending = data?.max_daily_spending ?? 0;
  const valuationCcy = data?.valuation_ccy ?? "";

  const getHeatmapStyle = (
    totalSpending: number,
    isToday: boolean,
  ): React.CSSProperties => {
    if (isToday || maxSpending <= 0 || totalSpending <= 0) return {};
    const ratio = Math.max(0.1, Math.min(1.0, totalSpending / maxSpending));
    return {
      backgroundColor: `hsl(var(--loss) / ${(ratio * 0.35).toFixed(2)})`,
    };
  };

  const monthDt = DateTime.fromFormat(selectedMonth, "yyyy-MM");
  const daysInMonth = monthDt.daysInMonth ?? 30;
  // Monday = 1 in Luxon; we want Mon as first column
  const firstWeekday = monthDt.startOf("month").weekday; // 1=Mon, 7=Sun
  const leadingBlanks = firstWeekday - 1;
  const todayStr = now.toFormat("yyyy-MM-dd");
  const dayAbbreviations = Info.weekdays("short");

  const goPrev = () => {
    setSelectedMonth(
      DateTime.fromFormat(selectedMonth, "yyyy-MM")
        .minus({ months: 1 })
        .toFormat("yyyy-MM"),
    );
  };
  const goNext = () => {
    setSelectedMonth(
      DateTime.fromFormat(selectedMonth, "yyyy-MM")
        .plus({ months: 1 })
        .toFormat("yyyy-MM"),
    );
  };

  if (error) {
    return (
      <Card className="border-border/50">
        <CardContent className="pt-6">
          <Alert variant="destructive">
            <AlertTitle>Failed to load calendar</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="flex h-full max-h-[420px] flex-col border-border/50">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="flex items-center gap-2 text-muted-foreground">
          <CalendarDays className="h-4 w-4" />
          <CardTitle className="text-sm font-medium uppercase tracking-wide">
            Spending Calendar
          </CardTitle>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={goPrev}
            className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          <span className="min-w-[120px] text-center text-sm font-medium">
            {monthDt.toFormat("LLLL yyyy")}
          </span>
          <button
            onClick={goNext}
            className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      </CardHeader>
      <CardContent className="flex min-h-0 flex-1 flex-col">
        {loading || !data ? (
          <div className="skeleton-shimmer h-[300px] flex-1 rounded" />
        ) : (
          <TooltipProvider delayDuration={150}>
            <div className="grid flex-1 auto-rows-fr grid-cols-7 gap-px">
              {/* Day name headers */}
              {dayAbbreviations.map((d) => (
                <div
                  key={d}
                  className="flex items-end justify-center pb-1 text-[11px] font-medium uppercase tracking-wider text-muted-foreground"
                >
                  {d}
                </div>
              ))}
              {/* Leading blanks */}
              {Array.from({ length: leadingBlanks }).map((_, i) => (
                <div key={`blank-${i}`} />
              ))}
              {/* Day cells */}
              {Array.from({ length: daysInMonth }).map((_, i) => {
                const dayNum = i + 1;
                const dateStr = `${selectedMonth}-${String(dayNum).padStart(2, "0")}`;
                const dayData = dayDataMap.get(dateStr);
                const payments = dayData?.recurring_payments ?? [];
                const totalSpending = dayData?.total_spending ?? 0;
                const isToday = dateStr === todayStr;
                const isPast =
                  dateStr < todayStr &&
                  selectedMonth === now.toFormat("yyyy-MM");
                const hasContent = totalSpending > 0 || payments.length > 0;

                const cellContent = (
                  <div
                    className={`relative flex flex-col items-center justify-center rounded-md ${
                      isToday
                        ? "font-semibold text-foreground ring-1 ring-border"
                        : isPast
                          ? "text-muted-foreground/60"
                          : ""
                    }`}
                    style={getHeatmapStyle(totalSpending, isToday)}
                  >
                    <span className="text-xs leading-none">{dayNum}</span>
                    {payments.length > 0 ? (
                      <div className="mt-1 flex items-center justify-center gap-0.5">
                        {payments.slice(0, 3).map((p, idx) => (
                          <span
                            key={idx}
                            className={`inline-block h-1.5 w-1.5 rounded-full ${
                              p.is_projected
                                ? "border border-primary bg-transparent"
                                : "bg-primary"
                            }`}
                          />
                        ))}
                        {payments.length > 3 && (
                          <span className="inline-block h-1.5 w-1.5 rounded-full bg-primary/50" />
                        )}
                      </div>
                    ) : (
                      <div className="mt-1 h-1.5" />
                    )}
                  </div>
                );

                if (!hasContent) {
                  return (
                    <React.Fragment key={dayNum}>{cellContent}</React.Fragment>
                  );
                }

                return (
                  <Tooltip key={dayNum}>
                    <TooltipTrigger asChild>{cellContent}</TooltipTrigger>
                    <TooltipContent side="top" className="max-w-[240px]">
                      <div className="space-y-1">
                        {totalSpending > 0 && (
                          <>
                            <div className="flex items-center justify-between gap-3 font-medium">
                              <span>Total spending</span>
                              <span className="shrink-0 font-mono tabular-nums">
                                {moneyFormatter(
                                  totalSpending,
                                  locale,
                                  valuationCcy,
                                )}
                              </span>
                            </div>
                            {payments.length > 0 && (
                              <div className="border-t border-border/50 pt-1" />
                            )}
                          </>
                        )}
                        {payments.map((p, idx) => (
                          <div
                            key={idx}
                            className="flex items-center justify-between gap-3"
                          >
                            <span className="flex items-center gap-1.5 truncate">
                              <span
                                className={`inline-block h-1.5 w-1.5 shrink-0 rounded-full ${
                                  p.is_projected
                                    ? "border border-primary-foreground bg-transparent"
                                    : "bg-primary-foreground"
                                }`}
                              />
                              {p.description ?? p.merchant_name}
                            </span>
                            <span className="shrink-0 font-mono tabular-nums">
                              {moneyFormatter(p.avg_amount, locale, p.currency)}
                            </span>
                          </div>
                        ))}
                      </div>
                    </TooltipContent>
                  </Tooltip>
                );
              })}
            </div>
          </TooltipProvider>
        )}
      </CardContent>
    </Card>
  );
};
