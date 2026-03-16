import React, { useEffect, useState, useContext } from "react";
import { AuthContext } from "contexts";
import { APP_SERVICE_ENDPOINT } from "utils/env-config";
import { Money } from "components";
import { MoneyFormatterType } from "components/money";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "components/ui/sheet";
import { Badge } from "components/ui/badge";
import { Separator } from "components/ui/separator";
import { Skeleton } from "components/ui/skeleton";
import {
  ArrowRightLeft,
  Building2,
  ExternalLink,
  Repeat,
  ShieldCheck,
  TrendingUp,
} from "lucide-react";
import { DateTime } from "luxon";

interface MerchantDetail {
  id: number;
  name: string;
  description: string | null;
  category: string | null;
  website_url: string | null;
}

interface RecurringGroupDetail {
  id: number;
  currency: string;
  avg_amount: number;
  avg_interval_days: number;
  transaction_count: number;
  total_spent: number;
  total_spent_ccy: number | null;
  yearly_cost: number;
  first_seen: string;
  last_seen: string;
  description: string | null;
}

interface MatchDetail {
  match_confidence: number;
  match_status: string;
  counterpart_transaction_id: number;
  counterpart_account_name: string;
  counterpart_description: string;
  counterpart_amount: number;
  counterpart_currency: string;
}

interface TransactionDetail {
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
  spending_category_source: string | null;
  provider_specific_data: unknown;
  merchant: MerchantDetail | null;
  recurring_group: RecurringGroupDetail | null;
  match: MatchDetail | null;
}

