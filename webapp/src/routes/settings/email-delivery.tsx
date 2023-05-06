import React, { useContext, useEffect, useState } from "react";

import { ServicesContext } from "contexts";
import { EmailDeliveryProvider } from "clients/finbot-client/types";

import Select from "react-select";
import { default as DataDrivenForm } from "react-jsonschema-form";
import { Row, Col, Form } from "react-bootstrap";
import { LoadingButton } from "components";
import { toast } from "react-toastify";

const makeProvidersSelectValue = (provider: EmailDeliveryProvider) => {
  return {
    label: provider.description,
    value: provider.provider_id,
  };
};

export const EmailDeliverySettingsPanel: React.FC<
  Record<string, never>
> = () => {
  const { finbotClient } = useContext(ServicesContext);
  const [loading, setLoading] = useState<boolean>(false);
  const [enableDelivery, setEnableDelivery] = useState<boolean>(false);
  const [senderName, setSenderName] = useState<string>("Finbot Admin");
  const [subjectPrefix, setSubjectPrefix] = useState<string>("[FINBOT]");
  const [providers, setProviders] = useState<Array<EmailDeliveryProvider>>([]);
  const [provider, setProvider] = useState<EmailDeliveryProvider | null>(null);
  const [providerSettings, setProviderSettings] = useState<any | null>(null);

  useEffect(() => {
    const fetch = async () => {
      const providersData = await finbotClient!.getEmailDeliveryProviders();
      setProviders(providersData);
      const currentSettings = await finbotClient!.getEmailDeliverySettings();
      if (currentSettings !== null) {
        const provider = providersData.filter((provider) => {
          return provider.provider_id === currentSettings.provider_id;
        })[0];
        setEnableDelivery(true);
        setProvider(provider);
        setProviderSettings(currentSettings.provider_settings);
      } else {
        setEnableDelivery(false);
        setProvider(null);
        setProviderSettings(null);
      }
    };
    fetch();
  }, [finbotClient]);

  const setProviderById = (providerId?: string | null): void => {
    for (const entry of providers) {
      if (entry.provider_id === providerId) {
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
      await finbotClient!.setEmailDeliverySettings(
        {
          sender_name: senderName,
          subject_prefix: subjectPrefix,
          provider_id: provider!.provider_id,
          provider_settings: formData,
        },
        validate
      );
      toast.success("Email delivery settings have been updated successfully");
    } catch (e) {
      toast.error(`${e}`);
    }
    setLoading(false);
  };

  const handleSaveDisableEmailDelivery = async () => {
    try {
      setLoading(true);
      await finbotClient!.disableEmailDelivery();
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
      <Row>
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
      <Row>
        <Col>
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
        <Col>
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
      <Row>
        <Col>
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
      <Row>
        <Col>
          {provider && (
            <DataDrivenForm
              formData={providerSettings ?? ({} as any)}
              onSubmit={({ formData }) => {
                handleSaveWithProviderSettings(formData);
              }}
              disabled={!enableDelivery}
              uiSchema={provider.settings_schema.ui_schema ?? {}}
              schema={provider.settings_schema.settings_schema}
            >
              <LoadingButton
                style={{
                  display: enableDelivery ? "block" : "none",
                }}
                disabled={!enableDelivery}
                loading={loading}
                type={"submit"}
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
              type={"submit"}
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
