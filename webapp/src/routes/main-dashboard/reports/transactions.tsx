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
import { Filter, ArrowRightLeft } from "lucide-react";
import { DateTime } from "luxon";

interface TransactionEntry {
  id: number;
  linked_account_id: number;
  linked_account_name: string;
  sub_account_id: string;
  sub_account_name: string;
  transaction_date: string;
  transaction_type: string;
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
  matched_transaction_id: number | null;
}

interface TransactionsReport {
  valuation_ccy: string;
  transactions: TransactionEntry[];
  total_count: number;
}

const TRANSACTION_TYPES = [
  { label: "Adjustment", value: "adjustment" },
  { label: "Buy", value: "buy" },
  { label: "Commission", value: "commission" },
  { label: "Contribution", value: "contribution" },
  { label: "Corporate Action", value: "corporate_action" },
  { label: "Deposit", value: "deposit" },
  { label: "Dividend", value: "dividend" },
  { label: "Fee", value: "fee" },
  { label: "Interest Charged", value: "interest_charged" },
  { label: "Interest Earned", value: "interest_earned" },
  { label: "Other", value: "other" },
  { label: "Payment", value: "payment" },
  { label: "Purchase", value: "purchase" },
  { label: "Sell", value: "sell" },
  { label: "Staking Reward", value: "staking_reward" },
  { label: "Tax", value: "tax" },
  { label: "Transfer In", value: "transfer_in" },
  { label: "Transfer Out", value: "transfer_out" },
  { label: "Withdrawal", value: "withdrawal" },
];

const SPENDING_CATEGORIES = [
  { label: "Bank Fees", value: "BANK_FEES" },
  { label: "Entertainment", value: "ENTERTAINMENT" },
  { label: "Food & Drink", value: "FOOD_AND_DRINK" },
  { label: "General Merchandise", value: "GENERAL_MERCHANDISE" },
  { label: "General Services", value: "GENERAL_SERVICES" },
  { label: "Government & Non-Profit", value: "GOVERNMENT_AND_NON_PROFIT" },
  { label: "Home Improvement", value: "HOME_IMPROVEMENT" },
  { label: "Income", value: "INCOME" },
  { label: "Loan Payments", value: "LOAN_PAYMENTS" },
  { label: "Medical", value: "MEDICAL" },
  { label: "Personal Care", value: "PERSONAL_CARE" },
  { label: "Rent & Utilities", value: "RENT_AND_UTILITIES" },
  { label: "Transfer In", value: "TRANSFER_IN" },
  { label: "Transfer Out", value: "TRANSFER_OUT" },
  { label: "Transportation", value: "TRANSPORTATION" },
  { label: "Travel", value: "TRAVEL" },
];

interface LinkedAccountEntry {
  id: number;
  account_name: string;
}

export interface TransactionsReportPanelProps {
  userAccountId: number;
  locale: string;
  moneyFormatter: MoneyFormatterType;
  linkedAccountId?: number;
  pageSize?: number;
}

