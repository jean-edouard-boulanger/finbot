import React, { useContext, useState } from "react";
import { Link } from "react-router-dom";

import { Credentials } from "clients/finbot-client/types";
import { AuthContext } from "contexts";

import { toast } from "react-toastify";
import { LoadingButton } from "components";
import { Row, Col, Button } from "react-bootstrap";

import {
  default as DataDrivenForm,
  UiSchema,
  ISubmitEvent,
} from "react-jsonschema-form";
import { JSONSchema6 } from "json-schema";

const LOGIN_DATA_SCHEMA: JSONSchema6 = {
  type: "object",
  required: ["password", "email"],
  properties: {
    email: {
      type: "string",
      title: "E-Mail",
      format: "email",
    },
    password: {
      type: "string",
      title: "Password",
    },
  },
};

const LOGIN_UI_SCHEMA: UiSchema = {
  email: {
    "ui:emptyValue": "",
    "ui:autofocus": true,
  },
  password: {
    "ui:widget": "password",
  },
};

export interface LoginFormProps {}

export const LoginForm: React.FC<LoginFormProps> = () => {
  const { login } = useContext(AuthContext);
  const [loading] = useState(false);

  const handleLogin = async (event: ISubmitEvent<Credentials>) => {
    try {
      await login!(event.formData);
    } catch (e) {
      toast.error(`${e}`);
    }
  };

  return (
    <>
      <Row>
        <Col md={12}>
          <Row>
            <Col>
              <div className={"page-header"}>
                <h1>
                  Sign in <small>to my finbot account</small>
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
                schema={LOGIN_DATA_SCHEMA}
                uiSchema={LOGIN_UI_SCHEMA}
                onSubmit={handleLogin}
                showErrorList={false}
              >
                <div>
                  <LoadingButton
                    variant={"dark"}
                    type="submit"
                    loading={loading}
                  >
                    Sign In
                  </LoadingButton>{" "}
                  <Link to={"/signup"}>
                    <Button variant={"dark"}>Sign up</Button>
                  </Link>
                </div>
              </DataDrivenForm>
            </Col>
          </Row>
        </Col>
      </Row>
    </>
  );
};

export default LoginForm;
