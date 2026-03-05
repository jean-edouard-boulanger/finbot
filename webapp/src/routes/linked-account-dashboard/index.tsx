import React, { useContext, useEffect, useMemo, useState } from "react";
import { useParams, Navigate } from "react-router-dom";
import { Clock } from "lucide-react";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";

import { AuthContext } from "contexts";
import {
  useApi,
  LinkedAccountsValuationApi,
  LinkedAccountValuationEntry,
  LinkedAccountsApi,
  LinkedAccount,
  UserAccountsReportsApi,
  ValuationTree,
  LinkedAccountNode,
  ValuationChange,
} from "clients";

import { Money, TreeGrid } from "components";
import { defaultMoneyFormatter } from "components/money";
import { ChartTooltipContent } from "components/ui/chart";
import { Alert, AlertTitle, AlertDescription } from "components/ui/alert";
import { Card, CardContent, CardHeader, CardTitle } from "components/ui/card";
import { Badge } from "components/ui/badge";
import {
  GridRow,
  Header,
  HoldingsReportNode,
} from "../main-dashboard/reports/holdings";
import { HistoricalValuationPanel } from "../main-dashboard/reports/historical-valuation";

import { DateTime } from "luxon";
import { CheckCircle, AlertCircle, Ghost, HelpCircle } from "lucide-react";

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

function AccountStatusBadge({
  linkedAccount,
}: {
  linkedAccount: LinkedAccount;
}) {
  const status = linkedAccount.frozen
    ? "frozen"
    : (linkedAccount.status ?? { status: "unknown" }).status;

  if (status === "stable") {
    return (
      <Badge variant="success">
        <CheckCircle className="mr-1 h-3 w-3" />
        Stable
      </Badge>
    );
  }
  if (status === "frozen") {
    return (
      <Badge variant="secondary">
        <Ghost className="mr-1 h-3 w-3" />
        Frozen
      </Badge>
    );
  }
  if (status === "unstable") {
    return (
      <Badge variant="destructive">
        <AlertCircle className="mr-1 h-3 w-3" />
        Error
      </Badge>
    );
  }
  return (
    <Badge variant="outline">
      <HelpCircle className="mr-1 h-3 w-3" />
      Pending
    </Badge>
  );
}

function getNodeValuation(node: HoldingsReportNode) {
  if ("valuation" in node) {
    return node.valuation;
  }
}

function MetricSkeleton() {
  return (
    <div className="space-y-3">
      <div className="skeleton-shimmer h-3 w-24 rounded" />
      <div className="skeleton-shimmer h-7 w-36 rounded" />
    </div>
  );
}

