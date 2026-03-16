import React, { useEffect, useState, useContext } from "react";
import { AuthContext } from "contexts";
import { APP_SERVICE_ENDPOINT } from "utils/env-config";

import { Card, CardContent, CardHeader, CardTitle } from "components/ui/card";
import { Alert, AlertTitle, AlertDescription } from "components/ui/alert";
import { MoneyFormatterType } from "components/money";
import { Repeat } from "lucide-react";

interface SubscriptionEntry {
  id: number;
  merchant_name: string;
  description: string | null;
  currency: string;
  avg_amount: number;
  avg_interval_days: number;
  yearly_cost: number;
  total_spent_this_year: number;
  last_seen: string;
  first_seen: string;
  transaction_count: number;
}

interface SubscriptionsReport {
  valuation_ccy: string;
  estimated_yearly_total: number;
  total_spent_this_year: number;
  subscriptions: SubscriptionEntry[];
}

function formatFrequency(days: number): string {
  if (days <= 8) return "Weekly";
  if (days <= 16) return "Biweekly";
  if (days <= 45) return "Monthly";
  if (days <= 100) return "Quarterly";
  if (days <= 200) return "Semi-annual";
  return "Yearly";
}

export interface SubscriptionsPanelProps {
  userAccountId: number;
  locale: string;
  moneyFormatter: MoneyFormatterType;
}

export const SubscriptionsPanel: React.FC<SubscriptionsPanelProps> = (
  props,
) => {
  const { userAccountId, locale, moneyFormatter } = props;
  const { accessToken } = useContext(AuthContext);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<SubscriptionsReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        const url = `${APP_SERVICE_ENDPOINT}/reports/subscriptions/`;
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
  }, [accessToken, userAccountId]);

  if (error) {
    return (
      <Card className="border-border/50">
        <CardContent className="pt-6">
          <Alert variant="destructive">
            <AlertTitle>Failed to load subscriptions</AlertTitle>
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
          <Repeat className="h-4 w-4" />
          <CardTitle className="text-sm font-medium uppercase tracking-wide">
            Subscriptions
          </CardTitle>
        </div>
        {data && (
          <span className="text-xs text-muted-foreground">
            {data.subscriptions.length} active
          </span>
        )}
      </CardHeader>
      <CardContent className="flex min-h-0 flex-1 flex-col">
        {loading || !data ? (
          <div className="skeleton-shimmer h-[300px] flex-1 rounded" />
        ) : data.subscriptions.length === 0 ? (
          <div className="flex flex-1 items-center justify-center text-sm text-muted-foreground">
            No active subscriptions detected
          </div>
        ) : (
          <div className="flex min-h-0 flex-1 flex-col gap-4">
            {/* Totals at top — fixed */}
            <div className="flex gap-6 rounded-lg border border-border/50 bg-muted/30 p-3">
              <div className="flex-1">
                <div className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Est. yearly cost
                </div>
                <div className="mt-1 font-mono text-lg font-semibold tabular-nums">
                  {moneyFormatter(
                    data.estimated_yearly_total,
                    locale,
                    data.valuation_ccy,
                  )}
                </div>
              </div>
              <div className="w-px bg-border/50" />
              <div className="flex-1">
                <div className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Spent this year
                </div>
                <div className="mt-1 font-mono text-lg font-semibold tabular-nums">
                  {moneyFormatter(
                    data.total_spent_this_year,
                    locale,
                    data.valuation_ccy,
                  )}
                </div>
              </div>
            </div>

            {/* Subscription list — scrollable */}
            <div className="min-h-0 flex-1 overflow-y-auto">
              <div className="flex flex-col divide-y divide-border/50">
                {data.subscriptions.map((sub) => (
                  <div key={sub.id} className="flex items-center gap-3 py-2.5">
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-sm font-medium">
                        {sub.description ?? sub.merchant_name}
                      </div>
                      <div className="mt-0.5 flex items-center gap-2 text-xs text-muted-foreground">
                        <span>{formatFrequency(sub.avg_interval_days)}</span>
                        <span>-</span>
                        <span>
                          {moneyFormatter(sub.avg_amount, locale, sub.currency)}
                          /ea
                        </span>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-mono text-sm font-medium tabular-nums">
                        {moneyFormatter(sub.yearly_cost, locale, sub.currency)}
                        <span className="text-xs text-muted-foreground">
                          /yr
                        </span>
                      </div>
                      <div className="mt-0.5 font-mono text-xs tabular-nums text-muted-foreground">
                        {moneyFormatter(
                          sub.total_spent_this_year,
                          locale,
                          sub.currency,
                        )}{" "}
                        YTD
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
