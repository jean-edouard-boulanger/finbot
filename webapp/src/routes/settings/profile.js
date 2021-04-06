import React, { useContext, useEffect, useState } from "react";

import { ServicesContext, AuthContext } from "contexts";

import { Row, Col, Form } from "react-bootstrap";
import { LoadingButton } from "../../components/loading-button";

import * as Yup from "yup";

const PROFILE_SCHEMA = Yup.object().shape({

})

export const ProfileSettings = () => {
  const { finbotClient } = useContext(ServicesContext);
  const auth = useContext(AuthContext);
  const [account, setAccount] = useState(null);

  useEffect(() => {
    const fetch = async () => {
      const results = await finbotClient.getAccount({
        account_id: auth.account.id,
      });
      console.log(results.user_account);
      setAccount(results.user_account);
    };
    fetch();
  }, [finbotClient, auth.account]);

  const valuationCurrency =
    (account ?? { settings: {} }).settings.valuation_ccy || "USD";

  return (
    <>
      <Row className={"mb-4"}>
        <Col>
          <h3>Profile</h3>
        </Col>
      </Row>
      <Row>
        <Col>
          <Form>
            <Form.Group>
              <Form.Label>Full name</Form.Label>
              <Form.Control
                type={"text"}
                value={(account ?? {}).full_name || ""}
                placeholder={"Full name"}
              />
            </Form.Group>
            <Form.Group>
              <Form.Label>Email</Form.Label>
              <Form.Control
                type={"text"}
                value={(account ?? {}).email || ""}
                placeholder={"Email"}
              />
            </Form.Group>
            <Form.Group>
              <Form.Label>Valuation currency</Form.Label>
              <Form.Control
                disabled={true}
                value={valuationCurrency}
                as="select"
              >
                <option value={valuationCurrency}>{valuationCurrency}</option>
              </Form.Control>
            </Form.Group>
            <LoadingButton loading={false} variant="dark">
              Save
            </LoadingButton>
          </Form>
        </Col>
      </Row>
    </>
  );
};
