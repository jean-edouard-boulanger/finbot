import React, { useState, useEffect, useContext } from "react";

import { ServicesContext } from "contexts";

import { Card, Dropdown, DropdownButton } from "react-bootstrap";
import Chart from "react-apexcharts";
import { MoneyFormatterType } from "components/money";

import { capitalize } from "utils/string";

type AggregationMode = "account" | "asset type";

const AGGREGATION_MODES: Array<AggregationMode> = ["account", "asset type"];

const DEFAULT_AGGREGATION_MODE = AGGREGATION_MODES[0];

interface ValuationData {
  valuation_ccy: string;
  labels: Array<string>;
  values: Array<number>;
}

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
  const [aggregationMode, setAggregationMode] = useState<AggregationMode>(
    DEFAULT_AGGREGATION_MODE
  );
  const [valuation, setValuation] = useState<ValuationData | null>(null);

  useEffect(() => {
    const fetch = async () => {
      switch (aggregationMode) {
        case "account": {
          const result = await finbotClient!.getLinkedAccountsValuation({
            account_id: userAccountId,
          });
          setValuation({
            valuation_ccy: result.valuation_ccy,
            labels: result.entries.map(
              (entry) => entry.linked_account.description
            ),
            values: result.entries.map((entry) => entry.valuation.value),
          });
          break;
        }
        case "asset type": {
          const result = await finbotClient!.getUserAccountValuationByAssetType(
            {
              account_id: userAccountId,
            }
          );
          setValuation({
            valuation_ccy: result.valuation_ccy,
            labels: Object.keys(result.by_asset_type).map(capitalize),
            values: Object.values(result.by_asset_type),
          });
          break;
        }
      }
    };
    fetch();
  }, [finbotClient, userAccountId, aggregationMode]);

  return (
    <Card style={{ height: "22rem" }}>
      <Card.Header className={"d-flex justify-content-between"}>
        Wealth Distribution
        <DropdownButton
          variant={""}
          size={"xs" as any}
          title={`By ${aggregationMode}`}
        >
          {AGGREGATION_MODES.map((mode) => {
            return (
              <Dropdown.Item
                active={mode === aggregationMode}
                key={mode}
                onClick={() => {
                  setAggregationMode(mode);
                }}
              >
                BY {mode.toUpperCase()}
              </Dropdown.Item>
            );
          })}
        </DropdownButton>
      </Card.Header>
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
                      valuation?.valuation_ccy
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
              labels: valuation.labels,
            }}
            type="donut"
            series={valuation.values}
            width="100%"
            height="255px"
          />
        )}
      </Card.Body>
    </Card>
  );
};
