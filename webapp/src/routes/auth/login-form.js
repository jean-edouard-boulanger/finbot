import React, {useContext} from "react";

import AuthContext from "context/auth/auth-context";

import StyledAuthContainer from "./styled";
import Form from "react-jsonschema-form";
import {Button} from "react-bootstrap";


const schema = {
  "title": "LOG IN",
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

const uiSchema = {
  "email": {
    "ui:emptyValue": "",
    "ui:autofocus": true,
  },
  "password": {
    "ui:widget": "password",
  }
}

const LoginForm = () => {
  const authContext = useContext(AuthContext)

  return (
    <StyledAuthContainer>
      <Form
        className="border border-secondary p-4 text-center opaque-background sign-form"
        schema={schema}
        uiSchema={uiSchema}
        onSubmit={(data) => {
          authContext.login(data.formData);
        }}
        showErrorList={false}>
        <div>
          <Button className="bg-dark col-md-6" type="submit">Log In</Button>
        </div>
      </Form>
    </StyledAuthContainer>
  )
}

export default LoginForm;
