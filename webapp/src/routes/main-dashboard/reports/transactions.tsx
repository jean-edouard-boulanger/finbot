import React, { useEffect, useState, useContext, useMemo } from "react";
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
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "components/ui/tooltip";
import { ArrowRightLeft, Repeat } from "lucide-react";
import { DateTime } from "luxon";
import { useDebounce } from "../../../hooks/use-debounce";
import {
  DateRangeFilter,
  MultiSelectFilter,
  TextSearchFilter,
  AmountRangeFilter,
  type AmountSign,
} from "./transactions/column-filters";
import { TransactionDetailSheet } from "./transactions/transaction-detail-sheet";

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
  merchant_id: number | null;
  merchant_name: string | null;
  merchant_website_url: string | null;
  recurring_group_id: number | null;
}

interface TransactionsReport {
  valuation_ccy: string;
  transactions: TransactionEntry[];
  total_count: number;
}

interface FilterOptionEntry {
  label: string;
  value: string;
  transaction_count: number;
}

interface FilterOptions {
  accounts: FilterOptionEntry[];
  merchants: FilterOptionEntry[];
  categories: FilterOptionEntry[];
  amount_min: number | null;
  amount_max: number | null;
  credit_count: number;
  debit_count: number;
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

  const [report, setReport] = useState<TransactionsReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedCategories, setSelectedCategories] = useState<Set<string>>(
    new Set(),
  );
  const [selectedAccounts, setSelectedAccounts] = useState<Set<number>>(
    new Set(),
  );
  const [offset, setOffset] = useState(0);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [detailId, setDetailId] = useState<number | null>(null);
  const [counterpartCache, setCounterpartCache] = useState<
    Record<number, TransactionEntry>
  >({});
  const limit = pageSize ?? 50;

  // New filter state
  const [fromDate, setFromDate] = useState(() => {
    const now = new Date();
    return new Date(now.getFullYear(), now.getMonth(), 1)
      .toISOString()
      .slice(0, 10);
  });
  const [toDate, setToDate] = useState(() =>
    new Date().toISOString().slice(0, 10),
  );
  const [descriptionSearch, setDescriptionSearch] = useState("");
  const [selectedMerchants, setSelectedMerchants] = useState<Set<string>>(
    new Set(),
  );
  const [amountMin, setAmountMin] = useState<number | null>(null);
  const [amountMax, setAmountMax] = useState<number | null>(null);
  const [amountSign, setAmountSign] = useState<AmountSign>("all");
  const [filterOptions, setFilterOptions] = useState<FilterOptions | null>(
    null,
  );

  const debouncedDescription = useDebounce(descriptionSearch, 400);
  const debouncedAmountMin = useDebounce(amountMin, 400);
  const debouncedAmountMax = useDebounce(amountMax, 400);

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

  // Fetch filter options (accounts, merchants, categories, amount range)
  useEffect(() => {
    const fetchFilterOptions = async () => {
      try {
        const params = new URLSearchParams();
        if (fromDate) {
          params.set("from_time", new Date(fromDate).toISOString());
        }
        if (toDate) {
          params.set("to_time", new Date(toDate + "T23:59:59").toISOString());
        }
        if (linkedAccountId !== undefined) {
          params.append("linked_account_id", String(linkedAccountId));
        }
        for (const id of selectedAccounts) {
          params.append("linked_account_id", String(id));
        }
        for (const c of selectedCategories) {
          params.append("spending_category", c);
        }
        if (debouncedDescription) {
          params.set("description", debouncedDescription);
        }
        for (const m of selectedMerchants) {
          params.append("merchant_name", m);
        }
        if (debouncedAmountMin !== null) {
          params.set("amount_min", String(debouncedAmountMin));
        }
        if (debouncedAmountMax !== null) {
          params.set("amount_max", String(debouncedAmountMax));
        }
        if (amountSign !== "all") {
          params.set("amount_sign", amountSign);
        }
        const qs = params.toString();
        const resp = await fetch(
          `${APP_SERVICE_ENDPOINT}/reports/transactions/filter-options/${qs ? `?${qs}` : ""}`,
          { headers: { Authorization: `Bearer ${accessToken}` } },
        );
        if (!resp.ok) return;
        const data = await resp.json();
        setFilterOptions(data.filter_options);
      } catch {
        // non-critical
      }
    };
    fetchFilterOptions();
  }, [
    accessToken,
    linkedAccountId,
    fromDate,
    toDate,
    selectedAccounts,
    selectedCategories,
    selectedMerchants,
    debouncedDescription,
    debouncedAmountMin,
    debouncedAmountMax,
    amountSign,
  ]);

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

  const toggleMerchant = (name: string) => {
    setSelectedMerchants((prev) => {
      const next = new Set(prev);
      if (next.has(name)) {
        next.delete(name);
      } else {
        next.add(name);
      }
      return next;
    });
    setOffset(0);
  };

  // Fetch transactions data
  useEffect(() => {
    const fetchData = async () => {
      try {
        const params = new URLSearchParams();
        params.set("limit", String(limit));
        params.set("offset", String(offset));
        if (linkedAccountId !== undefined) {
          params.append("linked_account_id", String(linkedAccountId));
        }
        for (const id of selectedAccounts) {
          params.append("linked_account_id", String(id));
        }
        for (const c of selectedCategories) {
          params.append("spending_category", c);
        }
        if (fromDate) {
          params.set("from_time", new Date(fromDate).toISOString());
        }
        if (toDate) {
          params.set("to_time", new Date(toDate + "T23:59:59").toISOString());
        }
        if (debouncedDescription) {
          params.set("description", debouncedDescription);
        }
        for (const m of selectedMerchants) {
          params.append("merchant_name", m);
        }
        if (debouncedAmountMin !== null) {
          params.set("amount_min", String(debouncedAmountMin));
        }
        if (debouncedAmountMax !== null) {
          params.set("amount_max", String(debouncedAmountMax));
        }
        if (amountSign !== "all") {
          params.set("amount_sign", amountSign);
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
    };
    fetchData();
  }, [
    accessToken,
    userAccountId,
    linkedAccountId,
    selectedCategories,
    selectedAccounts,
    selectedMerchants,
    fromDate,
    toDate,
    debouncedDescription,
    debouncedAmountMin,
    debouncedAmountMax,
    amountSign,
    offset,
  ]);

  const accountOptions = useMemo(
    () =>
      (filterOptions?.accounts ?? []).map((a) => ({
        label: a.label,
        value: a.value,
        count: a.transaction_count,
      })),
    [filterOptions],
  );

  const merchantOptions = useMemo(
    () =>
      (filterOptions?.merchants ?? []).map((m) => ({
        label: m.label,
        value: m.value,
        count: m.transaction_count,
      })),
    [filterOptions],
  );

  const categoryOptions = useMemo(
    () =>
      (filterOptions?.categories ?? []).map((c) => ({
        label: c.label,
        value: c.value,
        count: c.transaction_count,
      })),
    [filterOptions],
  );

  // Convert account selection between number Set and string Set for MultiSelectFilter
  const selectedAccountStrings = useMemo(
    () => new Set([...selectedAccounts].map(String)),
    [selectedAccounts],
  );
  const toggleAccountString = (value: string) => toggleAccount(Number(value));

  const hasActiveFilters =
    fromDate !== "" ||
    toDate !== "" ||
    selectedAccounts.size > 0 ||
    descriptionSearch !== "" ||
    selectedMerchants.size > 0 ||
    selectedCategories.size > 0 ||
    amountMin !== null ||
    amountMax !== null ||
    amountSign !== "all";

  const clearAllFilters = () => {
    setFromDate("");
    setToDate("");
    setSelectedAccounts(new Set());
    setDescriptionSearch("");
    setSelectedMerchants(new Set());
    setSelectedCategories(new Set());
    setAmountMin(null);
    setAmountMax(null);
    setAmountSign("all");
    setOffset(0);
  };

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Failed to load transactions</AlertTitle>
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-4">
      {!report ? (
        <div
          className="space-y-3 py-4"
          style={{ minHeight: `${limit * 3.125 + 9}rem` }}
        >
          {Array.from({ length: limit }).map((_, i) => (
            <div key={i} className="skeleton-shimmer h-10 rounded" />
          ))}
        </div>
      ) : (
        <>
          <div style={{ minHeight: `${limit * 3.125 + 9}rem` }}>
            <Table className="table-fixed">
              <colgroup>
                <col className="w-[12%]" />
                <col className="w-[20%]" />
                <col className="w-[28%]" />
                <col className="w-[14%]" />
                <col className="w-[14%]" />
                <col className="w-[10%]" />
              </colgroup>
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
                    Merchant
                  </TableHead>
                  <TableHead className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    Category
                  </TableHead>
                  <TableHead className="text-right text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    Amount
                  </TableHead>
                </TableRow>
                <TableRow className="border-border/30 hover:bg-transparent">
                  <TableHead className="py-1.5">
                    <DateRangeFilter
                      fromDate={fromDate}
                      toDate={toDate}
                      onFromDateChange={(v) => {
                        setFromDate(v);
                        setOffset(0);
                      }}
                      onToDateChange={(v) => {
                        setToDate(v);
                        setOffset(0);
                      }}
                    />
                  </TableHead>
                  <TableHead className="py-1.5">
                    {linkedAccountId === undefined &&
                      accountOptions.length > 0 && (
                        <MultiSelectFilter
                          options={accountOptions}
                          selected={selectedAccountStrings}
                          onToggle={toggleAccountString}
                          placeholder="Account"
                        />
                      )}
                  </TableHead>
                  <TableHead className="py-1.5">
                    <TextSearchFilter
                      value={descriptionSearch}
                      onChange={(v) => {
                        setDescriptionSearch(v);
                        setOffset(0);
                      }}
                      placeholder="Search..."
                    />
                  </TableHead>
                  <TableHead className="py-1.5">
                    <MultiSelectFilter
                      options={merchantOptions}
                      selected={selectedMerchants}
                      onToggle={toggleMerchant}
                      placeholder="Merchant"
                    />
                  </TableHead>
                  <TableHead className="py-1.5">
                    <MultiSelectFilter
                      options={categoryOptions}
                      selected={selectedCategories}
                      onToggle={toggleCategory}
                      placeholder="Category"
                    />
                  </TableHead>
                  <TableHead className="py-1.5">
                    {filterOptions &&
                      filterOptions.amount_min !== null &&
                      filterOptions.amount_max !== null && (
                        <AmountRangeFilter
                          min={amountMin}
                          max={amountMax}
                          rangeMin={Math.floor(filterOptions.amount_min)}
                          rangeMax={Math.ceil(filterOptions.amount_max)}
                          sign={amountSign}
                          creditCount={filterOptions.credit_count}
                          debitCount={filterOptions.debit_count}
                          onMinChange={(v) => {
                            setAmountMin(v);
                            setOffset(0);
                          }}
                          onMaxChange={(v) => {
                            setAmountMax(v);
                            setOffset(0);
                          }}
                          onSignChange={(v) => {
                            setAmountSign(v);
                            setOffset(0);
                          }}
                        />
                      )}
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {report.transactions.length === 0 ? (
                  <TableRow
                    className="hover:bg-transparent"
                    style={{ height: `${limit * 3.125}rem` }}
                  >
                    <TableCell colSpan={6} className="text-center align-middle">
                      <p className="text-sm text-muted-foreground">
                        {hasActiveFilters
                          ? "No transactions match the current filters."
                          : "No transactions available yet."}
                      </p>
                      {hasActiveFilters && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="mt-2 text-xs"
                          onClick={clearAllFilters}
                        >
                          Clear all filters
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ) : (
                  report.transactions.map((txn) => {
                    const isExpanded = expandedId === txn.id;
                    const hasMatch = txn.matched_transaction_id != null;
                    const counterpart =
                      hasMatch && isExpanded
                        ? (report.transactions.find(
                            (t) => t.id === txn.matched_transaction_id,
                          ) ?? counterpartCache[txn.matched_transaction_id!])
                        : undefined;
                    const colCount = 6;

                    return (
                      <React.Fragment key={txn.id}>
                        <TableRow
                          className="border-border/30 cursor-pointer"
                          onClick={() => setDetailId(txn.id)}
                        >
                          <TableCell className="truncate text-sm tabular-nums">
                            {DateTime.fromISO(
                              txn.transaction_date,
                            ).toLocaleString(DateTime.DATE_MED)}
                          </TableCell>
                          <TableCell className="truncate text-sm text-muted-foreground">
                            {txn.linked_account_name} ({txn.sub_account_name})
                          </TableCell>
                          <TableCell className="overflow-hidden text-sm">
                            <div className="flex items-center gap-1.5 overflow-hidden">
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
                              {txn.recurring_group_id != null && (
                                <TooltipProvider delayDuration={200}>
                                  <Tooltip>
                                    <TooltipTrigger asChild>
                                      <Repeat className="h-3.5 w-3.5 flex-shrink-0 text-blue-400" />
                                    </TooltipTrigger>
                                    <TooltipContent>
                                      Recurring transaction
                                    </TooltipContent>
                                  </Tooltip>
                                </TooltipProvider>
                              )}
                              {hasMatch && (
                                <button
                                  className="flex-shrink-0 rounded p-0.5 hover:bg-muted transition-colors"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleExpand(txn);
                                  }}
                                >
                                  <ArrowRightLeft className="h-3.5 w-3.5 text-muted-foreground" />
                                </button>
                              )}
                            </div>
                          </TableCell>
                          <TableCell className="truncate text-sm text-muted-foreground">
                            {txn.merchant_name ?? "\u2014"}
                          </TableCell>
                          <TableCell className="truncate text-sm text-muted-foreground">
                            {txn.spending_category_primary
                              ? txn.spending_category_primary
                                  .replace(/_/g, " ")
                                  .toLowerCase()
                                  .replace(/\b\w/g, (c) => c.toUpperCase())
                              : "\u2014"}
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
                            <TableCell
                              colSpan={colCount}
                              className="py-3 pl-10"
                            >
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
                                    {" \u00B7 "}
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
                  })
                )}
              </TableBody>
            </Table>
          </div>

          {/* Pagination */}
          {report.transactions.length > 0 && (
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
          )}

          <TransactionDetailSheet
            transactionId={detailId}
            onClose={() => setDetailId(null)}
            locale={locale}
            moneyFormatter={moneyFormatter}
          />
        </>
      )}
    </div>
  );
};