export const TransactionsReportPanel: React.FC<TransactionsReportPanelProps> = (
  props,
) => {
  const { userAccountId, locale, moneyFormatter, linkedAccountId, pageSize } =
    props;
  const { accessToken } = useContext(AuthContext);
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<TransactionsReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedTypes, setSelectedTypes] = useState<Set<string>>(new Set());
  const [selectedCategories, setSelectedCategories] = useState<Set<string>>(
    new Set(),
  );
  const [selectedAccounts, setSelectedAccounts] = useState<Set<number>>(
    new Set(),
  );
  const [accounts, setAccounts] = useState<LinkedAccountEntry[]>([]);
  const [offset, setOffset] = useState(0);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [counterpartCache, setCounterpartCache] = useState<
    Record<number, TransactionEntry>
  >({});
  const limit = pageSize ?? 50;

  const handleExpand = (txn: TransactionEntry) => {
    if (expandedId === txn.id) {
      setExpandedId(null);
      return;
    }
    setExpandedId(txn.id);
    const matchedId = txn.matched_transaction_id;
    if (
      matchedId == null ||
      counterpartCache[matchedId] ||
      report?.transactions.find((t) => t.id === matchedId)
    ) {
      return;
    }
    fetch(`${APP_SERVICE_ENDPOINT}/reports/transactions/${matchedId}/`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data?.transaction) {
          setCounterpartCache((prev) => ({
            ...prev,
            [matchedId]: data.transaction,
          }));
        }
      })
      .catch(() => {});
  };

  useEffect(() => {
    if (linkedAccountId !== undefined) return;
    const fetchAccounts = async () => {
      try {
        const resp = await fetch(
          `${APP_SERVICE_ENDPOINT}/accounts/${userAccountId}/linked_accounts/`,
          { headers: { Authorization: `Bearer ${accessToken}` } },
        );
        if (!resp.ok) return;
        const data = await resp.json();
        setAccounts(
          data.linked_accounts
            .filter((a: any) => !a.deleted)
            .map((a: any) => ({ id: a.id, account_name: a.account_name }))
            .sort((a: LinkedAccountEntry, b: LinkedAccountEntry) =>
              a.account_name.localeCompare(b.account_name),
            ),
        );
      } catch {
        // non-critical
      }
    };
    fetchAccounts();
  }, [accessToken, userAccountId, linkedAccountId]);

  const toggleType = (value: string) => {
    setSelectedTypes((prev) => {
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

  const toggleAccount = (id: number) => {
    setSelectedAccounts((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
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
        if (linkedAccountId !== undefined) {
          params.append("linked_account_id", String(linkedAccountId));
        }
        for (const id of selectedAccounts) {
          params.append("linked_account_id", String(id));
        }
        for (const t of selectedTypes) {
          params.append("transaction_type", t);
        }
        for (const c of selectedCategories) {
          params.append("spending_category", c);
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
  }, [
    accessToken,
    userAccountId,
    linkedAccountId,
    selectedTypes,
    selectedCategories,
    selectedAccounts,
    offset,
  ]);

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Failed to load transactions</AlertTitle>
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  const typeFilterLabel =
    selectedTypes.size === 0
      ? "All types"
      : [...selectedTypes]
          .map((v) => TRANSACTION_TYPES.find((t) => t.value === v)?.label ?? v)
          .join(", ");

  const categoryFilterLabel =
    selectedCategories.size === 0
      ? "All categories"
      : [...selectedCategories]
          .map(
            (v) => SPENDING_CATEGORIES.find((c) => c.value === v)?.label ?? v,
          )
          .join(", ");

  const accountFilterLabel =
    selectedAccounts.size === 0
      ? "All accounts"
      : [...selectedAccounts]
          .map(
            (id) =>
              accounts.find((a) => a.id === id)?.account_name ?? String(id),
          )
          .join(", ");

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        {linkedAccountId === undefined && accounts.length > 0 && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm" className="gap-1.5 text-xs">
                <Filter className="h-3.5 w-3.5" />
                {accountFilterLabel}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start">
              {accounts.map((account) => (
                <DropdownMenuCheckboxItem
                  key={account.id}
                  checked={selectedAccounts.has(account.id)}
                  onCheckedChange={() => toggleAccount(account.id)}
                  onSelect={(e) => e.preventDefault()}
                >
                  {account.account_name}
                </DropdownMenuCheckboxItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        )}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm" className="gap-1.5 text-xs">
              <Filter className="h-3.5 w-3.5" />
              {typeFilterLabel}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start">
            {TRANSACTION_TYPES.map(({ label, value }) => (
              <DropdownMenuCheckboxItem
                key={value}
                checked={selectedTypes.has(value)}
                onCheckedChange={() => toggleType(value)}
                onSelect={(e) => e.preventDefault()}
              >
                {label}
              </DropdownMenuCheckboxItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm" className="gap-1.5 text-xs">
              <Filter className="h-3.5 w-3.5" />
              {categoryFilterLabel}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start">
            {SPENDING_CATEGORIES.map(({ label, value }) => (
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
              {report.transactions.map((txn) => {
                const isExpanded = expandedId === txn.id;
                const hasMatch = txn.matched_transaction_id != null;
                const counterpart =
                  hasMatch && isExpanded
                    ? (report.transactions.find(
                        (t) => t.id === txn.matched_transaction_id,
                      ) ?? counterpartCache[txn.matched_transaction_id!])
                    : undefined;
                const colCount = 5;

                return (
                  <React.Fragment key={txn.id}>
                    <TableRow
                      className={`border-border/30 ${hasMatch ? "cursor-pointer" : ""}`}
                      onClick={hasMatch ? () => handleExpand(txn) : undefined}
                    >
                      <TableCell className="text-sm tabular-nums">
                        {DateTime.fromISO(txn.transaction_date).toLocaleString(
                          DateTime.DATE_MED,
                        )}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {txn.linked_account_name} ({txn.sub_account_name})
                      </TableCell>
                      <TableCell className="max-w-[200px] truncate text-sm">
                        <div className="flex items-center gap-1.5">
                          <TooltipProvider delayDuration={200}>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <span className="cursor-default truncate block">
                                  {txn.description}
                                </span>
                              </TooltipTrigger>
                              <TooltipContent>{txn.description}</TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                          {hasMatch && (
                            <ArrowRightLeft className="h-3.5 w-3.5 flex-shrink-0 text-muted-foreground" />
                          )}
                        </div>
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
                    {isExpanded && (
                      <TableRow className="border-border/30 bg-muted/30 hover:bg-muted/30">
                        <TableCell colSpan={colCount} className="py-3 pl-10">
                          {counterpart ? (
                            <div className="flex items-center gap-6 text-sm">
                              <div className="flex items-center gap-1.5 text-muted-foreground">
                                <ArrowRightLeft className="h-3.5 w-3.5" />
                                <span>Matched transfer</span>
                              </div>
                              <div>
                                <span className="text-muted-foreground">
                                  {counterpart.linked_account_name}
                                </span>
                                {" · "}
                                <span className="text-muted-foreground">
                                  {counterpart.sub_account_name}
                                </span>
                              </div>
                              <div className="text-muted-foreground">
                                {counterpart.transaction_type
                                  .replace(/_/g, " ")
                                  .toLowerCase()
                                  .replace(/\b\w/g, (c) => c.toUpperCase())}
                              </div>
                              <div className="text-muted-foreground">
                                {counterpart.description}
                              </div>
                              <div className="ml-auto">
                                <span
                                  className={`font-mono tabular-nums ${
                                    counterpart.amount > 0
                                      ? "text-gain"
                                      : counterpart.amount < 0
                                        ? "text-loss"
                                        : ""
                                  }`}
                                >
                                  <Money
                                    amount={counterpart.amount}
                                    locale={locale}
                                    ccy={counterpart.currency}
                                    moneyFormatter={moneyFormatter}
                                  />
                                </span>
                              </div>
                            </div>
                          ) : (
                            <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                              <ArrowRightLeft className="h-3.5 w-3.5" />
                              <span>Loading matched transfer...</span>
                            </div>
                          )}
                        </TableCell>
                      </TableRow>
                    )}
                  </React.Fragment>
                );
              })}
            </TableBody>
          </Table>

          {/* Pagination */}
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>
              Showing {offset + 1}-
              {Math.min(offset + limit, report.total_count)} of{" "}
              {report.total_count}
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
