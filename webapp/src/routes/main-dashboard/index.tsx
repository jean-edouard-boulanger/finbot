import React, { useState, useEffect, useContext } from "react";
import { Navigate } from "react-router-dom";

import { AuthContext } from "contexts";
import {
  useApi,
  UserAccountsValuationApi,
  UserAccountValuation,
  UserAccountsApi,
} from "clients";

import { Money, RelativeValuationChange, BarLoader } from "components";
import { defaultMoneyFormatter } from "components/money";
import {
  EarningsReportPanel,
  HoldingsReportPanel,
  HistoricalValuationPanel,
  WealthDistributionPanel,
} from "./reports";

import { Card, CardContent, CardHeader, CardTitle } from "components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "components/ui/tabs";

import { DateTime } from "luxon";

const getRelativeChange = (startVal: number, finalVal: number) => {
  return (finalVal - startVal) / startVal;
};

const REPORTS = {
  HOLDINGS: "holdings",
  EARNINGS: "earnings",
};

const DEFAULT_REPORT = REPORTS.HOLDINGS;

export const MainDashboard: React.FC<Record<string, never>> = () => {
  const { userAccountId } = useContext(AuthContext);
  const locale = "en-GB";
  const userAccountValuationApi = useApi(UserAccountsValuationApi);
  const userAccountsApi = useApi(UserAccountsApi);
  const [configured, setConfigured] = useState<boolean | null>(null);
  const [valuation, setValuation] = useState<UserAccountValuation | null>(null);
  const [selectedReport, setSelectedReport] = useState<string>(DEFAULT_REPORT);

  useEffect(() => {
    const fetch = async () => {
      const result = await userAccountsApi.isUserAccountConfigured({
        userAccountId: userAccountId!,
      });
      setConfigured(result.configured);
    };
    fetch();
  }, [userAccountsApi]);

  useEffect(() => {
    if (!configured) {
      return;
    }
    const fetch = async () => {
      {
        const result = await userAccountValuationApi.getUserAccountValuation({
          userAccountId: userAccountId!,
        });
        setValuation(result.valuation);
      }
    };
    fetch();
  }, [userAccountValuationApi, configured, userAccountId]);

  if (configured === false) {
    return <Navigate to={"/welcome"} />;
  }

  return (
    <>
      <div className="mt-3 grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Net Worth{" "}
              {valuation !== null &&
                `(${DateTime.fromJSDate(valuation.date).toLocaleString(
                  DateTime.DATETIME_FULL,
                )})`}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {valuation !== null && (
              <strong className="text-2xl">
                <Money
                  amount={valuation.value}
                  locale={locale}
                  ccy={valuation.currency}
                  moneyFormatter={defaultMoneyFormatter}
                />
              </strong>
            )}
          </CardContent>
          {valuation === null && <BarLoader width={"100%"} />}
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Liabilities
            </CardTitle>
          </CardHeader>
          <CardContent>
            {valuation !== null && (
              <span className="text-2xl">
                <Money
                  amount={valuation.totalLiabilities}
                  locale={locale}
                  ccy={valuation.currency}
                  moneyFormatter={defaultMoneyFormatter}
                />
              </span>
            )}
          </CardContent>
          {valuation === null && <BarLoader width={"100%"} />}
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              24h Change
            </CardTitle>
          </CardHeader>
          <CardContent>
            {valuation?.change?.change1day && (
              <span className="text-2xl">
                <RelativeValuationChange
                  amount={getRelativeChange(
                    valuation.value - valuation.change.change1day,
                    valuation.value,
                  )}
                />
              </span>
            )}
          </CardContent>
          {valuation === null && <BarLoader width={"100%"} />}
        </Card>
      </div>
      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <HistoricalValuationPanel
          userAccountId={userAccountId!}
          locale={locale}
          moneyFormatter={defaultMoneyFormatter}
        />
        <WealthDistributionPanel
          userAccountId={userAccountId!}
          locale={locale}
          moneyFormatter={defaultMoneyFormatter}
        />
      </div>
      <div className="mt-4">
        <Tabs
          defaultValue={DEFAULT_REPORT}
          value={selectedReport}
          onValueChange={(value) => setSelectedReport(value)}
        >
          <Card>
            <CardHeader className="pb-0">
              <TabsList className="self-start">
                <TabsTrigger value={REPORTS.HOLDINGS}>Holdings</TabsTrigger>
                <TabsTrigger value={REPORTS.EARNINGS}>Earnings</TabsTrigger>
              </TabsList>
            </CardHeader>
            <CardContent className="pt-4">
              <TabsContent value={REPORTS.HOLDINGS} className="mt-0">
                <HoldingsReportPanel
                  userAccountId={userAccountId!}
                  locale={locale}
                  moneyFormatter={defaultMoneyFormatter}
                />
              </TabsContent>
              <TabsContent value={REPORTS.EARNINGS} className="mt-0">
                <EarningsReportPanel
                  userAccountId={userAccountId!}
                  locale={locale}
                  moneyFormatter={defaultMoneyFormatter}
                />
              </TabsContent>
            </CardContent>
          </Card>
        </Tabs>
      </div>
    </>
  );
};

export default MainDashboard;
