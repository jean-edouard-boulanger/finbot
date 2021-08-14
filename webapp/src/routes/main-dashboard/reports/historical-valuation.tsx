import React, { useState, useEffect, useContext } from "react";

import { ServicesContext } from "contexts";

import { Card } from "react-bootstrap";
import Chart from "react-apexcharts";
import { MoneyFormatterType } from "components/money";

import { DateTime } from "luxon";

function maxValue<T>(
  list: Array<T>,
  accessor: (item: T) => number
): number | null {
  accessor = accessor || ((val) => val);
  let currentMax: number | null = null;
  for (let i = 0; i !== list.length; ++i) {
    const val = accessor(list[i]);
    if (currentMax === null || val > currentMax) {
      currentMax = val;
    }
  }
  return currentMax;
}

interface HistoricalValuationEntry {
  timestamp: number;
  value: number;
}

interface HistoricalValuation {
  valuation_ccy: string | null;
  data: Array<HistoricalValuationEntry>;
  high: number | null;
}

export interface HistoricalValuationProps {
  userAccountId: number;
  locale: string;
  moneyFormatter: MoneyFormatterType;
}

export const HistoricalValuationPanel: React.FC<HistoricalValuationProps> = (
  props
) => {
  const { userAccountId, locale, moneyFormatter } = props;
  const { finbotClient } = useContext(ServicesContext);
  const [
    historicalValuation,
    setHistoricalValuation,
  ] = useState<HistoricalValuation>({
    valuation_ccy: null,
    data: [],
    high: null,
  });

  useEffect(() => {
    const fetch = async () => {
      const result = await finbotClient!.getAccountHistoricalValuation({
        account_id: userAccountId,
      });
      setHistoricalValuation({
        valuation_ccy: result.valuation_ccy,
        data: result.entries.map((entry) => {
          return {
            timestamp: DateTime.fromISO(entry.date).toMillis(),
            value: entry.value,
          };
        }),
        high: maxValue(result.entries, (entry) => entry.value),
      });
    };
    fetch();
  }, [finbotClient, userAccountId]);

  return (
    <Card>
      <Card.Header>Historical Valuation</Card.Header>
      <Card.Body>
        <Chart
          options={{
            chart: {
              animations: {
                enabled: false,
              },
              stacked: false,
              zoom: {
                enabled: false,
              },
              toolbar: {
                show: true,
                tools: {
                  download: false,
                },
              },
            },
            grid: {
              show: false,
            },
            theme: {
              palette: "palette8",
            },
            dataLabels: {
              enabled: false,
            },
            xaxis: {
              type: "datetime",
              categories: historicalValuation.data.map(
                (entry) => entry.timestamp
              ),
              tooltip: {
                enabled: false,
              },
            },
            yaxis: {
              show: false,
              min: 0,
              max: historicalValuation.high ?? 0,
            },
            tooltip: {
              x: {
                format: "dd-MMM-yyyy hh:mm",
              },
              y: {
                formatter: (value: number) => {
                  return moneyFormatter(
                    value,
                    locale,
                    historicalValuation.valuation_ccy ?? ""
                  );
                },
              },
            },
            fill: {
              opacity: 0.5,
              type: "solid",
            },
            stroke: {
              width: 1,
            },
          }}
          series={[
            {
              name: "value",
              data: historicalValuation.data.map((entry) => entry.value),
            },
          ]}
          type="area"
          width="100%"
          height="250px"
        />
      </Card.Body>
    </Card>
  );
};
