import React, { useState, useEffect, useRef } from "react";

import AceEditor from "react-ace";
import { useApi, FinancialDataProvidersApi } from "clients";
import { withTheme } from "@rjsf/core";
import validator from "@rjsf/validator-ajv8";
import { shadcnTheme } from "components/ui/rjsf-theme";
const DataDrivenForm = withTheme(shadcnTheme);
import { LoadingButton } from "components";
import { Formik, Form as MetaForm, Field, ErrorMessage } from "formik";
import { ProviderSelector } from "./components";
import { toast } from "react-toastify";

import { Button } from "components/ui/button";
import { Label } from "components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "components/ui/tabs";
import { Alert, AlertDescription } from "components/ui/alert";
import { Separator } from "components/ui/separator";

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
      "Provider identifier must start with a letter, and only contain letters, numbers or the underscore '_' character",
    )
    .min(4)
    .max(64),
  description: Yup.string()
    .required("Description is required")
    .max(256, "Description should be at most 64 characters"),
  websiteUrl: Yup.string().required("Website is required").max(256),
});

const useSchema = (rawSchema: string): [any | null, string | null] => {
  try {
    const schema = JSON.parse(rawSchema);
    return [schema, null];
  } catch (e) {
    return [null, `${e}`];
  }
};

interface ProviderDescription {
  id: string;
  description: string;
  websiteUrl: string;
}

const makeProviderDescription = (
  entry?: Partial<ProviderDescription>,
): ProviderDescription => {
  return {
    id: entry?.id ?? "",
    description: entry?.description ?? "",
    websiteUrl: entry?.websiteUrl ?? "",
  };
};

export const EditProviderPanel: React.FC<Record<string, never>> = () => {
  const financialDataProvidersApi = useApi(FinancialDataProvidersApi);
  const [selectedProviderId, setSelectedProviderId] = useState<string | null>(
    null,
  );
  const [providerDescription, setProviderDescription] = useState(
    makeProviderDescription(),
  );
  const [rawSchema, setRawSchema] = useState(() => {
    return JSON.stringify(DEFAULT_CREDENTIALS_SCHEMA, null, 2);
  });
  const [schema, schemaError] = useSchema(rawSchema);
  const editorRef = useRef<AceEditor | null>();

  const handleSubmit = async (
    description: ProviderDescription,
    { setSubmitting }: { setSubmitting: (submitting: boolean) => void },
  ) => {
    const editor = editorRef.current!.editor;
    let schema = null;
    try {
      schema = JSON.parse(editor.getValue());
    } catch (e) {
      toast.error(
        "Could not save provider: invalid credentials schema (invalid JSON syntax)",
      );
      setSubmitting(false);
      return;
    }

    try {
      const result =
        await financialDataProvidersApi.updateOrCreateFinancialDataProvider({
          createOrUpdateProviderRequest: {
            ...description,
            credentialsSchema: schema,
          },
        });
      const provider = result.provider;
      setSubmitting(false);
      setSelectedProviderId(provider.id);
      toast.success(`Provider '${provider.id}' has been saved`);
    } catch (e) {
      setSubmitting(false);
      toast.error(`Could not save provider: ${e}`);
    }
  };

  const handleDelete = async (providerId: string | null) => {
    try {
      if (providerId !== null) {
        await financialDataProvidersApi.deleteFinancialDataProvider({
          providerId,
        });
        setSelectedProviderId(null);
        toast.success(`Provider '${providerId}' has been deleted`);
      }
    } catch (e) {
      toast.error(`Could not delete provider: ${e}`);
    }
  };

  const resetProviderDescription = (entry?: Partial<ProviderDescription>) => {
    setProviderDescription(makeProviderDescription(entry));
  };

  useEffect(() => {
    if (selectedProviderId === null) {
      resetProviderDescription();
      return;
    }
    const fetch = async () => {
      const result = await financialDataProvidersApi.getFinancialDataProvider({
        providerId: selectedProviderId,
      });
      const provider = result.provider;
      resetProviderDescription(provider);
      setRawSchema(JSON.stringify(provider.credentialsSchema, null, 2));
    };
    fetch();
  }, [financialDataProvidersApi, selectedProviderId]);

  const isNew = selectedProviderId === null;

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-2xl font-semibold">
          Providers{" "}
          <span className="text-lg text-muted-foreground">
            | {isNew ? "New" : selectedProviderId}
          </span>
        </h3>
        <Separator className="mt-2" />
      </div>
      <div>
        <ProviderSelector
          defaultValue={ProviderSelector.New}
          onChange={(item) => {
            setSelectedProviderId(item?.value ?? null);
          }}
          onNew={() => {
            setSelectedProviderId(null);
          }}
        />
      </div>
      <Formik
        enableReinitialize
        validationSchema={PROVIDER_SCHEMA}
        initialValues={providerDescription}
        onSubmit={handleSubmit}
      >
        {({ isSubmitting, submitForm }) => (
          <MetaForm>
            <div className="space-y-6">
              <div className="space-y-4">
                <h5 className="font-medium">Description</h5>
                <div className="space-y-2">
                  <Label>Identifier</Label>
                  <Field
                    type="text"
                    name="id"
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                    disabled={!isNew}
                  />
                  <ErrorMessage
                    className="text-sm text-red-500"
                    name="id"
                    component="div"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Description</Label>
                  <Field
                    type="text"
                    name="description"
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  />
                  <ErrorMessage
                    className="text-sm text-red-500"
                    name="description"
                    component="div"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Website</Label>
                  <Field
                    type="text"
                    name="websiteUrl"
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  />
                  <ErrorMessage
                    className="text-sm text-red-500"
                    name="websiteUrl"
                    component="div"
                  />
                </div>
              </div>
              <div className="space-y-4">
                <h5 className="font-medium">Credentials schema</h5>
                <Tabs defaultValue="editor">
                  <TabsList>
                    <TabsTrigger value="editor">Editor</TabsTrigger>
                    <TabsTrigger value="preview">Preview</TabsTrigger>
                  </TabsList>
                  <TabsContent value="editor">
                    <AceEditor
                      height="30em"
                      value={rawSchema}
                      onBlur={(e, editor) => {
                        const rawSchema = editor!.getValue();
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
                  </TabsContent>
                  <TabsContent value="preview">
                    <div className="p-4">
                      {schemaError === null && (
                        <DataDrivenForm
                          schema={schema.json_schema ?? {}}
                          uiSchema={schema.ui_schema ?? {}}
                          validator={validator}
                          showErrorList={false}
                        >
                          <Button hidden disabled size="sm">
                            Hidden
                          </Button>
                        </DataDrivenForm>
                      )}
                      {schemaError !== null && (
                        <Alert variant="warning">
                          <AlertDescription>
                            The credentials schema has errors: {schemaError}
                          </AlertDescription>
                        </Alert>
                      )}
                    </div>
                  </TabsContent>
                </Tabs>
              </div>
              <div className="flex items-center gap-2">
                <LoadingButton
                  size="sm"
                  onClick={submitForm}
                  disabled={schemaError !== null}
                  loading={isSubmitting}
                >
                  {isNew ? "Create" : "Update"}
                </LoadingButton>
                {!isNew && (
                  <Button
                    onClick={() => {
                      handleDelete(selectedProviderId);
                    }}
                    variant="destructive"
                    size="sm"
                  >
                    Delete
                  </Button>
                )}
              </div>
            </div>
          </MetaForm>
        )}
      </Formik>
    </div>
  );
};

export const ProvidersSettings: React.FC<Record<string, never>> = () => {
  return <EditProviderPanel />;
};
