import React, { useState, useEffect, useContext } from "react";
import { Navigate } from "react-router-dom";

import { AuthContext, ServicesContext } from "contexts";

import { UserAccountValuation } from "clients/finbot-client/types";

import { Money, RelativeValuationChange, BarLoader } from "components";
import { defaultMoneyFormatter } from "components/money";
import {
  EarningsReportPanel,
  HoldingsReportPanel,
  HistoricalValuationPanel,
  WealthDistributionPanel,
} from "./reports";
import { Row, Col, Card, Tabs, Tab } from "react-bootstrap";

import { DateTime } from "luxon";

const getRelativeChange = (startVal: number, finalVal: number) => {
  return (finalVal - startVal) / startVal;
};

const REPORTS = {
  HOLDINGS: "holdings",
  EARNINGS: "Earnings",
};

const DEFAULT_REPORT = REPORTS.HOLDINGS;

export const MainDashboard: React.FC<Record<string, never>> = () => {
  const { userAccountId } = useContext(AuthContext);
  const { finbotClient } = useContext(ServicesContext);
  const locale = "en-GB";
  const [configured, setConfigured] = useState<boolean | null>(null);
  const [valuation, setValuation] = useState<UserAccountValuation | null>(null);
  const [selectedReport, setSelectedReport] = useState<string>(DEFAULT_REPORT);

  useEffect(() => {
    const fetch = async () => {
      const configured = await finbotClient!.isAccountConfigured({
        account_id: userAccountId!,
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
          account_id: userAccountId!,
        });
        setValuation(result);
      }
    };
    fetch();
  }, [finbotClient, configured, userAccountId]);

  if (configured === false) {
    return <Navigate to={"/welcome"} />;
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
              {valuation !== null && (
                <strong>
                  <Money
                    amount={valuation.value}
                    locale={locale}
                    ccy={valuation.currency}
                    moneyFormatter={defaultMoneyFormatter}
                  />
                </strong>
              )}
            </Card.Body>
            {valuation === null && <BarLoader width={"100%"} />}
          </Card>
        </Col>
        <Col md={4} className="mt-3">
          <Card>
            <Card.Body>
              <Card.Title>Liabilities</Card.Title>
              {valuation !== null && (
                <Money
                  amount={valuation.total_liabilities}
                  locale={locale}
                  ccy={valuation.currency}
                  moneyFormatter={defaultMoneyFormatter}
                />
              )}
            </Card.Body>
            {valuation === null && <BarLoader width={"100%"} />}
          </Card>
        </Col>
        <Col md={4} className="mt-3">
          <Card>
            <Card.Body>
              <Card.Title>24h Change</Card.Title>
              {valuation?.change?.change_1day && (
                <RelativeValuationChange
                  amount={getRelativeChange(
                    valuation.value - valuation.change.change_1day,
                    valuation.value
                  )}
                />
              )}
            </Card.Body>
            {valuation === null && <BarLoader width={"100%"} />}
          </Card>
        </Col>
      </Row>
      <Row>
        <Col lg={6} md={12} sm={12} xs={12} className="mt-3">
          <HistoricalValuationPanel
            userAccountId={userAccountId!}
            locale={locale}
            moneyFormatter={defaultMoneyFormatter}
          />
        </Col>
        <Col lg={6} md={12} sm={12} xs={12} className="mt-3">
          <WealthDistributionPanel
            userAccountId={userAccountId!}
            locale={locale}
            moneyFormatter={defaultMoneyFormatter}
          />
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
                  userAccountId={userAccountId!}
                  locale={locale}
                  moneyFormatter={defaultMoneyFormatter}
                />
              )}
              {selectedReport === REPORTS.EARNINGS && (
                <EarningsReportPanel
                  userAccountId={userAccountId!}
                  locale={locale}
                  moneyFormatter={defaultMoneyFormatter}
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
