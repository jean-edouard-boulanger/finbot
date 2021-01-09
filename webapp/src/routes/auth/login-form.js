import React, {useContext, useState} from "react";
import { Link } from "react-router-dom";

import { AuthContext } from "contexts";

import { toast } from "react-toastify";
import { LoadingButton } from "components";
import { Row, Col, Button } from "react-bootstrap";

import { default as DataDrivenForm } from "react-jsonschema-form";


const LOGIN_DATA_SCHEMA = {
  "type": "object",
  "required": [
    "password",
    "email"
  ],
  "properties": {
    "email": {
      "type": "string",
      "title": "E-Mail",
      "format": "email"
    },
    "password": {
      "type": "string",
      "title": "Password",
    }
  }
}

const LOGIN_UI_SCHEMA = {
  "email": {
    "ui:emptyValue": "",
    "ui:autofocus": true,
  },
  "password": {
    "ui:widget": "password",
  }
}

export const LoginForm = () => {
  const {login} = useContext(AuthContext)
  const [loading] = useState(false);

  const handleLogin = async (data) => {
    try {
      await login(data.formData);
    }
    catch(e) {
      toast.error(e);
    }
  }

  return (
    <Row>
      <Col md={6}>
        <Row>
          <Col>
            <h2>Sign in</h2>
          </Col>
        </Row>
        <Row>
          <Col>
            <DataDrivenForm
              schema={LOGIN_DATA_SCHEMA}
              uiSchema={LOGIN_UI_SCHEMA}
              onSubmit={handleLogin}
              showErrorList={false} >
              <div>
                <LoadingButton
                  variant={"dark"}
                  type="submit"
                  loading={loading} >
                  Sign In
                </LoadingButton>
                {" "}
                <Link to={"/signup"}>
                  <Button variant={"dark"}>
                    Sign up
                  </Button>
                </Link>
              </div>
            </DataDrivenForm>
          </Col>
        </Row>
      </Col>
    </Row>
  )
}

export default LoginForm;
