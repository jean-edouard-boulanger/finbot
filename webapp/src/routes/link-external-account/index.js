import React, {useEffect, useState, useContext} from "react";
import { Redirect } from "react-router-dom";

import { AuthContext, ServicesContext } from "contexts";

import {default as DataDrivenForm} from "react-jsonschema-form";
import { toast } from "react-toastify";
import { LoadingButton } from "components";
import { Row, Col, Form, Button, Alert } from "react-bootstrap";
import { PlaidLink } from 'react-plaid-link';

const NO_PROVIDER_SELECTED = "NO_PROVIDER_SELECTED";
const PLAID_PROVIDER_ID = "plaid_us"


const DataDrivenAccountForm = ({operation, schema, onSubmit}) => {
  return (
    <DataDrivenForm
      schema={schema.json_schema ?? {}}
      uiSchema={schema.ui_schema ?? {}}
      onSubmit={(data) => {
        onSubmit(data.formData || {})
      }}
      showErrorList={false}>
      <LoadingButton loading={operation !== null} variant={"dark"} type="submit">
        {operation || "Link account"}
      </LoadingButton>
    </DataDrivenForm>
  );
}

const PlaidForm = ({operation, settings, onSubmit}) => {
  if(operation !== null) {
    return (
      <LoadingButton variant={"dark"} loading={true}>
        {operation}
      </LoadingButton>
    )
  }

  return (
    <PlaidLink
      clientName="Finbot"
      onSuccess={(public_token) => {
        onSubmit({public_token});
      }}
      publicKey={settings.public_key}
      env={settings.env}
      countryCodes={["GB", "US", "CA", "IE", "FR", "ES", "NL"]}
      product={["transactions", "identity"]}
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

export const LinkAccount = (props) => {
  const {account} = useContext(AuthContext);
  const {finbotClient} = useContext(ServicesContext);

  const [providers, setProviders] = useState([]);
  const [settings, setSettings] = useState(null);
  const [selectedProvider, setSelectedProvider] = useState(null);
  const [accountName, setAccountName] = useState(null);
  const [operation, setOperation] = useState(null);
  const [linked, setLinked] = useState(false);

  useEffect(() => {
    const fetch = async () => {
      const providersPayload = await finbotClient.getProviders();
      setProviders(providersPayload.sort((p1, p2) => {
        return p1.description.localeCompare(p2.description);
      }));
    };
    fetch();
  }, [finbotClient]);

  useEffect(() => {
    const fetch = async () => {
      setSettings(await finbotClient.getAccountSettings({
        account_id: account.id
      }))
    }
    fetch();
  }, [finbotClient, account])

  const onSelectedProviderChanged = (event) => {
    const providerId = event.target.value;
    if (providerId === NO_PROVIDER_SELECTED) {
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

    setOperation("Validating credentials");

    try {
      const validated = await finbotClient.validateExternalAccountCredentials(
        account.id, link_settings);
      if (!validated) {
        toast.error(`Could not validate credentials: unknown error`)
        setOperation(null);
        return;
      }
    }
    catch(e) {
      toast.error(`${e}`)
      setOperation(null);
      return;
    }
    setOperation("Linking account");
    try {
      const results = await finbotClient.linkAccount(account.id, link_settings);
      if (!results.persisted) {
        toast.error(`Could not link account: unknown error`)
        setOperation(null);
        return;
      }
    }
    catch (e) {
      toast.error(`${e}`);
      setOperation(null);
      return;
    }
    setLinked(true);
  }

  if(linked) {
    return <Redirect to={"/dashboard"}  />
  }

  return (
    <>
      <Row className={"mb-4"}>
        <Col>
          <div className={"page-header"}>
            <h1>Link <small>a new external account</small></h1>
          </div>
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
            <>
              <Row className={"mb-4"}>
                <Col>
                  <h3>2. Account name</h3>
                </Col>
              </Row>
              <Row>
                <Col>
                  <Form.Group controlId="formBasicEmail">
                    <Form.Control
                      type="email"
                      placeholder="Account name"
                      value={accountName}
                      onChange={(event) => {
                        setAccountName(event.target.value);
                      }}/>
                  </Form.Group>
                </Col>
              </Row>
            </>
          }
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
                <DataDrivenAccountForm
                  operation={operation}
                  schema={selectedProvider.credentials_schema}
                  onSubmit={(credentials) => {
                    requestLinkAccount({...selectedProvider}, credentials)
                  }}/>
              }
              {
                (isPlaidSelected(selectedProvider) && isPlaidSupported(settings)) &&
                <PlaidForm
                  operation={operation}
                  settings={settings.plaid_settings}
                  onSubmit={(credentials) => {
                    requestLinkAccount({...selectedProvider}, credentials)
                  }}/>
              }
              {
                (isPlaidSelected(selectedProvider) && !isPlaidSupported(settings)) &&
                <Alert variant={"warning"}>To link an external account via Plaid (open banking), please first provide
                  your Plaid API details in your account settings.</Alert>
              }
            </Col>
          </Row>
        </Col>
        <Col md={1}>
        </Col>
      </Row>
    </>
  )
}

export default LinkAccount;
