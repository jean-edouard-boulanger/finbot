import React, { useEffect, useState } from "react";

import { useApi, UserAccountsReportsApi, EarningsReport } from "clients";

import {
  StackedBarLoader,
  Money,
  ValuationChange,
  RelativeValuationChange,
} from "components";
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
      <StackedBarLoader
        count={4}
        color={"#FBFBFB"}
        spacing={"0.8em"}
        height={"1em"}
        width={"100%"}
      />
    );
  }

  const currency = report.currency;

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Period</TableHead>
          <TableHead>Open</TableHead>
          <TableHead>Close</TableHead>
          <TableHead>Minimum</TableHead>
          <TableHead>Maximum</TableHead>
          <TableHead>Change</TableHead>
          <TableHead>Change (%)</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {report.entries.map((entry, index) => {
          return (
            <TableRow key={`entry-${index}`}>
              <TableCell>
                <strong>{entry.aggregation.asStr}</strong>
              </TableCell>
              <TableCell>
                <Money
                  amount={entry.metrics.firstValue}
                  locale={locale}
                  ccy={currency}
                  moneyFormatter={moneyFormatter}
                />
              </TableCell>
              <TableCell>
                <Money
                  amount={entry.metrics.lastValue}
                  locale={locale}
                  ccy={currency}
                  moneyFormatter={moneyFormatter}
                />
              </TableCell>
              <TableCell>
                <Money
                  amount={entry.metrics.minValue}
                  locale={locale}
                  ccy={currency}
                  moneyFormatter={moneyFormatter}
                />
              </TableCell>
              <TableCell>
                <Money
                  amount={entry.metrics.maxValue}
                  locale={locale}
                  ccy={currency}
                  moneyFormatter={moneyFormatter}
                />
              </TableCell>
              <TableCell>
                <strong>
                  <ValuationChange amount={entry.metrics.absChange} />
                </strong>
              </TableCell>
              <TableCell>
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
              ? "bg-green-50 font-bold"
              : "bg-red-50 font-bold"
          }
        >
          <TableCell>
            <strong>Summary</strong>
          </TableCell>
          <TableCell>
            <strong>
              <Money
                amount={report!.rollup.firstValue}
                locale={locale}
                ccy={currency}
                moneyFormatter={moneyFormatter}
              />
            </strong>
          </TableCell>
          <TableCell>
            <strong>
              <Money
                amount={report!.rollup.lastValue}
                locale={locale}
                ccy={currency}
                moneyFormatter={moneyFormatter}
              />
            </strong>
          </TableCell>
          <TableCell>
            <Money
              amount={report!.rollup.minValue}
              locale={locale}
              ccy={currency}
              moneyFormatter={moneyFormatter}
            />
          </TableCell>
          <TableCell>
            <Money
              amount={report!.rollup.maxValue}
              locale={locale}
              ccy={currency}
              moneyFormatter={moneyFormatter}
            />
          </TableCell>
          <TableCell>
            <strong>
              <ValuationChange amount={report!.rollup.absChange} />
            </strong>
          </TableCell>
          <TableCell>
            <strong>
              <RelativeValuationChange amount={report!.rollup.relChange} />
            </strong>
          </TableCell>
        </TableRow>
      </TableFooter>
    </Table>
  );
};
