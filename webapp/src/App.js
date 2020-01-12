import Table from 'react-bootstrap/Table';
import Container from 'react-bootstrap/Container';
import NavBar from 'react-bootstrap/NavBar';
import Navbar from 'react-bootstrap/Navbar';
import Nav from 'react-bootstrap/Nav';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Card from 'react-bootstrap/Card';
import DropDown from 'react-bootstrap/DropDown';
import Button from 'react-bootstrap/Button';
import ButtonGroup from 'react-bootstrap/ButtonGroup';
import Chart from "react-apexcharts";
import axios from 'axios';
import React from 'react';

function formatRelChange(val) {
  if(val === null || val === undefined || val === 0.0) {
    return (<span className="text-muted">-</span>);
  }
  if(val < 0) {
    return (<span className="text-danger">{(val * 100).toFixed(2)}%</span>)
  }
  else {
    return (<span className="text-success">+{(val * 100).toFixed(2)}%</span>)
  }
}

function getRelativeChange(startVal, finalVal) {
  return (finalVal - startVal) / startVal;
}

function moneyFormatter(amount, locale, currency) {
  return new Intl.NumberFormat(locale, { 
    style: 'currency', 
    currency: currency 
  }).format(amount);
}

function Money(props) {
  const {
    amount,
    locale,
    ccy
  } = props;
  return (<span {...props}>{moneyFormatter(amount, locale, ccy)}</span>);
}

function hasValue(val) {
  return val !== undefined && val !== null;
}

function ValuationChange(props) {
  const {
    amount,
    currentValue,
    previousValue,

    blankZero=true,
    decimalPlaces=2,
    format="absolute"
  } = props;

  const absFmt = (val) => { return val.toFixed(decimalPlaces); };
  const relFmt = (val) => { return `${(val * 100).toFixed(decimalPlaces)}%`; };
  const fmt = (format === "relative") ? relFmt : absFmt;

  function impl(val) {
    if(!hasValue(val) || (val === 0.0 && blankZero)) {
      return (<span className="text-muted">-</span>);
    }
    else if(val === 0.0) {
      return (<span className="text-muted">{fmt(0)}</span>);
    }
    else if(val < 0) {
      return (<span className="text-danger">{fmt(val)}</span>)
    }
    else {
      return (<span className="text-success">+{fmt(val)}</span>)
    }
  }

  // absolute change provided
  if(hasValue(amount)) {
    return impl(amount);
  }
  // current and previous values were provided, will compute difference
  else if(hasValue(currentValue) && hasValue(previousValue)) {
    return impl(currentValue - previousValue);
  }
  // invalid combination
  else {
    return impl(null);
  }
}

class FinbotApi {
  constructor(settings) {
    settings = settings || {};
    this.endpoint = settings.endpoint || "http://127.0.0.1:5003/api/v1"
  }

  handle_response(response) {
    const app_data = response.data;
    if(app_data.hasOwnProperty("error")) {
      throw app_data.error.debug_message;
    }
    return app_data;
  }

  async getAccount(settings) {
    const {account_id} = settings;
    const response = await axios.get(`${this.endpoint}/accounts/${account_id}`);
    return this.handle_response(response).result;
  }

  async getAccountHistoricalValuation(settings) {
    const {account_id} = settings;
    const response = await axios.get(`${this.endpoint}/accounts/${account_id}/history`);
    return this.handle_response(response).historical_valuation;
  }

  async getLinkedAccounts(settings) {
    const {account_id} = settings;
    const response = await axios.get(`${this.endpoint}/accounts/${account_id}/linked_accounts`);
    return this.handle_response(response).linked_accounts;
  }
};

class App extends React.Component {
  constructor(props) {
    super(props);
    this.account_id = 2;
    this.locale = "en-GB";
    this.state = {
      account: null,
      valuation: null,
      linked_accounts: [],
      historical_valuation: []
    };
  }

  async componentDidMount() {
    let finbot_api = new FinbotApi();

    const account_data = await finbot_api.getAccount({account_id: this.account_id});
    const linked_accounts = await finbot_api.getLinkedAccounts({account_id: this.account_id});
    const historical_valuation = await finbot_api.getAccountHistoricalValuation({account_id: this.account_id});

    this.setState({
      valuation: account_data.valuation,
      linked_accounts: linked_accounts,
      historical_valuation: historical_valuation.reverse().map(entry => {
        return {
          date:  Date.parse(entry.date).getTime(),
          value: entry.value
        }
      })
    });
  }

  render() {
    const locale = this.locale;
    const valuation = this.state.valuation;
    const linked_accounts = this.state.linked_accounts;
    const historical_valuation = this.state.historical_valuation;
    return (
      <>
        <NavBar bg="dark" variant="dark">
          <Navbar.Brand href="#home">Finbot</Navbar.Brand>
          <Nav className="mr-auto">
            <Nav.Link href="#home">Home</Nav.Link>
          </Nav>
        </NavBar>
        <Container>
          <Row className="mt-4">
            <Col>
              <Card>
                <Card.Body>
                  <Card.Title>Net Worth</Card.Title>
                  {valuation === null ? "-" :
                    <strong><Money className="text-info"
                                   amount={valuation.value} 
                                   locale={locale} 
                                   ccy={valuation.currency} /></strong>}
                </Card.Body>
              </Card>
            </Col>
            <Col>
              <Card>
                <Card.Body>
                  <Card.Title>24h Change</Card.Title>
                  {valuation  === null ? "-" : 
                    <strong>{
                      formatRelChange(
                        getRelativeChange(
                          valuation.value-valuation.change.change_1day, 
                          valuation.value))}
                    </strong>}
                </Card.Body>
                </Card>
            </Col>
            <Col></Col>
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
                        type: "area",
                        stacked: false,
                        zoom: {
                          type: 'x',
                          enabled: true,
                          autoScaleYaxis: true
                        },
                        toolbar: {
                          show: true,
                          tools: {
                            download: false,
                          }
                        }
                      },
                      xaxis: {
                        type: 'datetime',
                        categories: historical_valuation.map(entry => entry.date),
                        tooltip: {
                          enabled: false
                        }
                      },
                      yaxis: {
                        show: false
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
                      stroke: {
                        width: 1.8,
                      }
                    }}
                    series={[
                      {
                        name: "value",
                        data: historical_valuation.map(entry => entry.value)
                      }
                    ]}
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
                      labels: linked_accounts.map(entry => entry.linked_account.description)
                    }}
                    type="donut"
                    series={
                      linked_accounts.map(entry => entry.valuation.value)
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
              <Table bordered>
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
                    linked_accounts.sort((l1, l2) => {return l2.valuation.value - l1.valuation.value})
                                   .map(entry => {
                      const valuation = entry.valuation;
                      const change = valuation.change;
                      const linked_account = entry.linked_account;
                      const ccy = entry.valuation.currency;
                      return (
                        <tr key={`linked-account-${linked_account.id}`}>
                          <td>{linked_account.description}</td>
                          <td><Money amount={valuation.value} locale={locale} ccy={ccy} /></td>
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
                {valuation === null ? null :
                  <tfoot>
                    <tr>
                      <th>Totals</th>
                      <th><Money amount={valuation.value} locale={locale} ccy={valuation.currency} /></th>
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
