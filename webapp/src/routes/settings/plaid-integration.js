import React, { useState, useEffect, useContext } from "react";

import { AuthContext, ServicesContext } from "contexts";

import { Formik, Form as MetaForm, Field, ErrorMessage } from "formik";
import { LoadingButton, ToggleSecret } from "components";
import { Col, Row, Form } from "react-bootstrap";
import { toast } from "react-toastify";

import * as Yup from "yup";

const PLAID_ENVIRONMENTS = ["sandbox", "development", "production"];

const SETTINGS_SCHEMA = Yup.object().shape({
  env: Yup.string()
    .oneOf(PLAID_ENVIRONMENTS)
    .required()
    .label("Plaid environment"),
  client_id: Yup.string().required().min(1).label("Client identifier"),
  public_key: Yup.string().required().min(1).label("Public key"),
  secret_key: Yup.string().required().min(1).label("Secret key"),
});

const makePlaidSettings = (settings) => {
  settings = settings ?? {};
  return {
    env: settings.env ?? PLAID_ENVIRONMENTS[PLAID_ENVIRONMENTS.length - 1],
    client_id: settings.client_id ?? "",
    public_key: settings.public_key ?? "",
    secret_key: settings.secret_key ?? "",
  };
};

export const PlaidIntegrationSettings = () => {
  const { account } = useContext(AuthContext);
  const { finbotClient } = useContext(ServicesContext);

  const [enablePlaid, setEnablePlaid] = useState(false);
  const [plaidSettings, setPlaidSettings] = useState(null);

  useEffect(() => {
    const fetch = async () => {
      const plaidSettings = await finbotClient.getAccountPlaidSettings({
        account_id: account.id,
      });
      setEnablePlaid(plaidSettings !== null);
      setPlaidSettings(makePlaidSettings(plaidSettings));
    };
    fetch();
  }, [account, finbotClient]);

  const handleSubmit = async (values, { setSubmitting }) => {
    try {
      if (enablePlaid) {
        const newSettings = await finbotClient.updateAccountPlaidSettings({
          account_id: account.id,
          env: values.env,
          client_id: values.client_id,
          public_key: values.public_key,
          secret_key: values.secret_key,
        });
        setPlaidSettings(makePlaidSettings(newSettings));
      } else {
        await finbotClient.deleteAccountPlaidSettings({
          account_id: account.id,
        });
        setPlaidSettings(makePlaidSettings());
      }
      toast.success("Plaid settings updated");
    } catch (e) {
      toast.error(`Failed to update Plaid settings: ${e}`);
    }
    setSubmitting(false);
  };

  return (
    <>
      <Row className={"mb-4"}>
        <Col>
          <h3>Plaid integration</h3>
        </Col>
      </Row>
      <Row>
        <Col>
          <Formik
            enableReinitialize
            validationSchema={enablePlaid ? SETTINGS_SCHEMA : null}
            initialValues={plaidSettings}
            onSubmit={handleSubmit}
          >
            {({ isSubmitting, submitForm }) => (
              <MetaForm>
                <Form.Group>
                  <Form.Check
                    checked={enablePlaid}
                    onChange={(event) => {
                      setPlaidSettings(makePlaidSettings(plaidSettings));
                      setEnablePlaid(event.target.checked);
                    }}
                    type="checkbox"
                    label="Enable Plaid integration"
                  />
                </Form.Group>
                <Form.Group>
                  <Form.Label>Environment</Form.Label>
                  <Field
                    disabled={!enablePlaid}
                    type="text"
                    name="env"
                    as="select"
                    className="form-control"
                  >
                    <option value={"sandbox"}>Sandbox</option>
                    <option value={"development"}>Development</option>
                    <option value={"production"}>Production</option>
                  </Field>
                  <ErrorMessage
                    className="text-danger"
                    name="env"
                    component="div"
                  />
                </Form.Group>
                <Form.Group>
                  <Form.Label>Client identifier</Form.Label>
                  <ToggleSecret
                    renderAs={Field}
                    disabled={!enablePlaid}
                    name="client_id"
                    className="form-control"
                  />
                  <ErrorMessage
                    className="text-danger"
                    name="client_id"
                    component="div"
                  />
                </Form.Group>
                <Form.Group>
                  <Form.Label>Public key</Form.Label>
                  <ToggleSecret
                    renderAs={Field}
                    disabled={!enablePlaid}
                    name="public_key"
                    className="form-control"
                  />
                  <ErrorMessage
                    className="text-danger"
                    name="public_key"
                    component="div"
                  />
                </Form.Group>
                <Form.Group>
                  <Form.Label>Secret key</Form.Label>
                  <ToggleSecret
                    renderAs={Field}
                    disabled={!enablePlaid}
                    name="secret_key"
                    className="form-control"
                  />
                  <ErrorMessage
                    className="text-danger"
                    name="secret_key"
                    component="div"
                  />
                </Form.Group>
                <LoadingButton
                  size={"sm"}
                  onClick={submitForm}
                  loading={isSubmitting}
                  variant="dark"
                >
                  Save
                </LoadingButton>
              </MetaForm>
            )}
          </Formik>
        </Col>
      </Row>
    </>
  );
};
