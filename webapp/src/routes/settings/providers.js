import React, { useContext, useState, useEffect, useRef } from "react";

import AceEditor from "react-ace";
import { default as DataDrivenForm } from "react-jsonschema-form";
import { Alert, Row, Col, Button, Tabs, Tab, Form } from "react-bootstrap";
import { ServicesContext, AuthContext } from "contexts";
import { LoadingButton } from "components";
import { Formik, Form as MetaForm, Field, ErrorMessage } from "formik";
import { ProviderSelector } from "./components";
import { toast } from "react-toastify";

import * as Yup from "yup";

import "ace-builds/src-noconflict/theme-github";
import "ace-builds/src-noconflict/mode-json";

const DEFAULT_CREDENTIALS_SCHEMA = {
  json_schema: {
    $schema: "http://json-schema.org/draft-07/schema#",
    properties: {
      password: {
        title: "Password",
        type: "string",
      },
      username: {
        title: "Username",
        type: "string",
      },
    },
    required: ["username", "password"],
    type: "object",
  },
  ui_schema: {
    password: {
      "ui:widget": "password",
    },
    "ui:order": ["username", "password"],
  },
};

const PROVIDER_SCHEMA = Yup.object().shape({
  id: Yup.string()
    .required("Identifier is required")
    .matches(
      /^[a-z][a-zA-Z0-9_]+$/,
      "Provider identifier must start with a letter, and only contain letters, numbers or the underscore '_' character"
    )
    .min(4)
    .max(64),
  description: Yup.string()
    .required("Description is required")
    .max(256, "Description should be at most 64 characters"),
  website_url: Yup.string().required("Website is required").max(256),
});

const useSchema = (rawSchema) => {
  try {
    const schema = JSON.parse(rawSchema);
    return [schema, null];
  } catch (e) {
    return [null, e.toString()];
  }
};

