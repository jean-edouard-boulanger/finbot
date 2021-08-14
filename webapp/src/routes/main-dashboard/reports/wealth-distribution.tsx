import React, { useState, useEffect, useContext } from "react";

import { ServicesContext } from "contexts";

import { Card } from "react-bootstrap";
import Chart from "react-apexcharts";
import { MoneyFormatterType } from "components/money";

import { LinkedAccountsValuationEntry } from "clients/finbot-client/types";

export interface WealthDistributionProps {
  userAccountId: number;
  locale: string;
  moneyFormatter: MoneyFormatterType;
}

export const WealthDistributionPanel: React.FC<WealthDistributionProps> = (
  props
) => {
  const { userAccountId, locale, moneyFormatter } = props;
  const { finbotClient } = useContext(ServicesContext);
  const [
    valuation,
    setValuation,
  ] = useState<Array<LinkedAccountsValuationEntry> | null>(null);

  useEffect(() => {
    const fetch = async () => {
      const result = await finbotClient!.getLinkedAccountsValuation({
        account_id: userAccountId,
      });
      setValuation(result);
    };
    fetch();
  }, [finbotClient, userAccountId]);

  return (
    <Card>
      <Card.Header>Wealth Distribution</Card.Header>
      <Card.Body>
        {valuation !== null && (
          <Chart
            options={{
              chart: {
                animations: {
                  enabled: false,
                },
              },
              legend: {
                show: true,
              },
              theme: {
                palette: "palette8",
              },
              plotOptions: {
                pie: {
                  customScale: 1,
                },
              },
              tooltip: {
                y: {
                  formatter: (value: number) => {
                    const amount_str = moneyFormatter(
                      value,
                      locale,
                      "EUR" // FIXME
                    );
                    return `<span class="text-white">${amount_str}</span>`;
                  },
                  title: {
                    formatter: (seriesName: string) => {
                      return `<strong><span class="text-white">${seriesName}</span></strong>`;
                    },
                  },
                },
              },
              stroke: {
                width: 0,
              },
              responsive: [
                {
                  breakpoint: 765,
                  options: {
                    legend: {
                      show: false,
                    },
                  },
                },
              ],
              labels: valuation
                .filter((entry) => entry.valuation.value >= 0.0)
                .map((entry) => entry.linked_account.description),
            }}
            type="donut"
            series={valuation
              .filter((entry) => entry.valuation.value >= 0.0)
              .map((entry) => entry.valuation.value)}
            width="100%"
            height="255px"
          />
        )}
      </Card.Body>
    </Card>
  );
};
