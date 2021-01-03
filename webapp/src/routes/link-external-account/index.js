import React, {useEffect, useState} from "react";
import {withRouter} from "react-router";
import { default as DataDrivenForm } from "react-jsonschema-form";

import FinbotClient from "clients/finbot-client";

import {Row, Col, Form, Button} from "react-bootstrap";
import { PlaidLink } from 'react-plaid-link';

const NO_PROVIDER_SELECTED = "NO_PROVIDER_SELECTED";


const StandardAccountForm = ({schema}) => {
  console.log(schema);
  return (
    <DataDrivenForm
      schema={schema.json_schema ?? {}}
      uiSchema={schema.ui_schema ?? {}}
      onSubmit={() => {}}
      showErrorList={false} >
      <div>
        <Button className="bg-dark" type="submit">Link Account via Plaid</Button>
      </div>
    </DataDrivenForm>
  );
}

const PlaidForm = ({}) => {
  return (
    <PlaidLink
      clientName="Finbot"
      onSuccess={(token, payload) => { console.log("plaid onSuccess", token, payload) }}
      onExit={(val1, payload) => { console.log("plaid onExit", val1, payload) }}
      onLoad={(payload) => { console.log("plaid onLoad", payload) }}
      onEvent={(eventType, payload) => { console.log("plaid onEvent", eventType, payload) }}
      publicKey="e703d72b6d5d1399373fac7f779de0"
      env="sandbox"
      product={["auth", "assets"]}
    >
      Link Account
    </PlaidLink>
  )
}

const LinkAccount = (props) => {
  const [client] = useState(() => new FinbotClient());
  const [providers, setProviders] = useState([]);
  const [selectedProvider, setSelectedProvider] = useState(null);

  useEffect(() => {
    const fetch = async () => {
      let providersPayload = await client.getProviders();
      providersPayload.push({
        id: "plaid_us",
        description: "Open banking via Plaid"
      });
      setProviders(providersPayload.sort((p1, p2) => {
        return p1.description.localeCompare(p2.description);
      }));
    };
    if(client !== null) {
      fetch();
    }
  }, [client]);

  const onSelectedProviderChanged = (event) => {
    const providerId = event.target.value;
    if(providerId === NO_PROVIDER_SELECTED) {
      setSelectedProvider(null);
      return;
    }
    setSelectedProvider(providers.find((provider) => {
      return provider.id === providerId;
    }));
  }

  return (
    <>
      <Row className={"mb-4"}>
        <Col>
          <h2>Link a new account</h2>
        </Col>
      </Row>
      <Row>
        <Col md={6}>
          <Row className={"mb-4"}>
            <Col>
              <h3>1. Provider selection</h3>
            </Col>
          </Row>
          <Row className={"mb-4"}>
            <Col>
              <Form.Group>
                <Form.Control
                  value={(selectedProvider ?? {id: NO_PROVIDER_SELECTED}).id}
                  as="select"
                  size="md"
                  onChange={onSelectedProviderChanged}>
                  <option value={NO_PROVIDER_SELECTED}>Select a provider</option>
                  {
                    providers.map((provider) => {
                      return (
                        <option value={provider.id}>
                          {provider.description}
                        </option>
                      )
                    })
                  }
                </Form.Control>
              </Form.Group>
            </Col>
          </Row>
          {
            (selectedProvider !== null) &&
              <Row>
                <Col><h3>3. Account credentials</h3></Col>
              </Row>
          }
          <Row>
            <Col>
            {
              (selectedProvider !== null && selectedProvider.id !== "plaid_us") &&
                <StandardAccountForm schema={selectedProvider.credentials_schema} />
            }
            {
              (selectedProvider !== null && selectedProvider.id === "plaid_us") &&
                <PlaidForm />
            }
            </Col>
          </Row>
        </Col>
        <Col md={6}>
          <Row className={"mb-4"}>
            <Col>
              <h3>2. Account name</h3>
            </Col>
          </Row>
          <Row>
            <Form.Group controlId="formBasicEmail">
              <Form.Control type="email" placeholder="Account name" defaultValue={(selectedProvider ?? {description: ""}).description} />
              <Form.Text className="text-muted">
                The chosen account name will appear on the finbot report
              </Form.Text>
            </Form.Group>
          </Row>
        </Col>
      </Row>
    </>
  )
}

export default withRouter(LinkAccount);