function formatCategory(value: string): string {
  return value
    .replace(/_/g, " ")
    .toLowerCase()
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function MerchantFavicon({
  url,
  className,
}: {
  url: string;
  className?: string;
}) {
  const [errored, setErrored] = useState(false);
  let domain: string;
  try {
    domain = new URL(url).hostname;
  } catch {
    return <Building2 className={className} />;
  }
  if (errored) {
    return <Building2 className={className} />;
  }
  return (
    <img
      src={`https://www.google.com/s2/favicons?domain=${domain}&sz=32`}
      alt=""
      className={className}
      onError={() => setErrored(true)}
    />
  );
}

function Section({
  icon,
  title,
  children,
}: {
  icon: React.ReactNode;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 text-sm font-medium text-foreground">
        {icon}
        {title}
      </div>
      <div className="space-y-2 pl-6">{children}</div>
    </div>
  );
}

function DetailRow({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-baseline justify-between gap-4">
      <span className="text-xs text-muted-foreground shrink-0">{label}</span>
      <span className="text-sm text-right">{children}</span>
    </div>
  );
}

export interface TransactionDetailSheetProps {
  transactionId: number | null;
  onClose: () => void;
  locale: string;
  moneyFormatter: MoneyFormatterType;
}

export const TransactionDetailSheet: React.FC<TransactionDetailSheetProps> = ({
  transactionId,
  onClose,
  locale,
  moneyFormatter,
}) => {
  const { accessToken } = useContext(AuthContext);
  const [detail, setDetail] = useState<TransactionDetail | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (transactionId == null) {
      setDetail(null);
      return;
    }
    setLoading(true);
    fetch(
      `${APP_SERVICE_ENDPOINT}/reports/transactions/${transactionId}/detail/`,
      { headers: { Authorization: `Bearer ${accessToken}` } },
    )
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((data) => setDetail(data.transaction))
      .catch(() => setDetail(null))
      .finally(() => setLoading(false));
  }, [transactionId, accessToken]);

  const txn = detail;
  const hasInvestment =
    txn != null &&
    (txn.symbol != null || txn.units != null || txn.unit_price != null);

  return (
    <Sheet open={transactionId != null} onOpenChange={() => onClose()}>
      <SheetContent className="sm:max-w-lg overflow-y-auto">
        {loading || txn == null ? (
          <div className="space-y-6 pt-2">
            <div className="space-y-2">
              <Skeleton className="h-6 w-3/4" />
              <Skeleton className="h-4 w-1/2" />
            </div>
            <Separator />
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="space-y-2">
                <Skeleton className="h-4 w-1/3" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-2/3" />
              </div>
            ))}
          </div>
        ) : (
          <div className="space-y-6">
            {/* Header */}
            <SheetHeader>
              <SheetTitle className="pr-6 leading-snug">
                {txn.description}
              </SheetTitle>
              <SheetDescription>
                {DateTime.fromISO(txn.transaction_date).toLocaleString(
                  DateTime.DATE_FULL,
                )}{" "}
                &middot; {txn.linked_account_name} ({txn.sub_account_name})
              </SheetDescription>
            </SheetHeader>

            <Separator />

            {/* Transaction */}
            <Section
              icon={<TrendingUp className="h-4 w-4" />}
              title="Transaction"
            >
              <DetailRow label="Type">
                <Badge variant="outline" className="text-xs">
                  {formatCategory(txn.transaction_type)}
                </Badge>
              </DetailRow>
              <DetailRow label="Amount">
                <span
                  className={`font-mono tabular-nums ${
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
              </DetailRow>
              {txn.amount_snapshot_ccy != null &&
                txn.amount_snapshot_ccy !== txn.amount && (
                  <DetailRow label="Converted">
                    <span className="font-mono tabular-nums text-muted-foreground">
                      <Money
                        amount={txn.amount_snapshot_ccy}
                        locale={locale}
                        ccy={txn.currency}
                        moneyFormatter={moneyFormatter}
                      />
                    </span>
                  </DetailRow>
                )}
              {txn.fee != null && txn.fee !== 0 && (
                <DetailRow label="Fee">
                  <span className="font-mono tabular-nums">
                    <Money
                      amount={txn.fee}
                      locale={locale}
                      ccy={txn.currency}
                      moneyFormatter={moneyFormatter}
                    />
                  </span>
                </DetailRow>
              )}
              {txn.counterparty && (
                <DetailRow label="Counterparty">{txn.counterparty}</DetailRow>
              )}
              {txn.spending_category_primary && (
                <DetailRow label="Category">
                  <Badge variant="secondary" className="text-xs">
                    {formatCategory(txn.spending_category_primary)}
                  </Badge>
                </DetailRow>
              )}
              {txn.spending_category_detailed && (
                <DetailRow label="Detailed">
                  {formatCategory(txn.spending_category_detailed)}
                </DetailRow>
              )}
              {txn.spending_category_source && (
                <DetailRow label="Source">
                  <span className="text-xs text-muted-foreground">
                    {txn.spending_category_source}
                  </span>
                </DetailRow>
              )}
            </Section>

            {/* Investment */}
            {hasInvestment && (
              <>
                <Separator />
                <Section
                  icon={<TrendingUp className="h-4 w-4" />}
                  title="Investment"
                >
                  {txn.symbol && (
                    <DetailRow label="Symbol">
                      <Badge variant="outline" className="font-mono text-xs">
                        {txn.symbol}
                      </Badge>
                    </DetailRow>
                  )}
                  {txn.units != null && (
                    <DetailRow label="Units">
                      <span className="font-mono tabular-nums">
                        {txn.units}
                      </span>
                    </DetailRow>
                  )}
                  {txn.unit_price != null && (
                    <DetailRow label="Unit price">
                      <span className="font-mono tabular-nums">
                        <Money
                          amount={txn.unit_price}
                          locale={locale}
                          ccy={txn.currency}
                          moneyFormatter={moneyFormatter}
                        />
                      </span>
                    </DetailRow>
                  )}
                </Section>
              </>
            )}

            {/* Merchant */}
            {txn.merchant != null && (
              <>
                <Separator />
                <Section
                  icon={
                    txn.merchant.website_url ? (
                      <MerchantFavicon
                        url={txn.merchant.website_url}
                        className="h-5 w-5 rounded-sm"
                      />
                    ) : (
                      <Building2 className="h-4 w-4" />
                    )
                  }
                  title="Merchant"
                >
                  <DetailRow label="Name">
                    {txn.merchant.website_url ? (
                      <a
                        href={txn.merchant.website_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1.5 text-primary hover:underline"
                      >
                        <MerchantFavicon
                          url={txn.merchant.website_url}
                          className="h-5 w-5 rounded-sm"
                        />
                        {txn.merchant.name}
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    ) : (
                      txn.merchant.name
                    )}
                  </DetailRow>
                  {txn.merchant.category && (
                    <DetailRow label="Category">
                      <Badge variant="secondary" className="text-xs">
                        {formatCategory(txn.merchant.category)}
                      </Badge>
                    </DetailRow>
                  )}
                  {txn.merchant.description && (
                    <DetailRow label="Description">
                      {txn.merchant.description}
                    </DetailRow>
                  )}
                </Section>
              </>
            )}

            {/* Recurring */}
            {txn.recurring_group != null && (
              <>
                <Separator />
                <Section
                  icon={<Repeat className="h-4 w-4" />}
                  title="Recurring"
                >
                  {txn.recurring_group.description && (
                    <p className="text-sm text-muted-foreground">
                      {txn.recurring_group.description}
                    </p>
                  )}
                  <DetailRow label="Frequency">
                    Every ~{Math.round(txn.recurring_group.avg_interval_days)}{" "}
                    days
                  </DetailRow>
                  <DetailRow label="Avg amount">
                    <span className="font-mono tabular-nums">
                      <Money
                        amount={txn.recurring_group.avg_amount}
                        locale={locale}
                        ccy={txn.recurring_group.currency}
                        moneyFormatter={moneyFormatter}
                      />
                    </span>
                  </DetailRow>
                  <DetailRow label="Estimated yearly cost">
                    <span className="font-mono tabular-nums">
                      <Money
                        amount={txn.recurring_group.yearly_cost}
                        locale={locale}
                        ccy={txn.recurring_group.currency}
                        moneyFormatter={moneyFormatter}
                      />
                    </span>
                  </DetailRow>
                  <DetailRow label="Occurrences">
                    {txn.recurring_group.transaction_count}
                  </DetailRow>
                  <DetailRow label="Total spent">
                    <span className="font-mono tabular-nums">
                      <Money
                        amount={txn.recurring_group.total_spent}
                        locale={locale}
                        ccy={txn.recurring_group.currency}
                        moneyFormatter={moneyFormatter}
                      />
                    </span>
                  </DetailRow>
                  <DetailRow label="Period">
                    {DateTime.fromISO(
                      txn.recurring_group.first_seen,
                    ).toLocaleString(DateTime.DATE_MED)}{" "}
                    &ndash;{" "}
                    {DateTime.fromISO(
                      txn.recurring_group.last_seen,
                    ).toLocaleString(DateTime.DATE_MED)}
                  </DetailRow>
                </Section>
              </>
            )}

            {/* Matched Transfer */}
            {txn.match != null && (
              <>
                <Separator />
                <Section
                  icon={<ArrowRightLeft className="h-4 w-4" />}
                  title="Matched Transfer"
                >
                  <DetailRow label="Confidence">
                    {Math.round(txn.match.match_confidence * 100)}%
                  </DetailRow>
                  <DetailRow label="Status">
                    <Badge variant="outline" className="text-xs">
                      <ShieldCheck className="h-3 w-3 mr-1" />
                      {formatCategory(txn.match.match_status)}
                    </Badge>
                  </DetailRow>
                  <DetailRow label="Account">
                    {txn.match.counterpart_account_name}
                  </DetailRow>
                  <DetailRow label="Description">
                    {txn.match.counterpart_description}
                  </DetailRow>
                  <DetailRow label="Amount">
                    <span
                      className={`font-mono tabular-nums ${
                        txn.match.counterpart_amount > 0
                          ? "text-gain"
                          : txn.match.counterpart_amount < 0
                            ? "text-loss"
                            : ""
                      }`}
                    >
                      <Money
                        amount={txn.match.counterpart_amount}
                        locale={locale}
                        ccy={txn.match.counterpart_currency}
                        moneyFormatter={moneyFormatter}
                      />
                    </span>
                  </DetailRow>
                </Section>
              </>
            )}
          </div>
        )}
      </SheetContent>
    </Sheet>
  );
};
