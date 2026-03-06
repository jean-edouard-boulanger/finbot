import React, { useEffect, useState } from "react";

import { useApi, UserAccountsReportsApi, EarningsReport } from "clients";

import { Money, ValuationChange, RelativeValuationChange } from "components";
import { MoneyFormatterType } from "components/money";

import { Alert, AlertTitle, AlertDescription } from "components/ui/alert";
import {
  Table,
  TableBody,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from "components/ui/table";

export interface EarningsReportPanelProps {
  userAccountId: number;
  locale: string;
  moneyFormatter: MoneyFormatterType;
}

export const EarningsReportPanel: React.FC<EarningsReportPanelProps> = (
  props,
) => {
  const { userAccountId, locale, moneyFormatter } = props;
  const userAccountsReportsApi = useApi(UserAccountsReportsApi);
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<EarningsReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetch = async () => {
      try {
        setLoading(true);
        const report = (
          await userAccountsReportsApi.getUserAccountEarningsReport()
        ).report;
        setReport(report);
      } catch (e) {
        setError(`${e}`);
      }
      setLoading(false);
    };
    fetch();
  }, [userAccountsReportsApi, userAccountId]);

  if (error !== null) {
    return (
      <Alert variant="destructive">
        <AlertTitle>
          Snap! An error occurred while generating your report
        </AlertTitle>
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  if (loading || !report) {
    return (
      <div className="space-y-3 py-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="skeleton-shimmer h-10 rounded" />
        ))}
      </div>
    );
  }

  const currency = report.currency;

  return (
    <Table>
      <TableHeader>
        <TableRow className="border-border/50 hover:bg-transparent">
          <TableHead className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
            Period
          </TableHead>
          <TableHead className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
            Open
          </TableHead>
          <TableHead className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
            Close
          </TableHead>
          <TableHead className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
            Minimum
          </TableHead>
          <TableHead className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
            Maximum
          </TableHead>
          <TableHead className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
            Change
          </TableHead>
          <TableHead className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
            Change (%)
          </TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {report.entries.map((entry, index) => {
          return (
            <TableRow
              key={`entry-${index}`}
              className="border-border/30 transition-colors hover:bg-secondary/30"
            >
              <TableCell>
                <strong>{entry.aggregation.asStr}</strong>
              </TableCell>
              <TableCell className="font-mono tabular-nums">
                <Money
                  amount={entry.metrics.firstValue}
                  locale={locale}
                  ccy={currency}
                  moneyFormatter={moneyFormatter}
                />
              </TableCell>
              <TableCell className="font-mono tabular-nums">
                <Money
                  amount={entry.metrics.lastValue}
                  locale={locale}
                  ccy={currency}
                  moneyFormatter={moneyFormatter}
                />
              </TableCell>
              <TableCell className="font-mono tabular-nums">
                <Money
                  amount={entry.metrics.minValue}
                  locale={locale}
                  ccy={currency}
                  moneyFormatter={moneyFormatter}
                />
              </TableCell>
              <TableCell className="font-mono tabular-nums">
                <Money
                  amount={entry.metrics.maxValue}
                  locale={locale}
                  ccy={currency}
                  moneyFormatter={moneyFormatter}
                />
              </TableCell>
              <TableCell className="font-mono tabular-nums">
                <strong>
                  <ValuationChange amount={entry.metrics.absChange} />
                </strong>
              </TableCell>
              <TableCell className="font-mono tabular-nums">
                <strong>
                  <RelativeValuationChange amount={entry.metrics.relChange} />
                </strong>
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
      <TableFooter>
        <TableRow
          className={
            report!.rollup.absChange >= 0
              ? "border-border/50 bg-gain/5 font-bold"
              : "border-border/50 bg-loss/5 font-bold"
          }
        >
          <TableCell>
            <strong>Summary</strong>
          </TableCell>
          <TableCell className="font-mono tabular-nums">
            <strong>
              <Money
                amount={report!.rollup.firstValue}
                locale={locale}
                ccy={currency}
                moneyFormatter={moneyFormatter}
              />
            </strong>
          </TableCell>
          <TableCell className="font-mono tabular-nums">
            <strong>
              <Money
                amount={report!.rollup.lastValue}
                locale={locale}
                ccy={currency}
                moneyFormatter={moneyFormatter}
              />
            </strong>
          </TableCell>
          <TableCell className="font-mono tabular-nums">
            <Money
              amount={report!.rollup.minValue}
              locale={locale}
              ccy={currency}
              moneyFormatter={moneyFormatter}
            />
          </TableCell>
          <TableCell className="font-mono tabular-nums">
            <Money
              amount={report!.rollup.maxValue}
              locale={locale}
              ccy={currency}
              moneyFormatter={moneyFormatter}
            />
          </TableCell>
          <TableCell className="font-mono tabular-nums">
            <strong>
              <ValuationChange amount={report!.rollup.absChange} />
            </strong>
          </TableCell>
          <TableCell className="font-mono tabular-nums">
            <strong>
              <RelativeValuationChange amount={report!.rollup.relChange} />
            </strong>
          </TableCell>
        </TableRow>
      </TableFooter>
    </Table>
  );
};
