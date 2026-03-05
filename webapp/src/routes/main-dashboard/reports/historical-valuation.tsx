import React, { useState, useEffect, useMemo } from "react";

import {
  useApi,
  UserAccountsValuationApi,
  LinkedAccountsValuationApi,
  ValuationFrequency,
  HistoricalValuation,
} from "clients";

import { Alert, AlertTitle, AlertDescription } from "components/ui/alert";
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
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
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

const DEFAULT_LEVEL = LEVELS[0];

const FREQUENCIES: Array<string> = [
  "Daily",
  "Weekly",
  "Monthly",
  "Quarterly",
  "Yearly",
];

const DEFAULT_FREQUENCY = FREQUENCIES[0];

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
  const {
    userAccountId,
    locale,
    moneyFormatter,
    linkedAccountId,
    linkedAccountName,
  } = props;
  const isSingleAccount = linkedAccountId !== undefined;
  const availableLevels = isSingleAccount
    ? LEVELS.filter((l) => l.type !== "linked_account")
    : LEVELS;
  const userAccountsValuationApi = useApi(UserAccountsValuationApi);
  const linkedAccountsValuationApi = useApi(LinkedAccountsValuationApi);
  const [now] = useState<DateTime>(DateTime.now());
  const [selectedLevel, setSelectedLevel] = useState(DEFAULT_LEVEL);
  const [selectedFrequency, setSelectedFrequency] = useState(DEFAULT_FREQUENCY);
  const [selectedTimeRange, setSelectedTimeRange] =
    useState<TimeRangeChoiceType>(DEFAULT_RANGE);
  const [historicalValuation, setHistoricalValuation] =
    useState<HistoricalValuation | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setHistoricalValuation(null);
    setError(null);
    const fetchValuation = async () => {
      try {
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
              const hv = data.historicalValuation;
              const matchedSeries = hv.seriesData.series.filter(
                (s) => s.name === linkedAccountName,
              );
              // Trim x-axis to only indices where this series has data
              const seriesData = matchedSeries[0]?.data as
                | (number | null)[]
                | undefined;
              const categories = hv.seriesData.xAxis.categories as (
                | string
                | number
              )[];
              if (seriesData) {
                const firstIdx = seriesData.findIndex((v) => v != null);
                const lastIdx =
                  seriesData.length -
                  1 -
                  [...seriesData].reverse().findIndex((v) => v != null);
                const trimmedCategories = categories.slice(
                  firstIdx,
                  lastIdx + 1,
                );
                const trimmedSeries = matchedSeries.map((s) => ({
                  ...s,
                  data: (s.data as (number | null)[]).slice(
                    firstIdx,
                    lastIdx + 1,
                  ),
                }));
                setHistoricalValuation({
                  ...hv,
                  seriesData: {
                    xAxis: {
                      ...hv.seriesData.xAxis,
                      categories: trimmedCategories,
                    },
                    series: trimmedSeries,
                  },
                });
              } else {
                setHistoricalValuation({
                  ...hv,
                  seriesData: { ...hv.seriesData, series: matchedSeries },
                });
              }
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
                {
                  ...request,
                  linkedAccountId: linkedAccountId,
                },
              );
            setHistoricalValuation(data.historicalValuation);
            break;
          }
          case "asset_class": {
            const data =
              await userAccountsValuationApi.getUserAccountHistoricalValuationByAssetClass(
                {
                  ...request,
                  linkedAccountId: linkedAccountId,
                },
              );
            setHistoricalValuation(data.historicalValuation);
            break;
          }
        }
      } catch (e) {
        setError(`${e}`);
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

  const isSingleSeries = selectedLevel.type === "account";
  const gainColor = "hsl(var(--gain))";
  const lossColor = "hsl(var(--loss))";

  const { chartData, chartConfig, seriesKeys, isDatetime, gradientOffset } =
    useMemo(() => {
      if (!historicalValuation) {
        return {
          chartData: [],
          chartConfig: {} as ChartConfig,
          seriesKeys: [] as string[],
          isDatetime: false,
          gradientOffset: 1,
        };
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
        config[s.name] = {
          label: s.name,
          color: isSingleSeries ? gainColor : s.colour,
        };
      });

      // Compute gradient stop offset for area chart (where y=0 falls as fraction from top)
      let gradientOffset = 0;
      if (isSingleSeries && series.length === 1) {
        const values = (series[0].data as (number | null)[]).filter(
          (v): v is number => v != null,
        );
        const max = Math.max(...values);
        const min = Math.min(...values);
        if (max <= 0) {
          gradientOffset = 0;
        } else if (min >= 0) {
          gradientOffset = 1;
        } else {
          gradientOffset = max / (max - min);
        }
      }

      return {
        chartData: data,
        chartConfig: config,
        seriesKeys: series.map((s) => s.name),
        isDatetime,
        gradientOffset,
      };
    }, [historicalValuation, isSingleSeries]);

  const xTickFormatter = (value: string | number) => {
    if (!isDatetime) return String(value);
    const num = Number(value);
    const dt = isNaN(num)
      ? DateTime.fromISO(String(value))
      : DateTime.fromMillis(num);
    return dt.toFormat("MMM ''yy");
  };

  const yTickFormatter = (value: number) => {
    const ccy = historicalValuation?.valuationCcy ?? "";
    const abs = Math.abs(value);
    let formatted: string;
    if (abs >= 1_000_000_000) {
      formatted = `${Math.round(value / 1_000_000_000)}B`;
    } else if (abs >= 1_000_000) {
      formatted = `${Math.round(value / 1_000_000)}M`;
    } else if (abs >= 1_000) {
      formatted = `${Math.round(value / 1_000)}k`;
    } else {
      formatted = Math.round(value).toString();
    }
    return ccy ? `${ccy}${formatted}` : formatted;
  };

  const hasNegativeValues = useMemo(() => {
    if (!isSingleSeries || !historicalValuation) return false;
    const series = historicalValuation.seriesData.series;
    if (series.length !== 1) return false;
    return (series[0].data as (number | null)[]).some(
      (v) => v != null && v < 0,
    );
  }, [historicalValuation, isSingleSeries]);

  const xTickInterval = Math.max(Math.ceil(chartData.length / 6) - 1, 0);

  const tooltipFormatter = (value: number) => {
    return moneyFormatter(
      value,
      locale,
      historicalValuation?.valuationCcy ?? "",
    );
  };

  const labelFormatter = (label: string) => {
    if (isDatetime) {
      const num = Number(label);
      const dt = isNaN(num)
        ? DateTime.fromISO(label)
        : DateTime.fromMillis(num);
      return dt.toFormat("dd MMM yyyy");
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
            items={availableLevels.map((l) => ({
              key: l.type,
              label: l.label,
            }))}
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
          <ChartContainer
            config={chartConfig}
            className="h-[250px] w-full animate-fade-up"
          >
            {isDatetime ? (
              <AreaChart data={chartData}>
                {isSingleSeries && (
                  <defs>
                    <linearGradient
                      id="gainLossGradient"
                      x1="0"
                      y1="0"
                      x2="0"
                      y2="1"
                    >
                      <stop
                        offset={0}
                        stopColor={gainColor}
                        stopOpacity={0.6}
                      />
                      <stop
                        offset={gradientOffset}
                        stopColor={gainColor}
                        stopOpacity={0.6}
                      />
                      <stop
                        offset={gradientOffset}
                        stopColor={lossColor}
                        stopOpacity={0.6}
                      />
                      <stop
                        offset={1}
                        stopColor={lossColor}
                        stopOpacity={0.6}
                      />
                    </linearGradient>
                    <linearGradient
                      id="gainLossStroke"
                      x1="0"
                      y1="0"
                      x2="0"
                      y2="1"
                    >
                      <stop offset={0} stopColor={gainColor} stopOpacity={1} />
                      <stop
                        offset={gradientOffset}
                        stopColor={gainColor}
                        stopOpacity={1}
                      />
                      <stop
                        offset={gradientOffset}
                        stopColor={lossColor}
                        stopOpacity={1}
                      />
                      <stop offset={1} stopColor={lossColor} stopOpacity={1} />
                    </linearGradient>
                  </defs>
                )}
                <XAxis
                  dataKey="x"
                  interval={xTickInterval}
                  axisLine={false}
                  tickLine={false}
                  tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
                  tickFormatter={xTickFormatter}
                  padding={{ left: 20 }}
                />
                <YAxis
                  orientation="right"
                  tickCount={4}
                  axisLine={false}
                  tickLine={false}
                  tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
                  tickFormatter={yTickFormatter}
                  width={60}
                  domain={[(min: number) => Math.min(min, 0), "auto"]}
                />
                {isSingleSeries && hasNegativeValues && (
                  <ReferenceLine
                    y={0}
                    stroke="hsl(var(--muted-foreground))"
                    strokeDasharray="3 3"
                    strokeOpacity={0.5}
                  />
                )}
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
                    stackId={isSingleSeries ? undefined : "1"}
                    fill={
                      isSingleSeries
                        ? "url(#gainLossGradient)"
                        : chartConfig[key].color
                    }
                    stroke={
                      isSingleSeries
                        ? "url(#gainLossStroke)"
                        : chartConfig[key].color
                    }
                    fillOpacity={isSingleSeries ? 1 : 0.6}
                    strokeWidth={1.5}
                    isAnimationActive={false}
                  />
                ))}
              </AreaChart>
            ) : (
              <BarChart data={chartData}>
                <XAxis
                  dataKey="x"
                  interval={xTickInterval}
                  axisLine={false}
                  tickLine={false}
                  tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
                  tickFormatter={xTickFormatter}
                  padding={{ left: 20 }}
                />
                <YAxis
                  orientation="right"
                  tickCount={4}
                  axisLine={false}
                  tickLine={false}
                  tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
                  tickFormatter={yTickFormatter}
                  width={60}
                  domain={[(min: number) => Math.min(min, 0), "auto"]}
                />
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
                    stackId={isSingleSeries ? undefined : "1"}
                    fill={chartConfig[key].color}
                    strokeWidth={0}
                    radius={[2, 2, 0, 0]}
                    isAnimationActive={false}
                  >
                    {isSingleSeries &&
                      chartData.map((row, i) => (
                        <Cell
                          key={i}
                          fill={
                            (row[key] as number) < 0 ? lossColor : gainColor
                          }
                        />
                      ))}
                  </Bar>
                ))}
              </BarChart>
            )}
          </ChartContainer>
        ) : error !== null ? (
          <div className="flex h-[250px] items-center justify-center">
            <Alert variant="destructive">
              <AlertTitle>Failed to load chart</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          </div>
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
