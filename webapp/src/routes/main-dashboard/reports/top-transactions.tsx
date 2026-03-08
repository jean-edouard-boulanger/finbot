import React, { useEffect, useState, useContext } from "react";
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
import { Money } from "components";
import { MoneyFormatterType } from "components/money";
import { ArrowUpDown, ChevronDown } from "lucide-react";
import { DateTime } from "luxon";

interface TransactionEntry {
  id: number;
  linked_account_id: number;
  linked_account_name: string;
  sub_account_name: string;
  transaction_date: string;
  transaction_type: string;
  amount: number;
  currency: string;
  description: string;
  amount_snapshot_ccy: number | null;
}

interface TransactionsReport {
  valuation_ccy: string;
  transactions: TransactionEntry[];
  total_count: number;
}

interface TimeRange {
  from_time?: DateTime;
  to_time?: DateTime;
}

interface TimeRangeChoice {
  label: string;
  makeRange(now: DateTime): TimeRange;
}

const TIME_RANGES: TimeRangeChoice[] = [
  {
    label: "1W",
    makeRange: (now) => ({ from_time: now.minus({ weeks: 1 }) }),
  },
  {
    label: "2W",
    makeRange: (now) => ({ from_time: now.minus({ weeks: 2 }) }),
  },
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
    label: "THIS YEAR",
    makeRange: (now) => ({
      from_time: DateTime.fromObject({ year: now.year, month: 1, day: 1 }),
    }),
  },
];

const DEFAULT_TIME_RANGE = TIME_RANGES[2]; // 1M

export interface TopTransactionsPanelProps {
  userAccountId: number;
  locale: string;
  moneyFormatter: MoneyFormatterType;
}

export const TopTransactionsPanel: React.FC<TopTransactionsPanelProps> = (
  props,
) => {
  const { userAccountId, locale, moneyFormatter } = props;
  const { accessToken } = useContext(AuthContext);
  const [loading, setLoading] = useState(false);
  const [transactions, setTransactions] = useState<TransactionEntry[]>([]);
  const [, setValuationCcy] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [now] = useState<DateTime>(DateTime.now());
  const [selectedTimeRange, setSelectedTimeRange] =
    useState<TimeRangeChoice>(DEFAULT_TIME_RANGE);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        const range = selectedTimeRange.makeRange(now);
        const params = new URLSearchParams({
          limit: "200",
          offset: "0",
        });
        if (range.from_time) {
          params.set("from_time", range.from_time.toISO()!);
        }
        if (range.to_time) {
          params.set("to_time", range.to_time.toISO()!);
        }
        const resp = await fetch(
          `${APP_SERVICE_ENDPOINT}/reports/transactions/?${params}`,
          {
            headers: {
              Authorization: `Bearer ${accessToken}`,
            },
          },
        );
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const json = await resp.json();
        const report: TransactionsReport = json.report;
        setValuationCcy(report.valuation_ccy);
        const sorted = [...report.transactions].sort(
          (a, b) =>
            Math.abs(b.amount_snapshot_ccy ?? b.amount) -
            Math.abs(a.amount_snapshot_ccy ?? a.amount),
        );
        setTransactions(sorted.slice(0, 8));
      } catch (e) {
        setError(`${e}`);
      }
      setLoading(false);
    };
    fetchData();
  }, [accessToken, userAccountId, now, selectedTimeRange]);

  if (error) {
    return (
      <Card className="border-border/50">
        <CardContent className="pt-6">
          <Alert variant="destructive">
            <AlertTitle>Failed to load transactions</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-border/50">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="flex items-center gap-2 text-muted-foreground">
          <ArrowUpDown className="h-4 w-4" />
          <CardTitle className="text-sm font-medium tracking-wide uppercase">
            Largest Transactions
          </CardTitle>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="outline"
              size="xs"
              className="border-border/50 bg-secondary/50 text-xs font-medium tracking-wide text-muted-foreground hover:text-foreground"
            >
              {selectedTimeRange.label} <ChevronDown className="ml-1 h-3 w-3" />
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
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="skeleton-shimmer h-[300px] rounded" />
        ) : transactions.length === 0 ? (
          <div className="flex h-[300px] items-center justify-center text-sm text-muted-foreground">
            No transactions available yet.
          </div>
        ) : (
          <div className="flex h-[300px] flex-col gap-2 overflow-y-auto">
            {transactions.map((txn) => (
              <div
                key={txn.id}
                className="flex items-center justify-between gap-3 rounded-md border border-border/30 px-3 py-2"
              >
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm font-medium">
                    {txn.description}
                  </div>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <span>
                      {DateTime.fromISO(txn.transaction_date).toLocaleString(
                        DateTime.DATE_MED,
                      )}
                    </span>
                    <span>&middot;</span>
                    <span>{txn.linked_account_name}</span>
                  </div>
                </div>
                <span
                  className={`shrink-0 font-mono text-sm tabular-nums font-medium ${
                    txn.amount > 0
                      ? "text-gain"
                      : txn.amount < 0
                        ? "text-loss"
                        : ""
                  }`}
                >
                  <Money
                    amount={txn.amount}
                    locale={locale}
                    ccy={txn.currency}
                    moneyFormatter={moneyFormatter}
                  />
                </span>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};
