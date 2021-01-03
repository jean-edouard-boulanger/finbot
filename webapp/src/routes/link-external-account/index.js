import React, {useEffect, useState, useContext} from "react";
import {withRouter} from "react-router";
import { default as DataDrivenForm } from "react-jsonschema-form";

import FinbotClient from "clients/finbot-client";

import AuthContext from "context/auth/auth-context";

import {Row, Col, Form, Button, Alert} from "react-bootstrap";
import { PlaidLink } from 'react-plaid-link';

const NO_PROVIDER_SELECTED = "NO_PROVIDER_SELECTED";
const PLAID_PROVIDER_ID = "plaid_us"


const StandardAccountForm = ({schema, onSubmit}) => {
  return (
    <DataDrivenForm
      schema={schema.json_schema ?? {}}
      uiSchema={schema.ui_schema ?? {}}
      onSubmit={(data) => { onSubmit(data.formData || {}) }}
      showErrorList={false} >
      <div>
        <Button className="bg-dark" type="submit">Link Account</Button>
      </div>
    </DataDrivenForm>
  );
}

const PlaidForm = ({settings, onSubmit}) => {
  return (
    <PlaidLink
      clientName="Finbot"
      onSuccess={(public_token) => {
        onSubmit({public_token});
      }}
      publicKey={settings.public_key}
      env={settings.env}
      product={["auth", "transactions", "identity"]}
    >
      Link Account via Plaid
    </PlaidLink>
  )
}

const isPlaidSelected = (selectedProvider) => {
  return selectedProvider !== null && selectedProvider.id === PLAID_PROVIDER_ID;
}

const isPlaidSupported = (settings) => {
  return settings !== null && settings.plaid_settings !== null;
}

const LinkAccount = (props) => {
  const authContext = useContext(AuthContext);
  const accountID = authContext.accountID

  const [client] = useState(() => new FinbotClient());
  const [providers, setProviders] = useState([]);
  const [settings, setSettings] = useState(null);
  const [selectedProvider, setSelectedProvider] = useState(null);
  const [accountName, setAccountName] = useState(null);

  useEffect(() => {
    if(client === null) { return; }
    const fetch = async () => {
      const providersPayload = await client.getProviders();
      setProviders(providersPayload.sort((p1, p2) => {
        return p1.description.localeCompare(p2.description);
      }));
    };
    fetch();
  }, [client]);

  useEffect(() => {
    if(client === null) { return; }
    const fetch = async () => {
      setSettings(await client.getAccountSettings({account_id: accountID}))
    }
    fetch();
  }, [client, accountID])

  const onSelectedProviderChanged = (event) => {
    const providerId = event.target.value;
    if(providerId === NO_PROVIDER_SELECTED) {
      setSelectedProvider(null);
      return;
    }
    const provider = providers.find((provider) => {
      return provider.id === providerId;
    });
    setAccountName(provider.description);
    setSelectedProvider(provider);
  }

  const requestLinkAccount = async (provider, credentials) => {
    const link_settings = {
      provider_id: provider.id,
      account_name: (accountName || provider.description),
      credentials
    };
    const validated = await client.validateExternalAccountCredentials(link_settings);
    if(!validated) {
      return;
    }
    const results = await client.linkAccount(link_settings);
    if(!results.persisted) {

    }
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
            (selectedProvider !== null && !isPlaidSelected(selectedProvider)) &&
              <Row className={"mb-4"}>
                <Col><h3>3. Account settings</h3></Col>
              </Row>
          }
          <Row>
            <Col>
            {
              (selectedProvider !== null && !isPlaidSelected(selectedProvider)) &&
                <StandardAccountForm
                  schema={selectedProvider.credentials_schema}
                  onSubmit={(credentials) => {
                    console.log(credentials);
                    requestLinkAccount({...selectedProvider}, credentials)
                  }} />
            }
            {
              (isPlaidSelected(selectedProvider) && isPlaidSupported(settings)) &&
                <PlaidForm
                  settings={settings.plaid_settings}
                  onSubmit={(credentials) => {
                    requestLinkAccount({...selectedProvider}, credentials)
                  }} />
            }
            {
              (isPlaidSelected(selectedProvider) && !isPlaidSupported(settings)) &&
                <Alert variant={"warning"}>To link an external account via Plaid (open banking), please first provide your Plaid API details in your account settings.</Alert>
            }
            </Col>
          </Row>
        </Col>
        {
          (selectedProvider !== null) &&
            <Col md={6}>
              <Row className={"mb-4"}>
                <Col>
                  <h3>2. Account name</h3>
                </Col>
              </Row>
              <Row>
                <Form.Group controlId="formBasicEmail">
                  <Form.Control
                    type="email"
                    placeholder="Account name"
                    value={accountName}
                    onChange={(event) => { setAccountName(event.target.value); }} />
                  <Form.Text className="text-muted">
                    The chosen account name will appear on the finbot report, it needs to be unique per provider.
                  </Form.Text>
                </Form.Group>
              </Row>
            </Col>
        }
      </Row>
    </>
  )
}

export default withRouter(LinkAccount);
