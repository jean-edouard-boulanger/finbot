import React, { useContext, useState } from "react";
import { Redirect } from "react-router-dom";

import { ServicesContext } from "contexts";

import { toast } from "react-toastify";
import { LoadingButton } from "components";
import { default as DataDrivenForm } from "react-jsonschema-form";
import { Row, Col } from "react-bootstrap";

const SIGNUP_DATA_SCHEMA = {
  type: "object",
  required: ["full_name", "password", "valuation_ccy", "email"],
  properties: {
    full_name: {
      type: "string",
      title: "Name",
      minLength: 4,
    },
    email: {
      type: "string",
      title: "E-Mail",
      format: "email",
    },
    valuation_ccy: {
      type: "string",
      title: "Valuation currency",
      enum: ["EUR", "GBP", "AUD", "USD", "CAD", "JPY", "CNY", "INR", "CHF"],
    },
    password: {
      type: "string",
      title: "Password",
      minLength: 7,
    },
  },
};

const SIGNUP_UI_SCHEMA = {
  full_name: {
    "ui:autofocus": true,
    "ui:emptyValue": "",
    "ui:placeholder": "John Doe",
  },
  email: {
    "ui:emptyValue": "",
  },
  password: {
    "ui:widget": "password",
  },
};

export const SignupForm = () => {
  const { finbotClient } = useContext(ServicesContext);
  const [loading, setLoading] = useState(false);
  const [registered, setRegistered] = useState(false);

  const handleSignup = async (data) => {
    try {
      setLoading(true);
      await finbotClient.registerAccount(data.formData);
      setLoading(false);
      setRegistered(true);
    } catch (e) {
      setLoading(false);
      toast.error(e);
    }
  };

  if (registered) {
    return <Redirect to={"/login"} />;
  }

  return (
    <>
      <Row>
        <Col md={12}>
          <Row>
            <Col>
              <div className={"page-header"}>
                <h1>
                  Register <small>a new finbot account</small>
                </h1>
              </div>
            </Col>
          </Row>
        </Col>
      </Row>
      <Row>
        <Col md={6}>
          <Row>
            <Col>
              <DataDrivenForm
                schema={SIGNUP_DATA_SCHEMA}
                uiSchema={SIGNUP_UI_SCHEMA}
                onSubmit={handleSignup}
                showErrorList={false}
              >
                <LoadingButton variant={"dark"} type="submit" loading={loading}>
                  Sign up
                </LoadingButton>
              </DataDrivenForm>
            </Col>
          </Row>
        </Col>
      </Row>
    </>
  );
};
