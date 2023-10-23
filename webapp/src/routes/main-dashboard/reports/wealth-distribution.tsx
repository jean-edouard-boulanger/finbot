import React, { useState, useEffect } from "react";

import {
  useApi,
  UserAccountsValuationApi,
  LinkedAccountsValuationApi,
} from "clients";
import { Card, Dropdown, DropdownButton } from "react-bootstrap";
import Chart from "react-apexcharts";
import { MoneyFormatterType } from "components/money";

type AggregationMode = "account" | "asset type" | "asset class";

const AGGREGATION_MODES: Array<AggregationMode> = [
  "account",
  "asset type",
  "asset class",
];

const DEFAULT_AGGREGATION_MODE = AGGREGATION_MODES[0];

interface ValuationData {
  valuation_ccy: string;
  labels: Array<string>;
  values: Array<number>;
  colours?: Array<string>;
}

export interface WealthDistributionProps {
  userAccountId: number;
  locale: string;
  moneyFormatter: MoneyFormatterType;
}

export const WealthDistributionPanel: React.FC<WealthDistributionProps> = (
  props,
) => {
  const { userAccountId, locale, moneyFormatter } = props;
  const [aggregationMode, setAggregationMode] = useState<AggregationMode>(
    DEFAULT_AGGREGATION_MODE,
  );
  const [valuation, setValuation] = useState<ValuationData | null>(null);
  const userAccountsValuationApi = useApi(UserAccountsValuationApi);
  const linkedAccountsValuationApi = useApi(LinkedAccountsValuationApi);

  useEffect(() => {
    const fetch = async () => {
      switch (aggregationMode) {
        case "account": {
          const result = (
            await linkedAccountsValuationApi.getLinkedAccountsValuation({
              userAccountId,
            })
          ).valuation;
          setValuation({
            valuation_ccy: result.valuationCcy,
            labels: result.entries.map(
              (entry) => entry.linkedAccount.description,
            ),
            values: result.entries.map((entry) => entry.valuation.value),
            colours: result.entries.map(
              (entry) => entry.linkedAccount.accountColour,
            ),
          });
          break;
        }
        case "asset type": {
          const result = (
            await userAccountsValuationApi.getUserAccountValuationByAssetType({
              userAccountId,
            })
          ).valuation;
          setValuation({
            valuation_ccy: result.valuationCcy,
            labels: result.byAssetType.map((entry) => entry.name),
            values: result.byAssetType.map((entry) => entry.value),
            colours: result.byAssetType.map((entry) => entry.colour),
          });
          break;
        }
        case "asset class": {
          const result = (
            await userAccountsValuationApi!.getUserAccountValuationByAssetClass(
              { userAccountId },
            )
          ).valuation;
          setValuation({
            valuation_ccy: result.valuationCcy,
            labels: result.byAssetClass.map((entry) => entry.name),
            values: result.byAssetClass.map((entry) => entry.value),
            colours: result.byAssetClass.map((entry) => entry.colour),
          });
          break;
        }
      }
    };
    fetch();
  }, [userAccountsValuationApi, userAccountId, aggregationMode]);

  return (
    <Card style={{ height: "22rem" }}>
      <Card.Header className={"d-flex justify-content-between"}>
        Asset diversification
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
                      valuation?.valuation_ccy,
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
              colors: valuation.colours,
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
