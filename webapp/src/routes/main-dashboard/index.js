import React, { useState, useEffect, useContext } from 'react';
import { Redirect } from 'react-router-dom';

import { AuthContext, ServicesContext } from "contexts";

import { Row, Col, Card, Nav, Tabs, Tab } from 'react-bootstrap';
import { Money } from "components"
import { HoldingsReport } from "./reports";
import Chart from "react-apexcharts";
import BarLoader from "react-spinners/BarLoader";

import queryString from 'query-string';


function formatRelChange(val) {
  if (val === null || val === undefined || val === 0.0) {
    return (<span className="text-muted">-</span>);
  }
  if (val < 0) {
    return (<span className="text-danger">{(val * 100).toFixed(2)}%</span>)
  } else {
    return (<span className="text-success">+{(val * 100).toFixed(2)}%</span>)
  }
}


function getRelativeChange(startVal, finalVal) {
  return (finalVal - startVal) / startVal;
}


function moneyFormatter(amount, locale, currency) {
  const localized = new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: currency
  }).format(Math.abs(amount));
  return amount >= 0 ? localized : `(${localized})`
}


function maxValue(list, accessor) {
  accessor = accessor || ((val) => val);
  let currentMax = null;
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
  EARNINGS: "Earnings"
}

function getAccountIdOverride() {
  const urlParams = queryString.parse(window.location.search);
  const userId = urlParams.userId;
  return userId === undefined ? null : userId;
}

export const MainDashboard = () => {
  const {account} = useContext(AuthContext);
  const {finbotClient} = useContext(ServicesContext);

  const locale = "en-GB";
  const [accountId] = useState(() => {
    const accountIdOverride = getAccountIdOverride();
    if(accountIdOverride !== null) {
      return accountIdOverride;
    }
    return account.id;
  });
  const [configured, setConfigured] = useState(null);
  const [valuation, setValuation] = useState(null);
  const [linkedAccounts, setLinkedAccounts] = useState([]);
  const [historicalValuation, setHistoricalValuation] = useState({data: [], high: 0});

  useEffect(() => {
    let fetch = async () => {
      const configured = await finbotClient.isAccountConfigured({account_id: accountId});
      setConfigured(configured);
    };
    fetch();
  }, [finbotClient, accountId])

  useEffect(() => {
    if(!configured) { return; }
    let fetch = async () => {
      const account_data = await finbotClient.getAccount({account_id: accountId});
      setValuation(account_data.valuation)

      const linked_accounts = await finbotClient.getLinkedAccountsValuation({account_id: accountId});
      setLinkedAccounts(linked_accounts);

      const historical_valuation = await finbotClient.getAccountHistoricalValuation({account_id: accountId});
      setHistoricalValuation({
        data: historical_valuation.map(entry => {
          return {
            date: Date.parse(entry.date).getTime(),
            value: entry.value
          }
        }),
        high: maxValue(historical_valuation, (entry) => entry.value)
      });
    };
    fetch();
  }, [finbotClient, configured, accountId]);

  if(configured === false) {
    return <Redirect to={"/welcome"} />
  }

  return (
    <>
      <Row>
        <Col md={4} className="mt-3">
          <Card>
            <Card.Body>
              <Card.Title>Net Worth</Card.Title>
              {valuation === null ? <BarLoader color={"#F0F0F0"}/> :
                <strong><Money className="text-info"
                               amount={valuation.value}
                               locale={locale}
                               ccy={valuation.currency}
                               moneyFormatter={moneyFormatter}/></strong>}
            </Card.Body>
          </Card>
        </Col>
        <Col md={4} className="mt-3">
          <Card>
            <Card.Body>
              <Card.Title>Liabilities</Card.Title>
              {valuation === null ? <BarLoader color={"#F0F0F0"}/> :
                <strong><Money className="text-info"
                               amount={valuation.total_liabilities}
                               locale={locale}
                               ccy={valuation.currency}
                               moneyFormatter={moneyFormatter}/></strong>}
            </Card.Body>
          </Card>
        </Col>
        <Col md={4} className="mt-3">
          <Card>
            <Card.Body>
              <Card.Title>24h Change</Card.Title>
              {(valuation?.change?.change_1day) ?
                <strong>{
                  formatRelChange(
                    getRelativeChange(
                      valuation.value - valuation.change.change_1day,
                      valuation.value))}
                </strong> :
                <BarLoader color={"#F0F0F0"}/>
              }
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
                      enabled: false
                    },
                    stacked: false,
                    zoom: {
                      enabled: false,
                    },
                    toolbar: {
                      show: true,
                      tools: {
                        download: false,
                      }
                    },
                  },
                  grid: {
                    show: false
                  },
                  theme: {
                    palette: "palette8"
                  },
                  dataLabels: {
                    enabled: false
                  },
                  xaxis: {
                    type: 'datetime',
                    categories: historicalValuation.data.map(entry => entry.date),
                    tooltip: {
                      enabled: false
                    }
                  },
                  yaxis: {
                    show: false,
                    min: 0,
                    max: historicalValuation.high
                  },
                  tooltip: {
                    x: {
                      format: 'dd-MMM-yyyy hh:mm'
                    },
                    y: {
                      formatter: (value) => {
                        return moneyFormatter(value, locale, valuation.currency);
                      }
                    }
                  },
                  fill: {
                    opacity: 0.5,
                    type: "solid"
                  },
                  stroke: {
                    width: 1,
                  }
                }}
                series={[
                  {
                    name: "value",
                    data: historicalValuation.data.map(entry => entry.value)
                  }
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
                    show: true
                  },
                  theme: {
                    palette: "palette8"
                  },
                  plotOptions: {
                    pie: {
                      customScale: 1
                    }
                  },
                  tooltip: {
                    y: {
                      formatter: (value) => {
                        const amount_str = moneyFormatter(value, locale, valuation.currency);
                        return `<span class="text-white">${amount_str}</span>`;
                      },
                      title: {
                        formatter: (seriesName) => {
                          return `<strong><span class="text-white">${seriesName}</span></strong>`;
                        }
                      }
                    }
                  },
                  responsive: [
                    {
                      breakpoint: 765,
                      options: {
                        legend: {
                          show: false
                        }
                      }
                    }],
                  labels: linkedAccounts.filter(entry => entry.valuation.value >= 0.0)
                    .map(entry => entry.linked_account.description)
                }}
                type="donut"
                series={
                  linkedAccounts.filter(entry => entry.valuation.value >= 0.0)
                    .map(entry => entry.valuation.value)
                }
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
              <Tabs id={"reports-nav"}>
                <Tab eventKey={REPORTS.HOLDINGS} title={"Holdings"}/>
              </Tabs>
            </Card.Header>
            <Card.Body>
              <HoldingsReport
                accountId={accountId}
                locale={locale}
                moneyFormatter={moneyFormatter} />
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </>
  );
}

export default MainDashboard;