import Table from 'react-bootstrap/Table';
import Container from 'react-bootstrap/Container';
import NavBar from 'react-bootstrap/NavBar';
import Navbar from 'react-bootstrap/Navbar';
import Nav from 'react-bootstrap/Nav';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Card from 'react-bootstrap/Card';
import Chart from "react-apexcharts";
import axios from 'axios';
import React from 'react';

function formatMoney(amount, locale, currency) {
  console.log(locale);
  return new Intl.NumberFormat(locale, { 
    style: 'currency', 
    currency: currency 
  }).format(amount);
}

function formatChange(val) {
  if(val === null || val === undefined || val === 0.0) {
    return (<span className="text-muted">-</span>);
  }
  if(val < 0) {
    return (<span className="text-danger">{val.toFixed(2)}</span>)
  }
  else {
    return (<span className="text-success">+{val.toFixed(2)}</span>)
  }
}

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
  console.log(startVal);
  console.log(finalVal);
  return (finalVal - startVal) / startVal;
}

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
    const account_response = (await axios.get(`http://127.0.0.1:5003/api/v1/accounts/${this.account_id}`)).data;
    const valuation = account_response.result.valuation;
    const account = account_response.user_account;

    const linked_response = (await axios.get(`http://127.0.0.1:5003/api/v1/accounts/${this.account_id}/linked_accounts`)).data
    const linked_accounts = linked_response.linked_accounts

    const history_response = (await axios.get(`http://127.0.0.1:5003/api/v1/accounts/${this.account_id}/history`)).data
    const historical_valuation = history_response.historical_valuation;

    this.setState({
      account: account,
      valuation: valuation,
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
                    <strong>{formatMoney(valuation.value, locale, valuation.currency)}</strong>}
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
              <Chart
                options={{
                  chart: {
                    id: "basic-bar",
                    type: "area",
                    stacked: false,
                    zoom: {
                      type: 'x',
                      enabled: true,
                      autoScaleYaxis: true
                    }
                  },
                  xaxis: {
                    type: 'datetime',
                    categories: historical_valuation.map(entry => entry.date),
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
                        return formatMoney(value, locale, valuation.currency);
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
                height="300px"
              />
            </Col>
            <Col>
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
                                   .map(linked => {
                      const change = linked.valuation.change;
                      const linked_account = linked.linked_account;
                      const currency = linked.valuation.currency;
                      return (
                        <tr key={`linked-account-${linked_account.id}`}>
                          <td>{linked.linked_account.description}</td>
                          <td>{formatMoney(linked.valuation.value, locale, currency)}</td>
                          <td>{formatChange(change.change_1hour)}</td>
                          <td>{formatChange(change.change_1day)}</td>
                          <td>{formatChange(change.change_1week)}</td>
                          <td>{formatChange(change.change_1month)}</td>
                          <td>{formatChange(change.change_1year)}</td>
                        </tr>
                      )
                    })
                  }
                </tbody>
                {valuation === null ? "" :
                  <tfoot>
                    <tr>
                      <th>Totals</th>
                      <th>{formatMoney(valuation.value, locale, valuation.currency)}</th>
                      <th>{formatChange(valuation.change.change_1hour)}</th>
                      <th>{formatChange(valuation.change.change_1day)}</th>
                      <th>{formatChange(valuation.change.change_1week)}</th>
                      <th>{formatChange(valuation.change.change_1month)}</th>
                      <th>{formatChange(valuation.change.change_1year)}</th>
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
