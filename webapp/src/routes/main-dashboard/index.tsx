import React, { useState, useEffect, useContext, useMemo } from "react";
import { Navigate } from "react-router-dom";
import { Clock, Wallet, CreditCard } from "lucide-react";
import { AreaChart, Area, ResponsiveContainer } from "recharts";

import { AuthContext } from "contexts";
import {
  useApi,
  UserAccountsValuationApi,
  UserAccountValuation,
  UserAccountsApi,
  ValuationChange,
} from "clients";

import { Money } from "components";
import { defaultMoneyFormatter } from "components/money";
import {
  EarningsReportPanel,
  HoldingsReportPanel,
  HistoricalValuationPanel,
  WealthDistributionPanel,
  TransactionsReportPanel,
  CashFlowPanel,
  SpendingBreakdownPanel,
} from "./reports";

import { Alert, AlertTitle, AlertDescription } from "components/ui/alert";
import { Card, CardContent, CardHeader, CardTitle } from "components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "components/ui/tabs";

import { DateTime } from "luxon";

const getRelativeChange = (startVal: number, finalVal: number) => {
  return (finalVal - startVal) / startVal;
};

const CHANGE_PERIODS: { key: keyof ValuationChange; label: string }[] = [
  { key: "change1day", label: "1D" },
  { key: "change1week", label: "1W" },
  { key: "change1month", label: "1M" },
  { key: "change6months", label: "6M" },
  { key: "change1year", label: "1Y" },
  { key: "change2years", label: "2Y" },
];

const REPORTS = {
  HOLDINGS: "holdings",
  EARNINGS: "earnings",
  TRANSACTIONS: "transactions",
};

const DEFAULT_REPORT = REPORTS.HOLDINGS;

function MetricSkeleton() {
  return (
    <div className="space-y-3">
      <div className="skeleton-shimmer h-3 w-24 rounded" />
      <div className="skeleton-shimmer h-7 w-36 rounded" />
    </div>
  );
}

