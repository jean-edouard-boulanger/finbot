import React, { useEffect, useState } from "react";

import { useApi, AdministrationApi, EmailProviderMetadata } from "clients";

import Select from "react-select";
import { default as DataDrivenForm, UiSchema } from "react-jsonschema-form";
import { Row, Col, Form } from "react-bootstrap";
import { LoadingButton } from "components";
import { toast } from "react-toastify";

const getProviderUiSchema = (provider: EmailProviderMetadata): UiSchema => {
  if ("ui_schema" in provider.settingsSchema) {
    return provider.settingsSchema.ui_schema as UiSchema;
  }
  return {};
};

const getProviderSchema = (provider: EmailProviderMetadata): any => {
  if ("settings_schema" in provider.settingsSchema) {
    return provider.settingsSchema.settings_schema as any;
  }
  return {};
};

const makeProvidersSelectValue = (provider: EmailProviderMetadata) => {
  return {
    label: provider.description,
    value: provider.providerId,
  };
};

export const EmailDeliverySettingsPanel: React.FC<
  Record<string, never>
> = () => {
  const administrationApi = useApi(AdministrationApi);
  const [loading, setLoading] = useState<boolean>(false);
  const [enableDelivery, setEnableDelivery] = useState<boolean>(false);
  const [senderName, setSenderName] = useState<string>("Finbot Admin");
  const [subjectPrefix, setSubjectPrefix] = useState<string>("[FINBOT]");
  const [providers, setProviders] = useState<Array<EmailProviderMetadata>>([]);
  const [provider, setProvider] = useState<EmailProviderMetadata | null>(null);
  const [providerSettings, setProviderSettings] = useState<any | null>(null);

  useEffect(() => {
    const fetch = async () => {
      const providersData = (
        await administrationApi.getEmailDeliveryProviders()
      ).providers;
      setProviders(providersData);
      const currentSettings = (
        await administrationApi.getEmailDeliverySettings()
      ).settings;
      if (currentSettings) {
        const provider = providersData.filter((provider) => {
          return provider.providerId === currentSettings.providerId;
        })[0];
        setEnableDelivery(true);
        setProvider(provider);
        setProviderSettings(currentSettings.providerSettings);
      } else {
        setEnableDelivery(false);
        setProvider(null);
        setProviderSettings(null);
      }
    };
    fetch();
  }, [administrationApi]);

  const setProviderById = (providerId?: string | null): void => {
    for (const entry of providers) {
      if (entry.providerId === providerId) {
        setProvider(entry);
        return;
      }
    }
    setProvider(null);
  };

  const handleSaveWithProviderSettings = async (formData: any) => {
    try {
      setLoading(true);
      setProviderSettings(formData);
      const validate = true;
      await administrationApi.setEmailDeliverySettings({
        validate,
        appEmailDeliverySettings: {
          senderName,
          subjectPrefix,
          providerId: provider!.providerId,
          providerSettings: formData,
        },
      });
      toast.success("Email delivery settings have been updated successfully");
    } catch (e) {
      toast.error(`${e}`);
    }
    setLoading(false);
  };

  const handleSaveDisableEmailDelivery = async () => {
    try {
      setLoading(true);
      await administrationApi.removeEmailDeliverySettings();
      toast.success("Email delivery has been disabled");
    } catch (e) {
      toast.error(`${e}`);
    }
    setLoading(false);
  };

  return (
    <>
      <Row className={"mb-4"}>
        <Col>
          <h3>Email delivery</h3>
          <hr />
        </Col>
      </Row>
      <Row className={"mb-4"}>
        <Col>
          <Form.Group>
            <Form.Check
              checked={enableDelivery}
              onChange={(event) => {
                const checked = event.currentTarget.checked;
                setEnableDelivery(checked);
                if (provider === null && checked) {
                  setProvider(providers[0]);
                }
              }}
              type="checkbox"
              label="Enable email delivery"
            />
          </Form.Group>
        </Col>
      </Row>
      <Row className={"mb-4"}>
        <Col md={3}>
          <Form.Group>
            <Form.Label>Sender name*</Form.Label>
            <Form.Control
              type={"text"}
              value={senderName}
              disabled={!enableDelivery}
              onChange={(event) => {
                setSenderName(event.currentTarget.value);
              }}
            />
          </Form.Group>
        </Col>
        <Col md={3}>
          <Form.Group>
            <Form.Label>Subject prefix</Form.Label>
            <Form.Control
              type={"text"}
              value={subjectPrefix}
              disabled={!enableDelivery}
              onChange={(event) => {
                setSubjectPrefix(event.currentTarget.value);
              }}
            />
          </Form.Group>
        </Col>
      </Row>
      <Row className={"mb-4"}>
        <Col md={6}>
          <Form.Group>
            <Form.Label>Delivery method*</Form.Label>
            <Select
              isDisabled={!enableDelivery}
              placeholder="Delivery method"
              isLoading={providers.length === 0}
              value={
                provider === null
                  ? undefined
                  : makeProvidersSelectValue(provider)
              }
              options={providers.map(makeProvidersSelectValue)}
              onChange={(entry) => {
                setProviderById(entry?.value);
              }}
            />
          </Form.Group>
        </Col>
      </Row>
      <Row className={"mb-4"}>
        <Col md={6}>
          {provider && (
            <DataDrivenForm
              formData={providerSettings ?? ({} as any)}
              onSubmit={({ formData }) => {
                handleSaveWithProviderSettings(formData);
              }}
              disabled={!enableDelivery}
              uiSchema={getProviderUiSchema(provider)}
              schema={getProviderSchema(provider)}
            >
              <LoadingButton
                style={{
                  display: enableDelivery ? "block" : "none",
                }}
                disabled={!enableDelivery}
                loading={loading}
                size={"sm"}
              >
                Save
              </LoadingButton>
            </DataDrivenForm>
          )}
          {!enableDelivery && (
            <LoadingButton
              onClick={handleSaveDisableEmailDelivery}
              disabled={enableDelivery}
              loading={loading}
              size={"sm"}
            >
              Save
            </LoadingButton>
          )}
        </Col>
      </Row>
    </>
  );
};
