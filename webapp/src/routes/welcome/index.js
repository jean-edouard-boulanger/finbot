import React, { useContext } from "react";

import { AuthContext } from "contexts";

import { Link } from "react-router-dom";

import { Card, Row, Col } from "react-bootstrap";

export const Welcome = () => {
  const { account } = useContext(AuthContext);
  return (
    <>
      <Row className={"mb-4"}>
        <Col md={12}>
          <Row>
            <Col>
              <div className={"page-header"}>
                <h1>
                  Welcome to finbot
                  <small>{` ${account.full_name.split(" ")[0]}`}</small>
                </h1>
              </div>
            </Col>
          </Row>
        </Col>
      </Row>
      <Row>
        <Col md={2} className={"mr-4"}>
          <img src={"/finbot_medium.png"} alt={"finbot"} />
        </Col>
        <Col md={6}>
          <Card>
            <Card.Body>
              <Card.Title>First steps</Card.Title>
              <Card.Text>
                <strong>Finbot</strong> is your personal finance assistant, it
                automatically gathers financial information from your personal
                accounts and displays them on your dashboard.
              </Card.Text>
              <Card.Text>
                To <strong>get started with finbot</strong>, you need to{" "}
                <Link to={"/settings/linked"}>link at least one account</Link>.
              </Card.Text>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </>
  );
};
