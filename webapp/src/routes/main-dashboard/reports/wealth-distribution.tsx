import React, { useState, useEffect, useMemo } from "react";

import {
  useApi,
  UserAccountsValuationApi,
  LinkedAccountsValuationApi,
} from "clients";
import { Card, CardContent, CardHeader } from "components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "components/ui/dropdown-menu";
import { Button } from "components/ui/button";
import { ChevronDown } from "lucide-react";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { ChartTooltipContent } from "components/ui/chart";
import { MoneyFormatterType } from "components/money";

type AggregationMode =
  | "account"
  | "asset type"
  | "asset class"
  | "currency exposure";

const AGGREGATION_MODES: Array<AggregationMode> = [
  "account",
  "asset type",
  "asset class",
  "currency exposure",
];

const DEFAULT_AGGREGATION_MODE = AGGREGATION_MODES[0];

interface ValuationData {
  valuation_ccy: string;
  labels: Array<string>;
  values: Array<number>;
  colours?: Array<string>;
}

function useShowLegend(breakpoint = 765) {
  const [show, setShow] = useState(
    () => typeof window !== "undefined" && window.innerWidth >= breakpoint,
  );
  useEffect(() => {
    const mql = window.matchMedia(`(min-width: ${breakpoint}px)`);
    const handler = (e: MediaQueryListEvent) => setShow(e.matches);
    mql.addEventListener("change", handler);
    setShow(mql.matches);
    return () => mql.removeEventListener("change", handler);
  }, [breakpoint]);
  return show;
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
  const showLegend = useShowLegend();

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
        case "currency exposure": {
          const result = (
            await userAccountsValuationApi!.getUserAccountValuationByCurrencyExposure(
              { userAccountId },
            )
          ).valuation;
          setValuation({
            valuation_ccy: result.valuationCcy,
            labels: result.byCurrencyExposure.map((entry) => entry.name),
            values: result.byCurrencyExposure.map((entry) => entry.value),
            colours: result.byCurrencyExposure.map((entry) => entry.colour),
          });
          break;
        }
      }
    };
    fetch();
  }, [userAccountsValuationApi, userAccountId, aggregationMode]);

  const pieData = useMemo(() => {
    if (!valuation) return [];
    return valuation.labels.map((label, i) => ({
      name: label,
      value: valuation.values[i],
      fill: valuation.colours?.[i] ?? "#8884d8",
    }));
  }, [valuation]);

  const tooltipFormatter = (value: number) => {
    return moneyFormatter(value, locale, valuation?.valuation_ccy ?? "");
  };

  const total = useMemo(
    () => pieData.reduce((sum, d) => sum + d.value, 0),
    [pieData],
  );

  return (
    <Card className="h-[22rem]">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <span className="font-medium">Asset diversification</span>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="xs">
              BY {aggregationMode.toUpperCase()}{" "}
              <ChevronDown className="ml-1 h-3 w-3" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            {AGGREGATION_MODES.map((mode) => (
              <DropdownMenuItem
                key={mode}
                className={mode === aggregationMode ? "bg-accent" : ""}
                onClick={() => setAggregationMode(mode)}
              >
                BY {mode.toUpperCase()}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      </CardHeader>
      <CardContent>
        {valuation !== null && (
          <div className="flex items-center gap-4">
            <div className="shrink-0" style={{ width: showLegend ? "55%" : "100%", height: 240 }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    dataKey="value"
                    nameKey="name"
                    innerRadius="50%"
                    outerRadius="85%"
                    stroke="none"
                    isAnimationActive={false}
                  >
                    {pieData.map((entry, i) => (
                      <Cell key={i} fill={entry.fill} />
                    ))}
                  </Pie>
                  <Tooltip
                    content={
                      <ChartTooltipContent formatter={tooltipFormatter} />
                    }
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            {showLegend && (
              <div className="flex min-w-0 flex-1 flex-col gap-1.5 overflow-y-auto" style={{ maxHeight: 240 }}>
                {pieData.map((entry, i) => {
                  const pct = total > 0 ? ((entry.value / total) * 100).toFixed(1) : "0.0";
                  return (
                    <div key={i} className="flex items-center gap-2 text-xs">
                      <span
                        className="h-2 w-2 shrink-0 rounded-full"
                        style={{ backgroundColor: entry.fill }}
                      />
                      <span className="min-w-0 flex-1 truncate text-muted-foreground">
                        {entry.name}
                      </span>
                      <span className="shrink-0 tabular-nums font-medium">
                        {pct}%
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};
