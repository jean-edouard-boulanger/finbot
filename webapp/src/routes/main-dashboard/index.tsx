import React, { useState, useEffect, useContext } from "react";
import { Navigate } from "react-router-dom";
import { TrendingUp, TrendingDown, Minus, Clock, Wallet, CreditCard } from "lucide-react";

import { AuthContext } from "contexts";
import {
  useApi,
  UserAccountsValuationApi,
  UserAccountValuation,
  UserAccountsApi,
} from "clients";

import { Money, RelativeValuationChange, BarLoader } from "components";
import { defaultMoneyFormatter } from "components/money";
import {
  EarningsReportPanel,
  HoldingsReportPanel,
  HistoricalValuationPanel,
  WealthDistributionPanel,
} from "./reports";

import { Card, CardContent, CardHeader, CardTitle } from "components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "components/ui/tabs";

import { DateTime } from "luxon";

const getRelativeChange = (startVal: number, finalVal: number) => {
  return (finalVal - startVal) / startVal;
};

const REPORTS = {
  HOLDINGS: "holdings",
  EARNINGS: "earnings",
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

  useEffect(() => {
    const fetch = async () => {
      const result = await userAccountsApi.isUserAccountConfigured({
        userAccountId: userAccountId!,
      });
      setConfigured(result.configured);
    };
    fetch();
  }, [userAccountsApi]);

  useEffect(() => {
    if (!configured) {
      return;
    }
    const fetch = async () => {
      {
        const result = await userAccountValuationApi.getUserAccountValuation({
          userAccountId: userAccountId!,
        });
        setValuation(result.valuation);
      }
    };
    fetch();
  }, [userAccountValuationApi, configured, userAccountId]);

  if (configured === false) {
    return <Navigate to={"/welcome"} />;
  }

  const change1d = valuation?.change?.change1day;
  const relativeChange =
    change1d !== undefined && change1d !== null
      ? getRelativeChange(valuation!.value - change1d, valuation!.value)
      : null;
  const changeDirection =
    relativeChange === null
      ? "neutral"
      : relativeChange > 0
        ? "up"
        : relativeChange < 0
          ? "down"
          : "neutral";

  return (
    <div className="bg-dot-grid min-h-[calc(100vh-3.5rem)]">
      <div className="container mx-auto px-6 pb-48 pt-8">
        {/* Hero: Net Worth */}
        <div className="animate-fade-up stagger-1">
          <Card className="hero-glow relative overflow-hidden border-border/50">
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
                    <div className="flex gap-6">
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
                      {relativeChange !== null && (
                        <div>
                          <div className="mb-1 flex items-center gap-1.5 text-xs font-medium uppercase tracking-wider text-muted-foreground">
                            {changeDirection === "up" && (
                              <TrendingUp className="h-3 w-3 text-gain" />
                            )}
                            {changeDirection === "down" && (
                              <TrendingDown className="h-3 w-3 text-loss" />
                            )}
                            {changeDirection === "neutral" && (
                              <Minus className="h-3 w-3" />
                            )}
                            24h Change
                          </div>
                          <div className="font-mono text-lg font-medium tabular-nums">
                            <RelativeValuationChange amount={relativeChange} />
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="flex items-end justify-between">
                    <MetricSkeleton />
                    <div className="flex gap-6">
                      <MetricSkeleton />
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
              </CardContent>
            </Card>
          </Tabs>
        </div>
      </div>
    </div>
  );
};

export default MainDashboard;
