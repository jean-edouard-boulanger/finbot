import React, {useState, useEffect, useContext} from "react";

import { AuthContext, ServicesContext } from "contexts";

import { LoadingButton } from "components";
import { Col, Row, Form } from "react-bootstrap";


export const PlaidIntegrationSettings = () => {
  const {account} = useContext(AuthContext);
  const {finbotClient} = useContext(ServicesContext);

  const [plaidSettings, setPlaidSettings] = useState(null);

  useEffect(() => {
    const fetch = async () => {
      const settings = await finbotClient.getAccountSettings({
        account_id: account.id
      });
      resetPlaidSettings(settings.plaid_settings);
    }
    fetch();
  }, [account, finbotClient]);

  const resetPlaidSettings = ({env, client_id, public_key, secret_key}) => {
    setPlaidSettings({
      env: env || "production",
      client_id: client_id || null,
      public_key: public_key || null,
      secret_key: secret_key || null
    });
  }

  const handleChange = (field, value) => {
    if(plaidSettings !== null) {
      const newSettings = {
        ...plaidSettings,
        [field]: value
      };
      console.log(newSettings);
      setPlaidSettings(newSettings);
    }
  }

  return (
    <>
      <Row className={"mb-4"}>
        <Col>
          <h3>
            Plaid integration
          </h3>
        </Col>
      </Row>
      <Row>
        <Col>
          <Form>
            <Form.Group>
              <Form.Check
                checked={plaidSettings !== null}
                onChange={(event) => {
                  if(event.target.checked) {
                    return setPlaidSettings({});
                  }
                  resetPlaidSettings({});
                }}
                type="checkbox"
                label="Enable Plaid integration" />
            </Form.Group>
            <Form.Group>
              <Form.Label>Environment</Form.Label>
              <Form.Control
                onChange={(event) => {handleChange("env", event.target.value)}}
                disabled={plaidSettings === null}
                value={(plaidSettings ?? {}).env || "production"}
                as="select">
                <option value={"sandbox"}>Sandbox</option>
                <option value={"development"}>Development</option>
                <option value={"production"}>Production</option>
              </Form.Control>
            </Form.Group>
            <Form.Group>
              <Form.Label>Client identifier</Form.Label>
              <Form.Control
                type="text"
                disabled={plaidSettings === null}
                value={(plaidSettings ?? {}).client_id || ""}
                onChange={(event) => handleChange("client_id", event.target.value)}
                placeholder="client_id Plaid API key" />
            </Form.Group>
            <Form.Group>
              <Form.Label>Public key</Form.Label>
              <Form.Control
                type="text"
                disabled={plaidSettings === null}
                onChange={(event) => handleChange("public_key", event.target.value)}
                value={(plaidSettings ?? {}).public_key || ""}
                placeholder="public_key Plaid API key" />
            </Form.Group>
            <Form.Group>
              <Form.Label>Secret key</Form.Label>
              <Form.Control
                type="text"
                disabled={plaidSettings === null}
                onChange={(event) => handleChange("secret_key", event.target.value)}
                value={(plaidSettings ?? {}).secret_key || ""}
                placeholder="secret Plaid API key" />
            </Form.Group>
            <LoadingButton
              size={"sm"}
              loading={false}
              variant="dark">
              Save
            </LoadingButton>
          </Form>
        </Col>
      </Row>
    </>
  )
};
