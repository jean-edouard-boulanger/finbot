import FinbotClient from "../../clients/finbot-client";
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Card from 'react-bootstrap/Card';
import Chart from "react-apexcharts";
import Money from "../../components/money"
import HoldingsTable from "../../components/holdings-table";
import React from 'react';
import BarLoader from "react-spinners/BarLoader";
import queryString from 'query-string';

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


function getAccountId() {
    const urlParams = queryString.parse(window.location.search);
    const userId = urlParams.userId;
    return userId === undefined ? 1 : userId;
}


class MainDashboard extends React.Component {
    constructor(props) {
        super(props);
        this.account_id = getAccountId();
        this.locale = "en-GB";
        this.state = {
            account: null,
            valuation: null,
            linked_accounts: [],
            historical_valuation: []
        };
    }

    async componentDidMount() {
        //redirect to sign up page if not logged in
        if (!localStorage.getItem("identity")) {
            console.log("there is not a user")
            this.props.history.push("/auth/log-in");
            return;
        }
        let finbot_client = new FinbotClient();
        console.log("acccccccid", this.account_id)

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
        const valuationIsLoaded = valuation !== null && valuation.change !== null

        return (
            <div className="main-wrapper">
                <Container>
                    <Row>
                        <Col md={4} className="mt-3">
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
                        <Col md={4} className="mt-3">
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
                        <Col md={4} className="mt-3">
                            <Card>
                                <Card.Body>
                                    <Card.Title>24h Change</Card.Title>
                                    {(valuationIsLoaded) ?
                                        <strong>{
                                            formatRelChange(
                                                getRelativeChange(
                                                    valuation.value - valuation.change.change_1day,
                                                    valuation.value))}
                                        </strong> :
                                        <BarLoader color={"#F0F0F0"} />
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
                                                        return moneyFormatter(value, locale, valuation.currency);
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
                    <HoldingsTable
                        linked_accounts={linked_accounts}
                        locale={locale}
                        moneyFormatter={moneyFormatter}
                        valuation={valuation}
                        valuationIsLoaded={valuationIsLoaded} />
                </Container>
            </div>
        );
    }
}


export { MainDashboard };
