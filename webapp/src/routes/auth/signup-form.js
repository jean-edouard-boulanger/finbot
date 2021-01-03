import React, {useContext} from "react";

import AuthContext from "context/auth/auth-context";

import StyledAuthContainer from "./styled";

import Form from "react-jsonschema-form";
import Button from "react-bootstrap/Button";


const schema = {
  "title": "SIGN UP",
  "type": "object",
  "required": [
    "full_name",
    "password",
    "settings",
    "email"
  ],
  "properties": {
    "full_name": {
      "type": "string",
      "title": "Name",
      minLength: 4
    },
    "email": {
      "type": "string",
      "title": "E-Mail",
      "format": "email"
    },
    "settings": {
      "type": "string",
      "title": "Settings",
      "enum": [
        "EUR",
        "GBP",
        "AUD",
        "USD",
        "CAD",
        "JPY",
        "CNY",
        "INR",
        "CHF"
      ]
    },
    "password": {
      "type": "string",
      "title": "Password",
      "minLength": 7
    }
  }
}

const uiSchema = {
  "full_name": {
    "ui:autofocus": true,
    "ui:emptyValue": "",
    "ui:placeholder": "John Doe"
  },
  "email": {
    "ui:emptyValue": ""
  },
  "password": {
    "ui:widget": "password",
    "ui:help": "Hint: Make it strong!"
  },
  "settings": {
    "ui:placeholder": "Choose currency",
  }
}

const SignupForm = props => {
  const authContext = useContext(AuthContext);

  return (
    <StyledAuthContainer>
      <Form
        className="border border-secondary p-4 text-center opaque-background sign-form"
        schema={schema}
        uiSchema={uiSchema}
        onSubmit={(data) => {
          authContext.register(data.formData)
        }}
        showErrorList={false}>
        <div className="d-flex flex-column align-items-center">
          <Button className="bg-dark col-md-6 m-1" type="submit">Submit</Button>
          <Button className="bg-dark col-md-6 m-1" type="button">Log In</Button>
        </div>
      </Form>
    </StyledAuthContainer>
  )
}

export default SignupForm;