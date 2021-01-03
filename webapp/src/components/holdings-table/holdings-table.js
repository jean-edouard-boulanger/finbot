import React from "react";
import PropTypes from "prop-types";
import Row from 'react-bootstrap/Row';
import Card from 'react-bootstrap/Card';
import Col from 'react-bootstrap/Col';
import Table from 'react-bootstrap/Table';
import BarLoader from "react-spinners/BarLoader";

import DurationBadge from "components/duration-badge";
import ValuationChange from "components/valuation-change";
import Money from "components/money";


const HoldingsTable = props => {
  const {
    linked_accounts,
    locale,
    moneyFormatter,
    valuation,
    valuationIsLoaded
  } = props;

  return (
    <Row className="mt-3">
      <Col>
        <Card>
          <Card.Header>Holdings Summary</Card.Header>
          <Card.Body>
            <Table responsive className="table-sm">
              <thead>
              <tr>
                <th>Account Name</th>
                <th>Value</th>
                <th>1D</th>
                <th>1W</th>
                <th>1M</th>
                <th>1Y</th>
                <th>2Y</th>
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
                        <h6><DurationBadge from={Date.parse(valuation.date)}/>
                        </h6>
                      </td>
                      <td><Money amount={valuation.value} locale={locale} ccy={ccy} moneyFormatter={moneyFormatter}/>
                      </td>
                      <td> {change ? <ValuationChange amount={change.change_1day}/> : "-"}</td>
                      <td> {change ? <ValuationChange amount={change.change_1week}/> : "-"}</td>
                      <td> {change ? <ValuationChange amount={change.change_1month}/> : "-"}</td>
                      <td> {change ? <ValuationChange amount={change.change_1year}/> : "-"}</td>
                      <td> {change ? <ValuationChange amount={change.change_2years}/> : "-"}</td>
                    </tr>
                  )
                })
              }
              </tbody>
              {valuation === null ? <tfoot>
                <tr>
                  <th><BarLoader color={"#F0F0F0"}/></th>
                </tr>
                </tfoot> :
                <tfoot>
                <tr>
                  <th>Totals</th>
                  <th><Money amount={valuation.value} locale={locale} ccy={valuation.currency}
                             moneyFormatter={moneyFormatter}/></th>
                  <th>{valuationIsLoaded ? <ValuationChange amount={valuation.change.change_1day}/> : "-"}</th>
                  <th>{valuationIsLoaded ? <ValuationChange amount={valuation.change.change_1week}/> : "-"}</th>
                  <th>{valuationIsLoaded ? <ValuationChange amount={valuation.change.change_1month}/> : "-"}</th>
                  <th>{valuationIsLoaded ? <ValuationChange amount={valuation.change.change_1year}/> : "-"}</th>
                  <th>{valuationIsLoaded ? <ValuationChange amount={valuation.change.change_2years}/> : "-"}</th>
                </tr>
                </tfoot>
              }
            </Table>
          </Card.Body>
        </Card>
      </Col>
    </Row>
  )
}


HoldingsTable.propTypes = {
  linked_accounts: PropTypes.array,
  locale: PropTypes.string,
  moneyFormatter: PropTypes.func,
  valuation: PropTypes.object,
  valuationIsLoaded: PropTypes.bool,
};

export {HoldingsTable};

