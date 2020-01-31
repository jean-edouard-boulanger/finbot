import FinbotClient from './FinbotClient'
import Table from 'react-bootstrap/Table';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Card from 'react-bootstrap/Card';
import Chart from "react-apexcharts";
import Money from "./Money";
import DurationBadge from "./DurationBadge";
import ValuationChange from "./ValuationChange";
import Navbar from "./Navbar";
import React from 'react';
import BarLoader from "react-spinners/BarLoader";

function formatRelChange(val) {
  if (val === null || val === undefined || val === 0.0) {
    return (<span className="text-muted">-</span>);
  }
  if (val < 0) {
    return (<span className="text-danger">{(val * 100).toFixed(2)}%</span>)
  }
  else {
    return (<span className="text-success">+{(val * 100).toFixed(2)}%</span>)
  }
}

function byValuation(item1, item2) {
  return item2.valuation.value - item1.valuation.value
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

class App extends React.Component {
  constructor(props) {
    super(props);
    this.account_id = process.env.REACT_APP_SELECTED_USER;
    this.locale = "en-GB";
    this.state = {
      account: null,
      valuation: null,
      linked_accounts: [],
      historical_valuation: []
    };
  }

  async componentDidMount() {
    let finbot_client = new FinbotClient();

    const account_data = await finbot_client.getAccount({ account_id: this.account_id });
    const linked_accounts = await finbot_client.getLinkedAccounts({ account_id: this.account_id });
    const historical_valuation = await finbot_client.getAccountHistoricalValuation({ account_id: this.account_id });

    this.setState({
      valuation: account_data.valuation,
      linked_accounts: linked_accounts.sort(byValuation),
      valuation_high: maxValue(historical_valuation, (entry) => entry.value),
      historical_valuation: historical_valuation.map(entry => {
        return {
          date: Date.parse(entry.date).getTime(),
          value: entry.value
        }
      })
    });
  }

  render() {
    const locale = this.locale;
    const {
      valuation_high,
      valuation,
      linked_accounts,
      historical_valuation } = this.state;

    return (
      <>
        <Navbar />
        <Container>
          <Row className="mt-4">
            <Col>
              <Card>
                <Card.Body>
                  <Card.Title>Net Worth</Card.Title>
                  {valuation === null ? <BarLoader color={"#F0F0F0"} /> :
                    <strong><Money className="text-info"
                      amount={valuation.value}
                      locale={locale}
                      ccy={valuation.currency}
                      moneyFormatter={moneyFormatter} /></strong>}
                </Card.Body>
              </Card>
            </Col>
            <Col>
              <Card>
                <Card.Body>
                  <Card.Title>Liabilities</Card.Title>
                  {valuation === null ? <BarLoader color={"#F0F0F0"} /> :
                    <strong><Money className="text-info"
                      amount={valuation.total_liabilities}
                      locale={locale}
                      ccy={valuation.currency}
                      moneyFormatter={moneyFormatter} /></strong>}
                </Card.Body>
              </Card>
            </Col>
            <Col>
              <Card>
                <Card.Body>
                  <Card.Title>24h Change</Card.Title>
                  {valuation === null ? <BarLoader color={"#F0F0F0"} /> :
                    <strong>{
                      formatRelChange(
                        getRelativeChange(
                          valuation.value - valuation.change.change_1day,
                          valuation.value))}
                    </strong>}
                </Card.Body>
              </Card>
            </Col>
            <Col></Col>
          </Row>
          <Row className="mt-4">
            <Col>
              <Card>
                <Card.Header>Historical Valuation</Card.Header>
                <Card.Body>
                  <Chart
                    options={{
                      chart: {
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
                        categories: historical_valuation.map(entry => entry.date),
                        tooltip: {
                          enabled: false
                        }
                      },
                      yaxis: {
                        show: false,
                        min: 0,
                        max: valuation_high
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
                        data: historical_valuation.map(entry => entry.value)
                      }
                    ]}
                    type="area"
                    width="100%"
                    height="250px"
                  />
                </Card.Body>
              </Card>
            </Col>
            <Col>
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
                      tooltip: {
                        y: {
                          formatter: (value) => {
                            return moneyFormatter(value, locale, valuation.currency);
                          }
                        }
                      },
                      labels: linked_accounts.filter(entry => entry.valuation.value >= 0.0)
                        .map(entry => entry.linked_account.description)
                    }}
                    type="donut"
                    series={
                      linked_accounts.filter(entry => entry.valuation.value >= 0.0)
                        .map(entry => entry.valuation.value)
                    }
                    width="100%"
                    height="250px"
                  />
                </Card.Body>
              </Card>
            </Col>
          </Row>
          <Row className="mt-4">
            <Col>
              <h3>Holdings summary</h3>
            </Col>
          </Row>
          <Row className="mt-4">
            <Col>
              <Table responsive className="table-sm">
                <thead>
                  <tr>
                    <th>Account Name</th>
                    <th>Value</th>
                    <th>Hour</th>
                    <th>Day</th>
                    <th>Week</th>
                    <th>Month</th>
                    <th>Year</th>
                  </tr>
                </thead>
                <tbody>
                  {
                    linked_accounts.map(entry => {
                      const valuation = entry.valuation;
                      const change = valuation.change;
                      const linked_account = entry.linked_account;
                      const ccy = entry.valuation.currency;
                      return (
                        <tr key={`linked-account-${linked_account.id}`}>
                          <td>
                            {linked_account.description}
                            <h6><DurationBadge from={Date.parse(valuation.date)} />
                            </h6>
                          </td>
                          <td><Money amount={valuation.value} locale={locale} ccy={ccy} moneyFormatter={moneyFormatter} /></td>
                          <td><ValuationChange amount={change.change_1hour} /></td>
                          <td><ValuationChange amount={change.change_1day} /></td>
                          <td><ValuationChange amount={change.change_1week} /></td>
                          <td><ValuationChange amount={change.change_1month} /></td>
                          <td><ValuationChange amount={change.change_1year} /></td>
                        </tr>
                      )
                    })
                  }
                </tbody>
                {valuation === null ? <BarLoader color={"#F0F0F0"} /> :
                  <tfoot>
                    <tr>
                      <th>Totals</th>
                      <th><Money amount={valuation.value} locale={locale} ccy={valuation.currency} moneyFormatter={moneyFormatter} /></th>
                      <th><ValuationChange amount={valuation.change.change_1hour} /></th>
                      <th><ValuationChange amount={valuation.change.change_1day} /></th>
                      <th><ValuationChange amount={valuation.change.change_1week} /></th>
                      <th><ValuationChange amount={valuation.change.change_1month} /></th>
                      <th><ValuationChange amount={valuation.change.change_1year} /></th>
                    </tr>
                  </tfoot>
                }
              </Table>
            </Col>
          </Row>
        </Container>
      </>
    );
  }
}

export default App;
