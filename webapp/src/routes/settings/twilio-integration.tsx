import React, { useState, useEffect, useContext } from "react";

import { AuthContext, ServicesContext } from "contexts";
import { LoadingButton, ToggleSecret } from "components";
import { TwilioSettings } from "clients/finbot-client/types";

import { Formik, Form as MetaForm, Field, ErrorMessage } from "formik";
import { Col, Row, Form, Alert } from "react-bootstrap";
import { toast } from "react-toastify";

import * as Yup from "yup";

const SETTINGS_SCHEMA = Yup.object().shape({
  account_sid: Yup.string().required().label("Account SID"),
  auth_token: Yup.string().required().label("Auth token"),
  phone_number: Yup.string().required().label("Phone number"),
});

const makeTwilioSettings = (settings?: TwilioSettings | null) => {
  return {
    account_sid: settings?.account_sid ?? "",
    auth_token: settings?.auth_token ?? "",
    phone_number: settings?.phone_number ?? "",
  };
};

export const TwilioIntegrationSettings: React.FC<
  Record<string, never>
> = () => {
  const { account } = useContext(AuthContext);
  const { finbotClient } = useContext(ServicesContext);

  const [enableTwilio, setEnableTwilio] = useState(false);
  const [twilioSettings, setTwilioSettings] = useState<TwilioSettings>(
    makeTwilioSettings()
  );

  useEffect(() => {
    const fetch = async () => {
      const settings = await finbotClient!.getAccountSettings({
        account_id: account!.id,
      });
      const twilioSettings = settings.twilio_settings;
      setEnableTwilio(twilioSettings !== null);
      setTwilioSettings(makeTwilioSettings(twilioSettings));
    };
    fetch();
  }, [account, finbotClient]);

  const handleSubmit = async (
    values: TwilioSettings,
    { setSubmitting }: { setSubmitting: (submitting: boolean) => void }
  ) => {
    try {
      const newSettings = enableTwilio ? values : null;
      await finbotClient!.updateTwilioAccountSettings({
        account_id: account!.id,
        twilio_settings: newSettings,
      });
      setSubmitting(false);
      toast.success("Twilio settings updated");
    } catch (e) {
      toast.error(`Failed to update Twilio settings: ${e}`);
    }
  };

  return (
    <>
      <Row className={"mb-4"}>
        <Col>
          <h3>Twilio integration</h3>
        </Col>
      </Row>
      <Row>
        <Col>
          <Alert variant={"info"}>
            Integrating with{" "}
            <a
              href={"https://www.twilio.com/"}
              target={"_blank"}
              rel={"noreferrer"}
            >
              Twilio
            </a>{" "}
            allows Finbot to send notifications over text messages.
          </Alert>
        </Col>
      </Row>
      <Row>
        <Col>
          <Formik
            enableReinitialize
            validationSchema={enableTwilio ? SETTINGS_SCHEMA : null}
            initialValues={twilioSettings}
            onSubmit={handleSubmit}
          >
            {({ isSubmitting, submitForm }) => (
              <MetaForm>
                <Form.Group>
                  <Form.Check
                    checked={enableTwilio}
                    onChange={(event) => {
                      setTwilioSettings(makeTwilioSettings(twilioSettings));
                      setEnableTwilio(event.target.checked);
                    }}
                    type="checkbox"
                    label="Enable Twilio integration"
                  />
                </Form.Group>
                <Form.Group>
                  <Form.Label>Account SID</Form.Label>
                  <Field
                    disabled={!enableTwilio}
                    type="text"
                    name="account_sid"
                    className="form-control"
                  />
                  <ErrorMessage
                    className="text-danger"
                    name="account_sid"
                    component="div"
                  />
                </Form.Group>
                <Form.Group>
                  <Form.Label>Auth token</Form.Label>
                  <ToggleSecret
                    renderAs={Field}
                    disabled={!enableTwilio}
                    name="auth_token"
                    className="form-control"
                  />
                  <ErrorMessage
                    className="text-danger"
                    name="auth_token"
                    component="div"
                  />
                </Form.Group>
                <Form.Group>
                  <Form.Label>
                    Phone number (sender) or friendly name
                  </Form.Label>
                  <Field
                    disabled={!enableTwilio}
                    type="text"
                    name="phone_number"
                    className="form-control"
                  />
                  <ErrorMessage
                    className="text-danger"
                    name="phone_number"
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
