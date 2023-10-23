import React, { useState, useEffect } from "react";

import {
  useApi,
  UserAccountsValuationApi,
  LinkedAccountsValuationApi,
  ValuationFrequency,
  HistoricalValuation,
} from "clients";

import { Card, Dropdown, DropdownButton } from "react-bootstrap";
import Chart from "react-apexcharts";
import { MoneyFormatterType } from "components/money";

import { DateTime } from "luxon";
import { lastItem } from "utils/array";

interface TimeRange {
  from_time?: DateTime;
  to_time?: DateTime;
}

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
  props,
) => {
  const { userAccountId, locale, moneyFormatter } = props;
  const userAccountsValuationApi = useApi(UserAccountsValuationApi);
  const linkedAccountsValuationApi = useApi(LinkedAccountsValuationApi);
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
        userAccountId: userAccountId,
        fromTime: range.from_time?.toJSDate(),
        toTime: range.to_time?.toJSDate(),
        frequency: selectedFrequency as ValuationFrequency,
      };
      switch (selectedLevel.type) {
        case "account": {
          const data =
            await userAccountsValuationApi.getUserAccountHistoricalValuation(
              request,
            );
          setHistoricalValuation(data.historicalValuation);
          break;
        }
        case "linked_account": {
          const data =
            await linkedAccountsValuationApi.getLinkedAccountsHistoricalValuation(
              request,
            );
          setHistoricalValuation(data.historicalValuation);
          break;
        }
        case "asset_type": {
          const data =
            await userAccountsValuationApi.getUserAccountHistoricalValuationByAssetType(
              request,
            );
          setHistoricalValuation(data.historicalValuation);
          break;
        }
        case "asset_class": {
          const data =
            await userAccountsValuationApi.getUserAccountHistoricalValuationByAssetClass(
              request,
            );
          setHistoricalValuation(data.historicalValuation);
          break;
        }
      }
    };
    fetchValuation();
  }, [
    userAccountsValuationApi,
    linkedAccountsValuationApi,
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
                type: historicalValuation.seriesData.xAxis.type as
                  | "category"
                  | "datetime",
                tickAmount: 6,
                categories: historicalValuation.seriesData.xAxis.categories,
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
                      historicalValuation?.valuationCcy ?? "",
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
              colors: historicalValuation.seriesData.series.map(
                (entry) => entry.colour,
              ),
            }}
            series={historicalValuation.seriesData.series as Array<any>}
            type={
              historicalValuation.seriesData.xAxis.type === "datetime"
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
