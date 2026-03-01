import React, { useState, useEffect, useMemo } from "react";

import {
  useApi,
  UserAccountsValuationApi,
  LinkedAccountsValuationApi,
  ValuationFrequency,
  HistoricalValuation,
} from "clients";

import { Card, CardContent, CardHeader } from "components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "components/ui/dropdown-menu";
import { Button } from "components/ui/button";
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
} from "recharts";
import {
  ChartContainer,
  ChartTooltipContent,
  type ChartConfig,
} from "components/ui/chart";
import { MoneyFormatterType } from "components/money";

import { DateTime } from "luxon";
import { lastItem } from "utils/array";
import { ChevronDown } from "lucide-react";

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

function FilterDropdown({
  label,
  items,
  activeKey,
  onSelect,
}: {
  label: string;
  items: { key: string; label: string }[];
  activeKey: string;
  onSelect: (key: string) => void;
}) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          size="xs"
          className="border-border/50 bg-secondary/50 text-xs font-medium tracking-wide text-muted-foreground hover:text-foreground"
        >
          {label} <ChevronDown className="ml-1 h-3 w-3" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent>
        {items.map((item) => (
          <DropdownMenuItem
            key={item.key}
            className={activeKey === item.key ? "bg-accent text-primary" : ""}
            onClick={() => onSelect(item.key)}
          >
            {item.label}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export interface HistoricalValuationProps {
  userAccountId: number;
  locale: string;
  moneyFormatter: MoneyFormatterType;
  linkedAccountId?: number;
  linkedAccountName?: string;
}

export const HistoricalValuationPanel: React.FC<HistoricalValuationProps> = (
  props,
) => {
  const { userAccountId, locale, moneyFormatter, linkedAccountId, linkedAccountName } = props;
  const isSingleAccount = linkedAccountId !== undefined;
  const availableLevels = isSingleAccount
    ? LEVELS.filter((l) => l.type !== "linked_account")
    : LEVELS;
  const userAccountsValuationApi = useApi(UserAccountsValuationApi);
  const linkedAccountsValuationApi = useApi(LinkedAccountsValuationApi);
  const [now] = useState<DateTime>(DateTime.now());
  const [selectedLevel, setSelectedLevel] = useState(isSingleAccount ? LEVELS[0] : DEFAULT_LEVEL);
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
          if (isSingleAccount) {
            const data =
              await linkedAccountsValuationApi.getLinkedAccountsHistoricalValuation(
                request,
              );
            const filtered = {
              ...data.historicalValuation,
              seriesData: {
                ...data.historicalValuation.seriesData,
                series: data.historicalValuation.seriesData.series.filter(
                  (s) => s.name === linkedAccountName,
                ),
              },
            };
            setHistoricalValuation(filtered);
          } else {
            const data =
              await userAccountsValuationApi.getUserAccountHistoricalValuation(
                request,
              );
            setHistoricalValuation(data.historicalValuation);
          }
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

  const { chartData, chartConfig, seriesKeys, isDatetime } = useMemo(() => {
    if (!historicalValuation) {
      return { chartData: [], chartConfig: {} as ChartConfig, seriesKeys: [] as string[], isDatetime: false };
    }
    const { xAxis, series } = historicalValuation.seriesData;
    const categories = xAxis.categories as Array<string | number>;
    const isDatetime = xAxis.type === "datetime";

    const data = categories.map((cat, i) => {
      const row: Record<string, unknown> = { x: cat };
      series.forEach((s) => {
        row[s.name] = (s.data as number[])[i];
      });
      return row;
    });

    const config: ChartConfig = {};
    series.forEach((s) => {
      config[s.name] = { label: s.name, color: s.colour };
    });

    return {
      chartData: data,
      chartConfig: config,
      seriesKeys: series.map((s) => s.name),
      isDatetime,
    };
  }, [historicalValuation]);

  const tooltipFormatter = (value: number, name: string) => {
    return moneyFormatter(
      value,
      locale,
      historicalValuation?.valuationCcy ?? "",
    );
  };

  const labelFormatter = (label: string) => {
    if (isDatetime) {
      const dt = DateTime.fromMillis(Number(label));
      return dt.toFormat("dd-MMM-yyyy HH:mm");
    }
    return String(label);
  };

  return (
    <Card className="h-[22rem] border-border/50">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <span className="text-sm font-medium tracking-wide uppercase text-muted-foreground">
          Historical Valuation
        </span>
        <div className="flex gap-1">
          <FilterDropdown
            label={selectedLevel.label}
            items={availableLevels.map((l) => ({ key: l.type, label: l.label }))}
            activeKey={selectedLevel.type}
            onSelect={(key) =>
              setSelectedLevel(availableLevels.find((l) => l.type === key)!)
            }
          />
          <FilterDropdown
            label={selectedFrequency.toUpperCase()}
            items={FREQUENCIES.map((f) => ({
              key: f,
              label: f.toUpperCase(),
            }))}
            activeKey={selectedFrequency}
            onSelect={setSelectedFrequency}
          />
          <FilterDropdown
            label={selectedTimeRange.label}
            items={TIME_RANGES.map((r) => ({ key: r.label, label: r.label }))}
            activeKey={selectedTimeRange.label}
            onSelect={(key) =>
              setSelectedTimeRange(TIME_RANGES.find((r) => r.label === key)!)
            }
          />
        </div>
      </CardHeader>
      <CardContent>
        {historicalValuation ? (
          <ChartContainer config={chartConfig} className="h-[250px] w-full">
            {isDatetime ? (
              <AreaChart data={chartData}>
                <XAxis dataKey="x" tickCount={7} hide />
                <YAxis hide domain={[0, "auto"]} />
                <Tooltip
                  content={
                    <ChartTooltipContent
                      formatter={tooltipFormatter}
                      labelFormatter={labelFormatter}
                    />
                  }
                />
                {seriesKeys.map((key) => (
                  <Area
                    key={key}
                    type="monotone"
                    dataKey={key}
                    stackId="1"
                    fill={chartConfig[key].color}
                    stroke={chartConfig[key].color}
                    fillOpacity={0.6}
                    strokeWidth={1.5}
                    isAnimationActive={false}
                  />
                ))}
              </AreaChart>
            ) : (
              <BarChart data={chartData}>
                <XAxis dataKey="x" tickCount={7} hide />
                <YAxis hide domain={[0, "auto"]} />
                <Tooltip
                  content={
                    <ChartTooltipContent
                      formatter={tooltipFormatter}
                      labelFormatter={labelFormatter}
                    />
                  }
                />
                {seriesKeys.map((key) => (
                  <Bar
                    key={key}
                    dataKey={key}
                    stackId="1"
                    fill={chartConfig[key].color}
                    strokeWidth={0}
                    radius={[2, 2, 0, 0]}
                    isAnimationActive={false}
                  />
                ))}
              </BarChart>
            )}
          </ChartContainer>
        ) : (
          <div className="flex h-[250px] items-end gap-1 px-4">
            {Array.from({ length: 24 }).map((_, i) => (
              <div
                key={i}
                className="skeleton-shimmer flex-1 rounded-t"
                style={{ height: `${30 + Math.random() * 60}%` }}
              />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};
