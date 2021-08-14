import React, { useState, useEffect, useContext } from "react";
import { Redirect } from "react-router-dom";

import { AuthContext, ServicesContext } from "contexts";

import { Money, RelativeValuationChange } from "components";
import { MoneyFormatterType } from "components/money";
import { EarningsReportPanel, HoldingsReportPanel } from "./reports";

import { Row, Col, Card, Tabs, Tab } from "react-bootstrap";
import Chart from "react-apexcharts";
import BarLoader from "react-spinners/BarLoader";

import { DateTime } from "luxon";
import {
  LinkedAccountsValuationEntry,
  UserAccountValuation,
} from "clients/finbot-client/types";

const getRelativeChange = (startVal: number, finalVal: number) => {
  return (finalVal - startVal) / startVal;
};

const moneyFormatter: MoneyFormatterType = (amount, locale, currency) => {
  const localized = new Intl.NumberFormat(locale, {
    style: "currency",
    currency: currency,
  }).format(Math.abs(amount));
  return amount >= 0 ? localized : `(${localized})`;
};

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

const REPORTS = {
  HOLDINGS: "holdings",
  EARNINGS: "Earnings",
};

const DEFAULT_REPORT = REPORTS.HOLDINGS;

interface HistoricalValuationEntry {
  timestamp: number;
  value: number;
}

interface HistoricalValuation {
  data: Array<HistoricalValuationEntry>;
  high: number | null;
}

export const MainDashboard = () => {
  const { account } = useContext(AuthContext);
  const { finbotClient } = useContext(ServicesContext);
  const locale = "en-GB";
  const [configured, setConfigured] = useState<boolean | null>(null);
  const [valuation, setValuation] = useState<UserAccountValuation | null>(null);
  const [linkedAccountsValuation, setLinkedAccountsValuation] = useState<
    Array<LinkedAccountsValuationEntry>
  >([]);
  const [
    historicalValuation,
    setHistoricalValuation,
  ] = useState<HistoricalValuation>({
    data: [],
    high: 0,
  });
  const [selectedReport, setSelectedReport] = useState<string>(DEFAULT_REPORT);
  const userAccountId = account!.id;

  useEffect(() => {
    const fetch = async () => {
      const configured = await finbotClient!.isAccountConfigured({
        account_id: userAccountId,
      });
      setConfigured(configured);
    };
    fetch();
  }, [finbotClient]);

  useEffect(() => {
    if (!configured) {
      return;
    }
    const fetch = async () => {
      {
        const result = await finbotClient!.getAccountValuation({
          account_id: userAccountId,
        });
        setValuation(result);
      }

      {
        const result = await finbotClient!.getLinkedAccountsValuation({
          account_id: userAccountId,
        });
        setLinkedAccountsValuation(result);
      }

      {
        const result = await finbotClient!.getAccountHistoricalValuation({
          account_id: userAccountId,
        });
        setHistoricalValuation({
          data: result.map((entry) => {
            return {
              timestamp: DateTime.fromISO(entry.date).toMillis(),
              value: entry.value,
            };
          }),
          high: maxValue(result, (entry) => entry.value),
        });
      }
    };
    fetch();
  }, [finbotClient, configured, userAccountId]);

  if (configured === false) {
    return <Redirect to={"/welcome"} />;
  }

  return (
    <>
      <Row>
        <Col md={4} className="mt-3">
          <Card>
            <Card.Body>
              <Card.Title>
                Net Worth{" "}
                {valuation !== null &&
                  `(${DateTime.fromISO(valuation.date).toLocaleString(
                    DateTime.DATETIME_FULL
                  )})`}
              </Card.Title>
              {valuation === null ? (
                <BarLoader color={"#F0F0F0"} />
              ) : (
                <strong>
                  <Money
                    amount={valuation.value}
                    locale={locale}
                    ccy={valuation.currency}
                    moneyFormatter={moneyFormatter}
                  />
                </strong>
              )}
            </Card.Body>
          </Card>
        </Col>
        <Col md={4} className="mt-3">
          <Card>
            <Card.Body>
              <Card.Title>Liabilities</Card.Title>
              {valuation === null ? (
                <BarLoader color={"#F0F0F0"} />
              ) : (
                <strong>
                  <Money
                    amount={valuation.total_liabilities}
                    locale={locale}
                    ccy={valuation.currency}
                    moneyFormatter={moneyFormatter}
                  />
                </strong>
              )}
            </Card.Body>
          </Card>
        </Col>
        <Col md={4} className="mt-3">
          <Card>
            <Card.Body>
              <Card.Title>24h Change</Card.Title>
              {valuation?.change?.change_1day ? (
                <RelativeValuationChange
                  amount={getRelativeChange(
                    valuation.value - valuation.change.change_1day,
                    valuation.value
                  )}
                />
              ) : (
                <BarLoader color={"#F0F0F0"} />
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>
      <Row>
        <Col lg={6} md={12} sm={12} xs={12} className="mt-3">
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
                    max: historicalValuation.high,
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
                          valuation!.currency
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
        </Col>
        <Col lg={6} md={12} sm={12} xs={12} className="mt-3">
          <Card>
            <Card.Header>Wealth Distribution</Card.Header>
            <Card.Body>
              <Chart
                options={{
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
                          valuation!.currency
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
                  labels: linkedAccountsValuation
                    .filter((entry) => entry.valuation.value >= 0.0)
                    .map((entry) => entry.linked_account.description),
                }}
                type="donut"
                series={linkedAccountsValuation
                  .filter((entry) => entry.valuation.value >= 0.0)
                  .map((entry) => entry.valuation.value)}
                width="100%"
                height="250px"
              />
            </Card.Body>
          </Card>
        </Col>
      </Row>
      <Row className="mt-3">
        <Col>
          <Card>
            <Card.Header>
              <Tabs
                id={"reports-nav"}
                activeKey={selectedReport}
                onSelect={(reportSelection) =>
                  setSelectedReport(reportSelection ?? DEFAULT_REPORT)
                }
              >
                <Tab eventKey={REPORTS.HOLDINGS} title={"Holdings"} />
                <Tab eventKey={REPORTS.EARNINGS} title={"Earnings"} />
              </Tabs>
            </Card.Header>
            <Card.Body>
              {selectedReport === REPORTS.HOLDINGS && (
                <HoldingsReportPanel
                  accountId={userAccountId}
                  locale={locale}
                  moneyFormatter={moneyFormatter}
                />
              )}
              {selectedReport === REPORTS.EARNINGS && (
                <EarningsReportPanel
                  accountId={userAccountId}
                  locale={locale}
                  moneyFormatter={moneyFormatter}
                />
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </>
  );
};

export default MainDashboard;
