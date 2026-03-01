import React, { useEffect, useState } from "react";

import { useApi, AdministrationApi, EmailProviderMetadata } from "clients";

import ReactSelect from "react-select";
import { themedSelectStyles } from "components/ui/react-select-theme";
import { withTheme } from "@rjsf/core";
import type { UiSchema } from "@rjsf/utils";
import validator from "@rjsf/validator-ajv8";
import { shadcnTheme } from "components/ui/rjsf-theme";
const DataDrivenForm = withTheme(shadcnTheme);
import { LoadingButton } from "components";
import { toast } from "sonner";

import { Input } from "components/ui/input";
import { Label } from "components/ui/label";
import { Checkbox } from "components/ui/checkbox";
import { Separator } from "components/ui/separator";

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
        emailDeliverySettings: {
          senderName,
          subjectPrefix,
          providerId: provider!.providerId,
          providerSettings: formData,
        },
        validate: validate,
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
    <div className="space-y-6">
      <div>
        <h3 className="text-2xl font-semibold">Email delivery</h3>
        <Separator className="mt-2" />
      </div>
      <div className="flex items-center gap-2">
        <Checkbox
          id="enable-delivery"
          checked={enableDelivery}
          onCheckedChange={(checked) => {
            const isChecked = !!checked;
            setEnableDelivery(isChecked);
            if (provider === null && isChecked) {
              setProvider(providers[0]);
            }
          }}
        />
        <Label htmlFor="enable-delivery">Enable email delivery</Label>
      </div>
      <div className="grid max-w-lg gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <Label>Sender name*</Label>
          <Input
            type="text"
            value={senderName}
            disabled={!enableDelivery}
            onChange={(event) => {
              setSenderName(event.currentTarget.value);
            }}
          />
        </div>
        <div className="space-y-2">
          <Label>Subject prefix</Label>
          <Input
            type="text"
            value={subjectPrefix}
            disabled={!enableDelivery}
            onChange={(event) => {
              setSubjectPrefix(event.currentTarget.value);
            }}
          />
        </div>
      </div>
      <div className="max-w-lg space-y-2">
        <Label>Delivery method*</Label>
        <ReactSelect
          styles={themedSelectStyles}
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
      </div>
      <div className="max-w-lg">
        {provider && (
          <DataDrivenForm
            formData={providerSettings ?? ({} as any)}
            onSubmit={({ formData }) => {
              handleSaveWithProviderSettings(formData);
            }}
            disabled={!enableDelivery}
            uiSchema={getProviderUiSchema(provider)}
            schema={getProviderSchema(provider)}
            validator={validator}
          >
            <LoadingButton
              className={enableDelivery ? "mt-4" : "hidden"}
              type="submit"
              disabled={loading || !enableDelivery}
              loading={loading}
              size="sm"
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
            size="sm"
          >
            Save
          </LoadingButton>
        )}
      </div>
    </div>
  );
};
