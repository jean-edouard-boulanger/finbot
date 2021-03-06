import React, { useContext, useEffect, useState } from "react";

import { StackedBarLoader, Money, ValuationChange } from "components";
import { Alert, Table } from "react-bootstrap";
import { ServicesContext } from "contexts/services/services-context";


export const EarningsReport = (props) => {
  const {
    accountId,
    locale,
    moneyFormatter
  } = props;

  const {finbotClient} = useContext(ServicesContext);
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetch = async () => {
      try {
        setLoading(true);
        const report = await finbotClient.getEarningsReport();
        setReport(report);
      }
      catch(e) {
        setError(`${e}`);
      }
      setLoading(false);
    }
    fetch();
  }, [finbotClient, accountId])

  if(error !== null) {
    return (
      <Alert variant={"danger"}>
        <Alert.Heading>
          Snap! An error occurred while generating your report
        </Alert.Heading>
        <p>
          {error}
        </p>
      </Alert>
    )
  }

  if(loading || !report) {
    return (
      <StackedBarLoader
        count={4}
        color={"#FBFBFB"}
        spacing={"0.8em"}
        height={"1em"}
        width={"100%"} />
    )
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
      {
        report.entries.map((entry) => {
          return (
            <tr>
              <td><strong>{entry.aggregation.as_str}</strong></td>
              <td>
                <Money
                  amount={entry.metrics.first_value}
                  locale={locale}
                  ccy={currency}
                  moneyFormatter={moneyFormatter} />
              </td>
              <td>
                <Money
                  amount={entry.metrics.last_value}
                  locale={locale}
                  ccy={currency}
                  moneyFormatter={moneyFormatter} />
              </td>
              <td>
                <Money
                  amount={entry.metrics.min_value}
                  locale={locale}
                  ccy={currency}
                  moneyFormatter={moneyFormatter} />
              </td>
              <td>
                <Money
                  amount={entry.metrics.max_value}
                  locale={locale}
                  ccy={currency}
                  moneyFormatter={moneyFormatter} />
              </td>
              <td>
                <strong>
                  <ValuationChange amount={entry.metrics.abs_change} />
                </strong>
              </td>
              <td>
                <strong>
                  <ValuationChange.Relative amount={entry.metrics.rel_change} />
                </strong>
              </td>
            </tr>
          )
        })
      }
      </tbody>
      <tfoot>
        <tr
          style={{fontWeight: "bold"}}
          className={(report.rollup.abs_change >= 0) ? "table-success" : "table-danger"}>
          <td><strong>Summary</strong></td>
          <td>
            <strong>
              <Money
                amount={report.rollup.first_value}
                locale={locale}
                ccy={currency}
                moneyFormatter={moneyFormatter} />
            </strong>
          </td>
          <td>
            <strong>
              <Money
                amount={report.rollup.last_value}
                locale={locale}
                ccy={currency}
                moneyFormatter={moneyFormatter} />
            </strong>
          </td>
          <td>
            <Money
              amount={report.rollup.min_value}
              locale={locale}
              ccy={currency}
              moneyFormatter={moneyFormatter} />
          </td>
          <td>
            <Money
              amount={report.rollup.max_value}
              locale={locale}
              ccy={currency}
              moneyFormatter={moneyFormatter} />
          </td>
          <td>
            <strong>
              <ValuationChange amount={report.rollup.abs_change} />
            </strong>
          </td>
          <td>
            <strong>
              <ValuationChange.Relative amount={report.rollup.rel_change} />
            </strong>
          </td>
        </tr>
      </tfoot>
    </Table>
  )
}
