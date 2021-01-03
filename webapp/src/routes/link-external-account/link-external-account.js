import React, { useContext } from "react";

import Form from "react-jsonschema-form";
import {Button, Row, Col} from "react-bootstrap";
import ProvidersContext from "../../context/linked-account-context";
import SpinnerButton from "./spinner-button"

const LinkExternalAccount = () => {

    const providersContext = useContext(ProvidersContext);
    const { schema, _validateCredentials, loading } = providersContext;

    if(schema == null) {
      return (
        <Row>
          <Col>
            Select a provider in the dropdown
          </Col>
        </Row>
      )
    }

    return (
      <Row>
        <Col md={12}>
          <Form
              className="border border-secondary p-4 sign-form"
              schema={schema.json_schema || {}}
              uiSchema={schema.ui_schema || {}}
              onSubmit={_validateCredentials}
              showErrorList={false} >
              <div>
                  {loading.current ? <SpinnerButton message={loading.message} /> : <Button className="bg-dark" type="submit">Link Account</Button>}
              </div>
          </Form>
        </Col>
      </Row>
    )
}

export default LinkExternalAccount;