export const LinkedAccountDashboard: React.FC = () => {
  const { linkedAccountId: rawId } = useParams<{ linkedAccountId: string }>();
  const linkedAccountId = Number(rawId);
  const { userAccountId } = useContext(AuthContext);
  const locale = "en-GB";

  const linkedAccountsApi = useApi(LinkedAccountsApi);
  const linkedAccountsValuationApi = useApi(LinkedAccountsValuationApi);
  const userAccountsReportsApi = useApi(UserAccountsReportsApi);

  const [linkedAccount, setLinkedAccount] = useState<LinkedAccount | null>(
    null,
  );
  const [valuationEntry, setValuationEntry] =
    useState<LinkedAccountValuationEntry | null>(null);
  const [holdingsTree, setHoldingsTree] = useState<ValuationTree | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    setLinkedAccount(null);
    setValuationEntry(null);
    setHoldingsTree(null);

    const fetchAll = async () => {
      try {
        const [accountResult, valuationResult, holdingsResult] =
          await Promise.all([
            linkedAccountsApi.getLinkedAccount({
              userAccountId: userAccountId!,
              linkedAccountId,
            }),
            linkedAccountsValuationApi.getLinkedAccountsValuation({
              userAccountId: userAccountId!,
            }),
            userAccountsReportsApi.getUserAccountHoldingsReport(),
          ]);

        setLinkedAccount(accountResult.linkedAccount);

        const entry = valuationResult.valuation.entries.find(
          (e) => e.linkedAccount.id === linkedAccountId,
        );
        setValuationEntry(entry ?? null);

        setHoldingsTree(holdingsResult.report);
      } catch (e) {
        setError(`${e}`);
      }
      setLoading(false);
    };
    fetchAll();
  }, [
    linkedAccountsApi,
    linkedAccountsValuationApi,
    userAccountsReportsApi,
    userAccountId,
    linkedAccountId,
  ]);

  const accountNode = useMemo(() => {
    if (!holdingsTree) return null;
    const root = holdingsTree.valuationTree;
    if (!root || !("children" in root)) return null;
    return (
      (root.children as LinkedAccountNode[]).find(
        (c) => c.linkedAccount.id === linkedAccountId,
      ) ?? null
    );
  }, [holdingsTree, linkedAccountId]);

  const subAccountPieData = useMemo(() => {
    if (!accountNode) return [];
    return accountNode.children.map((sub) => ({
      name: sub.subAccount.description,
      value: sub.valuation.value,
    }));
  }, [accountNode]);

  const pieTotal = useMemo(
    () => subAccountPieData.reduce((s, d) => s + d.value, 0),
    [subAccountPieData],
  );

  const PIE_COLORS = [
    "hsl(var(--chart-1))",
    "hsl(var(--chart-2))",
    "hsl(var(--chart-3))",
    "hsl(var(--chart-4))",
    "hsl(var(--chart-5))",
    "hsl(var(--primary))",
    "hsl(var(--gain))",
    "hsl(var(--destructive))",
  ];

  if (isNaN(linkedAccountId)) {
    return <Navigate to="/dashboard" replace />;
  }

  if (loading) {
    return (
      <div className="bg-dot-grid min-h-screen">
        <div className="container mx-auto px-6 pb-48 pt-8">
          <div className="space-y-6">
            <div className="skeleton-shimmer h-32 rounded-lg" />
            <div className="grid gap-6 lg:grid-cols-2">
              <div className="skeleton-shimmer h-[22rem] rounded-lg" />
              <div className="skeleton-shimmer h-[22rem] rounded-lg" />
            </div>
            <div className="skeleton-shimmer h-64 rounded-lg" />
          </div>
        </div>
      </div>
    );
  }

  if (!linkedAccount) {
    if (error !== null) {
      return (
        <div className="bg-dot-grid min-h-screen">
          <div className="container mx-auto px-6 pb-48 pt-8">
            <Alert variant="destructive">
              <AlertTitle>Failed to load account</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          </div>
        </div>
      );
    }
    return <Navigate to="/dashboard" replace />;
  }

  const valuation = valuationEntry?.valuation;
  const lastSnapshotTime = linkedAccount.status?.lastSnapshotTime
    ? DateTime.fromJSDate(
        new Date(linkedAccount.status.lastSnapshotTime as unknown as string),
      )
    : null;

  return (
    <div className="bg-dot-grid min-h-screen">
      <div className="container mx-auto px-6 pb-48 pt-8">
        {/* Account Header */}
        <div className="animate-fade-up stagger-1">
          <div className="mb-6 flex flex-wrap items-center gap-3">
            <span
              className="h-3 w-3 shrink-0 rounded-sm"
              style={{ backgroundColor: linkedAccount.accountColour }}
            />
            <h1 className="text-2xl font-semibold tracking-tight">
              {linkedAccount.accountName}
            </h1>
            <span className="text-sm text-muted-foreground">
              {linkedAccount.provider.description}
            </span>
            <AccountStatusBadge linkedAccount={linkedAccount} />
            {lastSnapshotTime && (
              <span className="text-xs text-muted-foreground">
                Synced {lastSnapshotTime.toRelative()}
              </span>
            )}
          </div>
        </div>

        {/* Valuation Hero */}
        <div className="animate-fade-up stagger-1">
          <Card className="border-border/50">
            <CardHeader className="pb-2">
              <div className="flex items-center gap-2 text-muted-foreground">
                <CardTitle className="text-sm font-medium tracking-wide uppercase">
                  Account Value
                </CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              {valuation ? (
                <div className="space-y-4">
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
                            {label} &ndash;
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
                <MetricSkeleton />
              )}
            </CardContent>
          </Card>
        </div>

        {/* Charts: Historical + Sub-account distribution */}
        <div className="mt-6 grid gap-6 lg:grid-cols-2">
          <div className="animate-fade-up stagger-2">
            <HistoricalValuationPanel
              userAccountId={userAccountId!}
              locale={locale}
              moneyFormatter={defaultMoneyFormatter}
              linkedAccountId={linkedAccountId}
              linkedAccountName={valuationEntry?.linkedAccount.description}
            />
          </div>
          <div className="animate-fade-up stagger-3">
            <Card className="h-[22rem] border-border/50">
              <CardHeader className="pb-2">
                <span className="text-sm font-medium tracking-wide uppercase text-muted-foreground">
                  Sub-Account Distribution
                </span>
              </CardHeader>
              <CardContent>
                {subAccountPieData.length > 0 ? (
                  <div className="flex items-center gap-4">
                    <div
                      className="shrink-0"
                      style={{ width: "55%", height: 240 }}
                    >
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={subAccountPieData}
                            dataKey="value"
                            nameKey="name"
                            innerRadius="50%"
                            outerRadius="85%"
                            stroke="hsl(var(--card))"
                            strokeWidth={2}
                            isAnimationActive={false}
                          >
                            {subAccountPieData.map((_, i) => (
                              <Cell
                                key={i}
                                fill={PIE_COLORS[i % PIE_COLORS.length]}
                              />
                            ))}
                          </Pie>
                          <Tooltip
                            content={
                              <ChartTooltipContent
                                formatter={(value: number) =>
                                  defaultMoneyFormatter(
                                    value,
                                    locale,
                                    valuation?.currency ?? "",
                                  )
                                }
                              />
                            }
                          />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                    <div
                      className="flex min-w-0 flex-1 flex-col gap-2 overflow-y-auto"
                      style={{ maxHeight: 240 }}
                    >
                      {subAccountPieData.map((entry, i) => {
                        const pct =
                          pieTotal > 0
                            ? ((entry.value / pieTotal) * 100).toFixed(1)
                            : "0.0";
                        return (
                          <div
                            key={i}
                            className="flex items-center gap-2.5 text-xs"
                          >
                            <span
                              className="h-2.5 w-2.5 shrink-0 rounded-sm"
                              style={{
                                backgroundColor:
                                  PIE_COLORS[i % PIE_COLORS.length],
                              }}
                            />
                            <span className="min-w-0 flex-1 truncate text-muted-foreground">
                              {entry.name}
                            </span>
                            <span className="shrink-0 font-mono tabular-nums font-medium">
                              {pct}%
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ) : (
                  <div
                    className="flex items-center justify-center text-sm text-muted-foreground"
                    style={{ height: 240 }}
                  >
                    No sub-account data available
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Holdings Table */}
        {accountNode && (
          <div className="mt-6 animate-fade-up stagger-4">
            <Card className="border-border/50">
              <CardHeader className="pb-0">
                <CardTitle className="text-sm font-medium tracking-wide uppercase text-muted-foreground">
                  Holdings
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4">
                <TreeGrid
                  rowAs={GridRow(locale, defaultMoneyFormatter)}
                  headerAs={Header}
                  tree={accountNode as HoldingsReportNode}
                  sortBy={(node) =>
                    getNodeValuation(node)?.value ?? Number.MIN_VALUE
                  }
                />
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
};

export default LinkedAccountDashboard;
