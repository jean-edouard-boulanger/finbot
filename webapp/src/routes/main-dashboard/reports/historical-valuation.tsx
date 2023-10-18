import React, { useState, useEffect, useContext } from "react";

import { ServicesContext } from "contexts";

import { Card, Dropdown, DropdownButton } from "react-bootstrap";
import Chart from "react-apexcharts";
import { MoneyFormatterType } from "components/money";

import { DateTime } from "luxon";
import { HistoricalValuation, TimeRange } from "clients/finbot-client/types";
import { lastItem } from "utils/array";

interface TimeRangeChoiceType {
  label: string;
  makeRange(now: DateTime): TimeRange;
}

type LevelType = "account" | "linked_account" | "asset_type" | "asset_class";

interface LevelChoiceProp {
  type: LevelType;
  label: string;
}

const LEVELS: Array<LevelChoiceProp> = [
  {
    type: "account",
    label: "OVERALL",
  },
  {
    type: "linked_account",
    label: "BY ACCOUNT",
  },
  {
    type: "asset_type",
    label: "BY ASSET TYPE",
  },
  {
    type: "asset_class",
    label: "BY ASSET CLASS",
  },
];

const DEFAULT_LEVEL = LEVELS[1];

const FREQUENCIES: Array<string> = [
  "Daily",
  "Weekly",
  "Monthly",
  "Quarterly",
  "Yearly",
];

const DEFAULT_FREQUENCY = FREQUENCIES[2];

const TIME_RANGES: Array<TimeRangeChoiceType> = [
  {
    label: "1W",
    makeRange: (now) => {
      return {
        from_time: now.minus({ weeks: 1 }),
      };
    },
  },
  {
    label: "2W",
    makeRange: (now) => {
      return {
        from_time: now.minus({ weeks: 2 }),
      };
    },
  },
  {
    label: "1M",
    makeRange: (now) => {
      return {
        from_time: now.minus({ month: 1 }),
      };
    },
  },
  {
    label: "2M",
    makeRange: (now) => {
      return {
        from_time: now.minus({ months: 2 }),
      };
    },
  },
  {
    label: "6M",
    makeRange: (now) => {
      return {
        from_time: now.minus({ months: 6 }),
      };
    },
  },
  {
    label: "1Y",
    makeRange: (now) => {
      return {
        from_time: now.minus({ year: 1 }),
      };
    },
  },
  {
    label: "2Y",
    makeRange: (now) => {
      return {
        from_time: now.minus({ year: 2 }),
      };
    },
  },
  {
    label: "5Y",
    makeRange: (now) => {
      return {
        from_time: now.minus({ year: 5 }),
      };
    },
  },
  {
    label: "LAST YEAR",
    makeRange: (now) => {
      return {
        from_time: DateTime.fromObject({
          year: now.year - 1,
          month: 1,
          day: 1,
        }),
        to_time: DateTime.fromObject({
          year: now.year - 1,
          month: 12,
          day: 31,
          hour: 23,
          minute: 59,
        }),
      };
    },
  },
  {
    label: "THIS YEAR",
    makeRange: (now) => {
      return {
        from_time: DateTime.fromObject({
          year: now.year,
          month: 1,
          day: 1,
        }),
      };
    },
  },
  {
    label: "ALL DATA",
    makeRange: () => {
      return {};
    },
  },
];

const DEFAULT_RANGE = lastItem(TIME_RANGES)!;

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
  const [now] = useState<DateTime>(DateTime.now());
  const [selectedLevel, setSelectedLevel] = useState(DEFAULT_LEVEL);
  const [selectedFrequency, setSelectedFrequency] = useState(DEFAULT_FREQUENCY);
  const [selectedTimeRange, setSelectedTimeRange] =
    useState<TimeRangeChoiceType>(DEFAULT_RANGE);
  const [historicalValuation, setHistoricalValuation] =
    useState<HistoricalValuation | null>(null);

  useEffect(() => {
    const fetchValuation = async () => {
      const range = selectedTimeRange.makeRange(now);
      const request = {
        account_id: userAccountId,
        ...range,
        frequency: selectedFrequency,
      };
      switch (selectedLevel.type) {
        case "account": {
          const data = await finbotClient!.getAccountHistoricalValuation(
            request
          );
          setHistoricalValuation(data);
          break;
        }
        case "linked_account": {
          const data = await finbotClient!.getLinkedAccountsHistoricalValuation(
            request
          );
          setHistoricalValuation(data);
          break;
        }
        case "asset_type": {
          const data =
            await finbotClient!.getAccountHistoricalValuationByAssetType(
              request
            );
          setHistoricalValuation(data);
          break;
        }
        case "asset_class": {
          const data =
            await finbotClient!.getAccountHistoricalValuationByAssetClass(
              request
            );
          setHistoricalValuation(data);
          break;
        }
      }
    };
    fetchValuation();
  }, [
    finbotClient,
    userAccountId,
    now,
    selectedLevel,
    selectedTimeRange,
    selectedFrequency,
  ]);

  return (
    <Card style={{ height: "22rem" }}>
      <Card.Header className="d-flex">
        Historical Valuation
        <div>
          <DropdownButton
            variant={""}
            size={"xs" as any}
            title={selectedLevel.label}
          >
            {LEVELS.map((level) => {
              return (
                <Dropdown.Item
                  active={selectedLevel.type === level.type}
                  key={level.type}
                  onClick={() => {
                    setSelectedLevel(level);
                  }}
                >
                  {level.label.toUpperCase()}
                </Dropdown.Item>
              );
            })}
          </DropdownButton>
        </div>
        <div>
          <DropdownButton
            variant={""}
            size={"xs" as any}
            title={selectedFrequency}
          >
            {FREQUENCIES.map((freq) => {
              return (
                <Dropdown.Item
                  active={selectedFrequency === freq}
                  key={freq}
                  onClick={() => {
                    setSelectedFrequency(freq);
                  }}
                >
                  {freq.toUpperCase()}
                </Dropdown.Item>
              );
            })}
          </DropdownButton>
        </div>
        <div>
          <DropdownButton
            variant={""}
            size={"xs" as any}
            title={selectedTimeRange.label}
          >
            {TIME_RANGES.map((range) => {
              return (
                <Dropdown.Item
                  active={range.label === selectedTimeRange.label}
                  key={range.label}
                  onClick={() => {
                    setSelectedTimeRange(range);
                  }}
                >
                  {range.label.toUpperCase()}
                </Dropdown.Item>
              );
            })}
          </DropdownButton>
        </div>
      </Card.Header>
      <Card.Body>
        {historicalValuation && (
          <Chart
            options={{
              chart: {
                animations: {
                  enabled: false,
                },
                stacked: true,
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
                type: historicalValuation.series_data.x_axis.type,
                tickAmount: 6,
                categories: historicalValuation.series_data.x_axis.categories,
                tooltip: {
                  enabled: false,
                },
                labels: {
                  rotate: 0,
                },
              },
              legend: {
                show: false,
              },
              yaxis: {
                show: false,
                min: 0,
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
                opacity: 0.8,
                type: "solid",
              },
              stroke: {
                width: 1,
              },
              colors: historicalValuation.series_data.series.map(
                (entry) => entry.colour
              ),
            }}
            series={historicalValuation.series_data.series}
            type={
              historicalValuation.series_data.x_axis.type === "datetime"
                ? "area"
                : "bar"
            }
            width="100%"
            height="250px"
          />
        )}
      </Card.Body>
    </Card>
  );
};