export const MainDashboard: React.FC<Record<string, never>> = () => {
  const { userAccountId } = useContext(AuthContext);
  const locale = "en-GB";
  const userAccountValuationApi = useApi(UserAccountsValuationApi);
  const userAccountsApi = useApi(UserAccountsApi);
  const [configured, setConfigured] = useState<boolean | null>(null);
  const [valuation, setValuation] = useState<UserAccountValuation | null>(null);
  const [selectedReport, setSelectedReport] = useState<string>(DEFAULT_REPORT);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetch = async () => {
      try {
        const result = await userAccountsApi.isUserAccountConfigured({
          userAccountId: userAccountId!,
        });
        setConfigured(result.configured);
      } catch (e) {
        setError(`${e}`);
      }
    };
    fetch();
  }, [userAccountsApi]);

  useEffect(() => {
    if (!configured) {
      return;
    }
    const fetch = async () => {
      try {
        const result = await userAccountValuationApi.getUserAccountValuation({
          userAccountId: userAccountId!,
        });
        setValuation(result.valuation);
      } catch (e) {
        setError(`${e}`);
      }
    };
    fetch();
  }, [userAccountValuationApi, configured, userAccountId]);

  const sparklineData = useMemo(() => {
    if (!valuation?.sparkline) return [];
    return valuation.sparkline
      .filter((entry) => entry.value !== null)
      .map((entry, i) => ({ x: i, value: entry.value as number }));
  }, [valuation?.sparkline]);

  if (error !== null) {
    return (
      <div className="bg-dot-grid min-h-screen">
        <div className="container mx-auto px-6 pb-48 pt-8">
          <Alert variant="destructive">
            <AlertTitle>Failed to load dashboard</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        </div>
      </div>
    );
  }

  if (configured === false) {
    return <Navigate to={"/welcome"} />;
  }

  return (
    <div className="bg-dot-grid min-h-screen">
      <div className="container mx-auto px-6 pb-48 pt-8">
        {/* Hero: Net Worth */}
        <div className="animate-fade-up stagger-1">
          <Card className="hero-glow relative overflow-hidden border-border/50">
            {/* Sparkline background */}
            {sparklineData.length > 1 && (
              <div className="absolute inset-0 opacity-[0.12]">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart
                    data={sparklineData}
                    margin={{ top: 0, right: 0, bottom: 0, left: 0 }}
                  >
                    <defs>
                      <linearGradient
                        id="heroSparkFill"
                        x1="0"
                        y1="0"
                        x2="0"
                        y2="1"
                      >
                        <stop
                          offset="0%"
                          stopColor="hsl(var(--primary))"
                          stopOpacity={1}
                        />
                        <stop
                          offset="100%"
                          stopColor="hsl(var(--primary))"
                          stopOpacity={0}
                        />
                      </linearGradient>
                    </defs>
                    <Area
                      type="monotone"
                      dataKey="value"
                      stroke="hsl(var(--primary))"
                      strokeWidth={1.5}
                      fill="url(#heroSparkFill)"
                      isAnimationActive={false}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            )}
            <div className="relative z-10">
              <CardHeader className="pb-2">
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Wallet className="h-4 w-4" />
                  <CardTitle className="text-sm font-medium tracking-wide uppercase">
                    Net Worth
                  </CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                {valuation !== null ? (
                  <div className="space-y-4">
                    <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
                      <div>
                        <div className="font-serif text-4xl font-semibold tracking-tight sm:text-5xl">
                          <Money
                            amount={valuation.value}
                            locale={locale}
                            ccy={valuation.currency}
                            moneyFormatter={defaultMoneyFormatter}
                          />
                        </div>
                        <div className="mt-2 flex items-center gap-2 text-sm text-muted-foreground">
                          <Clock className="h-3.5 w-3.5" />
                          {DateTime.fromJSDate(valuation.date).toLocaleString(
                            DateTime.DATETIME_FULL,
                          )}
                        </div>
                      </div>
                      <div>
                        <div className="mb-1 flex items-center gap-1.5 text-xs font-medium uppercase tracking-wider text-muted-foreground">
                          <CreditCard className="h-3 w-3" />
                          Liabilities
                        </div>
                        <div className="font-mono text-lg font-medium tabular-nums">
                          <Money
                            amount={valuation.totalLiabilities}
                            locale={locale}
                            ccy={valuation.currency}
                            moneyFormatter={defaultMoneyFormatter}
                          />
                        </div>
                      </div>
                    </div>
                    {/* Change pills */}
                    <div className="flex flex-wrap gap-2">
                      {CHANGE_PERIODS.map(({ key, label }) => {
                        const absChange = valuation.change[key];
                        if (absChange === null || absChange === undefined) {
                          return (
                            <span
                              key={key}
                              className="inline-flex items-center gap-1 rounded-full border border-border/50 bg-muted/50 px-2.5 py-0.5 font-mono text-xs tabular-nums text-muted-foreground"
                            >
                              {label} –
                            </span>
                          );
                        }
                        const rel = getRelativeChange(
                          valuation.value - absChange,
                          valuation.value,
                        );
                        const pct = (rel * 100).toFixed(1);
                        const isPositive = rel > 0;
                        const isNegative = rel < 0;
                        return (
                          <span
                            key={key}
                            className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 font-mono text-xs tabular-nums ${
                              isPositive
                                ? "border-gain/30 bg-gain/10 text-gain"
                                : isNegative
                                  ? "border-loss/30 bg-loss/10 text-loss"
                                  : "border-border/50 bg-muted/50 text-muted-foreground"
                            }`}
                          >
                            {label} {isPositive ? "+" : ""}
                            {pct}%
                          </span>
                        );
                      })}
                    </div>
                  </div>
                ) : (
                  <div className="flex items-end justify-between">
                    <MetricSkeleton />
                    <div className="flex gap-6">
                      <MetricSkeleton />
                    </div>
                  </div>
                )}
              </CardContent>
            </div>
          </Card>
        </div>

        {/* Charts */}
        <div className="mt-6 grid gap-6 lg:grid-cols-2">
          <div className="animate-fade-up stagger-2">
            <HistoricalValuationPanel
              userAccountId={userAccountId!}
              locale={locale}
              moneyFormatter={defaultMoneyFormatter}
            />
          </div>
          <div className="animate-fade-up stagger-3">
            <WealthDistributionPanel
              userAccountId={userAccountId!}
              locale={locale}
              moneyFormatter={defaultMoneyFormatter}
            />
          </div>
          <div className="animate-fade-up stagger-4">
            <CashFlowPanel
              userAccountId={userAccountId!}
              locale={locale}
              moneyFormatter={defaultMoneyFormatter}
            />
          </div>
          <div className="animate-fade-up stagger-4">
            <SpendingBreakdownPanel
              userAccountId={userAccountId!}
              locale={locale}
              moneyFormatter={defaultMoneyFormatter}
            />
          </div>
        </div>

        {/* Reports */}
        <div className="mt-6 animate-fade-up stagger-4">
          <Tabs
            defaultValue={DEFAULT_REPORT}
            value={selectedReport}
            onValueChange={(value) => setSelectedReport(value)}
          >
            <Card className="border-border/50">
              <CardHeader className="pb-0">
                <TabsList className="self-start">
                  <TabsTrigger value={REPORTS.HOLDINGS}>Holdings</TabsTrigger>
                  <TabsTrigger value={REPORTS.EARNINGS}>Earnings</TabsTrigger>
                  <TabsTrigger value={REPORTS.TRANSACTIONS}>
                    Transactions
                  </TabsTrigger>
                </TabsList>
              </CardHeader>
              <CardContent className="pt-4">
                <TabsContent value={REPORTS.HOLDINGS} className="mt-0">
                  <HoldingsReportPanel
                    userAccountId={userAccountId!}
                    locale={locale}
                    moneyFormatter={defaultMoneyFormatter}
                  />
                </TabsContent>
                <TabsContent value={REPORTS.EARNINGS} className="mt-0">
                  <EarningsReportPanel
                    userAccountId={userAccountId!}
                    locale={locale}
                    moneyFormatter={defaultMoneyFormatter}
                  />
                </TabsContent>
                <TabsContent value={REPORTS.TRANSACTIONS} className="mt-0">
                  <TransactionsReportPanel
                    userAccountId={userAccountId!}
                    locale={locale}
                    moneyFormatter={defaultMoneyFormatter}
                  />
                </TabsContent>
              </CardContent>
            </Card>
          </Tabs>
        </div>
      </div>
    </div>
  );
};

export default MainDashboard;
