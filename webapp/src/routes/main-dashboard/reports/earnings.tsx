import React, { useEffect, useState } from "react";

import { useApi, UserAccountsReportsApi, EarningsReport } from "clients";

import {
  StackedBarLoader,
  Money,
  ValuationChange,
  RelativeValuationChange,
} from "components";
import { MoneyFormatterType } from "components/money";

import { Alert, Table } from "react-bootstrap";

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
      <Alert variant={"danger"}>
        <Alert.Heading>
          Snap! An error occurred while generating your report
        </Alert.Heading>
        <p>{error}</p>
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
    <Table hover size="sm">
      <thead>
        <tr>
          <th>Period</th>
          <th>Open</th>
          <th>Close</th>
          <th>Minimum</th>
          <th>Maximum</th>
          <th>Change</th>
          <th>Change (%)</th>
        </tr>
      </thead>
      <tbody>
        {report.entries.map((entry, index) => {
          return (
            <tr key={`entry-${index}`}>
              <td>
                <strong>{entry.aggregation.asStr}</strong>
              </td>
              <td>
                <Money
                  amount={entry.metrics.firstValue}
                  locale={locale}
                  ccy={currency}
                  moneyFormatter={moneyFormatter}
                />
              </td>
              <td>
                <Money
                  amount={entry.metrics.lastValue}
                  locale={locale}
                  ccy={currency}
                  moneyFormatter={moneyFormatter}
                />
              </td>
              <td>
                <Money
                  amount={entry.metrics.minValue}
                  locale={locale}
                  ccy={currency}
                  moneyFormatter={moneyFormatter}
                />
              </td>
              <td>
                <Money
                  amount={entry.metrics.maxValue}
                  locale={locale}
                  ccy={currency}
                  moneyFormatter={moneyFormatter}
                />
              </td>
              <td>
                <strong>
                  <ValuationChange amount={entry.metrics.absChange} />
                </strong>
              </td>
              <td>
                <strong>
                  <RelativeValuationChange amount={entry.metrics.relChange} />
                </strong>
              </td>
            </tr>
          );
        })}
      </tbody>
      <tfoot>
        <tr
          style={{ fontWeight: "bold" }}
          className={
            report!.rollup.absChange >= 0 ? "table-success" : "table-danger"
          }
        >
          <td>
            <strong>Summary</strong>
          </td>
          <td>
            <strong>
              <Money
                amount={report!.rollup.firstValue}
                locale={locale}
                ccy={currency}
                moneyFormatter={moneyFormatter}
              />
            </strong>
          </td>
          <td>
            <strong>
              <Money
                amount={report!.rollup.lastValue}
                locale={locale}
                ccy={currency}
                moneyFormatter={moneyFormatter}
              />
            </strong>
          </td>
          <td>
            <Money
              amount={report!.rollup.minValue}
              locale={locale}
              ccy={currency}
              moneyFormatter={moneyFormatter}
            />
          </td>
          <td>
            <Money
              amount={report!.rollup.maxValue}
              locale={locale}
              ccy={currency}
              moneyFormatter={moneyFormatter}
            />
          </td>
          <td>
            <strong>
              <ValuationChange amount={report!.rollup.absChange} />
            </strong>
          </td>
          <td>
            <strong>
              <RelativeValuationChange amount={report!.rollup.relChange} />
            </strong>
          </td>
        </tr>
      </tfoot>
    </Table>
  );
};
