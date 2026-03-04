import React, { useEffect, useState, useContext } from "react";
import { AuthContext } from "contexts";
import { APP_SERVICE_ENDPOINT } from "utils/env-config";

import { Money } from "components";
import { MoneyFormatterType } from "components/money";
import { Alert, AlertTitle, AlertDescription } from "components/ui/alert";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "components/ui/table";
import { Button } from "components/ui/button";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuCheckboxItem,
} from "components/ui/dropdown-menu";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "components/ui/tooltip";
import { Filter } from "lucide-react";
import { DateTime } from "luxon";

interface TransactionEntry {
  id: number;
  linked_account_id: number;
  linked_account_name: string;
  sub_account_id: string;
  sub_account_name: string;
  transaction_date: string;
  transaction_type: string;
  transaction_category: string;
  amount: number;
  amount_snapshot_ccy: number | null;
  currency: string;
  description: string;
  symbol: string | null;
  units: number | null;
  unit_price: number | null;
  fee: number | null;
  counterparty: string | null;
  spending_category_primary: string | null;
  spending_category_detailed: string | null;
}

interface TransactionsReport {
  valuation_ccy: string;
  transactions: TransactionEntry[];
  total_count: number;
}

const CATEGORIES = [
  { label: "Income", value: "income" },
  { label: "Expense", value: "expense" },
  { label: "Trade", value: "trade" },
  { label: "Transfer", value: "transfer" },
  { label: "Other", value: "other" },
];

export interface TransactionsReportPanelProps {
  userAccountId: number;
  locale: string;
  moneyFormatter: MoneyFormatterType;
}

export const TransactionsReportPanel: React.FC<TransactionsReportPanelProps> = (
  props,
) => {
  const { userAccountId, locale, moneyFormatter } = props;
  const { accessToken } = useContext(AuthContext);
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<TransactionsReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedCategories, setSelectedCategories] = useState<Set<string>>(
    new Set(),
  );
  const [offset, setOffset] = useState(0);
  const limit = 50;

  const toggleCategory = (value: string) => {
    setSelectedCategories((prev) => {
      const next = new Set(prev);
      if (next.has(value)) {
        next.delete(value);
      } else {
        next.add(value);
      }
      return next;
    });
    setOffset(0);
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const params = new URLSearchParams();
        params.set("limit", String(limit));
        params.set("offset", String(offset));
        for (const cat of selectedCategories) {
          params.append("transaction_category", cat);
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
        const data = await resp.json();
        setReport(data.report);
      } catch (e) {
        setError(`${e}`);
      }
      setLoading(false);
    };
    fetchData();
  }, [accessToken, userAccountId, selectedCategories, offset]);

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Failed to load transactions</AlertTitle>
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  const filterLabel =
    selectedCategories.size === 0
      ? "All categories"
      : [...selectedCategories]
          .map((v) => CATEGORIES.find((c) => c.value === v)?.label ?? v)
          .join(", ");

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm" className="gap-1.5 text-xs">
              <Filter className="h-3.5 w-3.5" />
              {filterLabel}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start">
            {CATEGORIES.map(({ label, value }) => (
              <DropdownMenuCheckboxItem
                key={value}
                checked={selectedCategories.has(value)}
                onCheckedChange={() => toggleCategory(value)}
                onSelect={(e) => e.preventDefault()}
              >
                {label}
              </DropdownMenuCheckboxItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {loading || !report ? (
        <div className="space-y-3 py-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="skeleton-shimmer h-10 rounded" />
          ))}
        </div>
      ) : report.transactions.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
          <p className="text-sm">No transactions available yet.</p>
        </div>
      ) : (
        <>
          <Table>
            <TableHeader>
              <TableRow className="border-border/50 hover:bg-transparent">
                <TableHead className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Date
                </TableHead>
                <TableHead className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Account
                </TableHead>
                <TableHead className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Sub-account
                </TableHead>
                <TableHead className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Description
                </TableHead>
                <TableHead className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Category
                </TableHead>
                <TableHead className="text-right text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Amount
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {report.transactions.map((txn) => (
                <TableRow key={txn.id} className="border-border/30">
                  <TableCell className="text-sm tabular-nums">
                    {DateTime.fromISO(txn.transaction_date).toLocaleString(
                      DateTime.DATE_MED,
                    )}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {txn.linked_account_name}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {txn.sub_account_name}
                  </TableCell>
                  <TableCell className="max-w-[200px] truncate text-sm">
                    <TooltipProvider delayDuration={200}>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <span className="cursor-default truncate block">
                            {txn.description}
                          </span>
                        </TooltipTrigger>
                        <TooltipContent>
                          {txn.description}
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {txn.spending_category_primary
                      ? txn.spending_category_primary
                          .replace(/_/g, " ")
                          .toLowerCase()
                          .replace(/\b\w/g, (c) => c.toUpperCase())
                      : "—"}
                  </TableCell>
                  <TableCell className="text-right">
                    <span
                      className={`font-mono text-sm tabular-nums ${
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
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          {/* Pagination */}
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>
              Showing {offset + 1}-{Math.min(offset + limit, report.total_count)}{" "}
              of {report.total_count}
            </span>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={offset === 0}
                onClick={() => setOffset(Math.max(0, offset - limit))}
              >
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={offset + limit >= report.total_count}
                onClick={() => setOffset(offset + limit)}
              >
                Next
              </Button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