export const EditProviderPanel = () => {
  const { finbotClient } = useContext(ServicesContext);
  const { account } = useContext(AuthContext);
  const [selectedProviderId, setSelectedProviderId] = useState(null);
  const [providerDescription, setProviderDescription] = useState(null);
  const [rawSchema, setRawSchema] = useState(() => {
    return JSON.stringify(DEFAULT_CREDENTIALS_SCHEMA, null, 2);
  });
  const [schema, schemaError] = useSchema(rawSchema);
  const editorRef = useRef();

  const handleSubmit = async (values, { setSubmitting }) => {
    let editor = editorRef.current.editor;
    let schema = null;
    try {
      schema = JSON.parse(editor.getValue());
    } catch (e) {
      toast.error(
        "Could not save provider: invalid credentials schema (invalid JSON syntax)"
      );
      setSubmitting(false);
      return;
    }

    try {
      const provider = await finbotClient.saveProvider({
        credentials_schema: schema,
        ...values,
      });
      setSubmitting(false);
      setSelectedProviderId(provider.id);
      toast.success(`Provider '${provider.id}' has been saved`);
    } catch (e) {
      setSubmitting(false);
      toast.error(`Could not save provider: ${e}`);
    }
  };

  const handleDelete = async (providerId) => {
    try {
      await finbotClient.deleteProvider(providerId);
      setSelectedProviderId(null);
      toast.success(`Provider '${providerId}' has been deleted`);
    } catch (e) {
      toast.error(`Could not delete provider: ${e}`);
    }
  };

  const resetProviderDescription = ({ id, description, website_url }) => {
    setProviderDescription({
      id: id || "",
      description: description || "",
      website_url: website_url || "",
    });
  };

  useEffect(() => {
    if (selectedProviderId === null) {
      resetProviderDescription({
        id: null,
        description: null,
        website_url: null,
      });
      return;
    }
    const fetch = async () => {
      const provider = await finbotClient.getProvider(selectedProviderId);
      resetProviderDescription(provider);
      setRawSchema(JSON.stringify(provider.credentials_schema, null, 2));
    };
    fetch();
  }, [finbotClient, account, selectedProviderId]);

  const isNew = selectedProviderId === null;

  return (
    <div>
      <Row className={"mb-4"}>
        <Col>
          <h3>
            Providers
            <small>| {isNew ? "New" : selectedProviderId}</small>
          </h3>
        </Col>
      </Row>
      <Row className={"mb-4"}>
        <Col>
          <ProviderSelector
            defaultValue={ProviderSelector.New}
            onChange={(value) => {
              setSelectedProviderId(value.value);
            }}
            onNew={() => {
              setSelectedProviderId(null);
            }}
          />
        </Col>
      </Row>
      <Formik
        enableReinitialize
        validationSchema={PROVIDER_SCHEMA}
        initialValues={providerDescription}
        onSubmit={handleSubmit}
      >
        {({ isSubmitting, submitForm }) => (
          <MetaForm>
            <Row className={"mb-4"}>
              <Col>
                <h5>Description</h5>
              </Col>
            </Row>
            <Row className={"mb-4"}>
              <Col>
                <Form.Group>
                  <Form.Label>Identifier</Form.Label>
                  <Field
                    type="text"
                    name="id"
                    className="form-control"
                    disabled={!isNew}
                  />
                  <ErrorMessage
                    className="text-danger"
                    name="id"
                    component="div"
                  />
                </Form.Group>
                <Form.Group>
                  <Form.Label>Description</Form.Label>
                  <Field
                    type="text"
                    name="description"
                    className="form-control"
                  />
                  <ErrorMessage
                    className="text-danger"
                    name="description"
                    component="div"
                  />
                </Form.Group>
                <Form.Group>
                  <Form.Label>Website</Form.Label>
                  <Field
                    type="text"
                    name="website_url"
                    className="form-control"
                  />
                  <ErrorMessage
                    className="text-danger"
                    name="website_url"
                    component="div"
                  />
                </Form.Group>
              </Col>
            </Row>
            <Row className={"mb-4"}>
              <Col>
                <h5>Credentials schema</h5>
              </Col>
            </Row>
            <Row className={"mb-4"}>
              <Col>
                <Tabs defaultActiveKey={"editor"} id={"editor"}>
                  <Tab eventKey={"editor"} title={"Editor"}>
                    <AceEditor
                      height="30em"
                      value={rawSchema}
                      onBlur={(e, editor) => {
                        const rawSchema = editor.getValue();
                        setRawSchema(rawSchema);
                      }}
                      ref={(editor) => {
                        editorRef.current = editor;
                      }}
                      tabSize={2}
                      mode={"json"}
                      theme="github"
                      width="100%"
                      showGutter={true}
                      showPrintMargin={true}
                      readOnly={false}
                    />
                  </Tab>
                  <Tab eventKey={"preview"} title={"Preview"}>
                    <Row className={"mx-2 my-4"}>
                      <Col>
                        {schemaError === null && (
                          <DataDrivenForm
                            schema={schema.json_schema ?? {}}
                            uiSchema={schema.ui_schema ?? {}}
                            showErrorList={false}
                          >
                            <Button hidden disabled size={"xs"}>
                              Hidden
                            </Button>
                          </DataDrivenForm>
                        )}
                        {schemaError !== null && (
                          <Alert variant={"warning"}>
                            The credentials schema has errors: {schemaError}
                          </Alert>
                        )}
                      </Col>
                    </Row>
                  </Tab>
                </Tabs>
              </Col>
            </Row>
            <Row>
              <Col>
                <LoadingButton
                  size={"sm"}
                  onClick={submitForm}
                  variant="dark"
                  disabled={schemaError !== null}
                  loading={isSubmitting}
                >
                  {isNew ? "Create" : "Update"}
                </LoadingButton>{" "}
                {!isNew && (
                  <Button
                    onClick={() => {
                      handleDelete(selectedProviderId);
                    }}
                    variant={"dark"}
                    size={"sm"}
                  >
                    Delete
                  </Button>
                )}
              </Col>
            </Row>
          </MetaForm>
        )}
      </Formik>
    </div>
  );
};

export const ProvidersSettings = () => {
  return (
    <Row>
      <Col>
        <EditProviderPanel />
      </Col>
    </Row>
  );
};
