import React, { useEffect, useState, useContext, useRef } from "react";
import { Navigate } from "react-router-dom";
import { Check } from "lucide-react";

import {
  useApi,
  Provider,
  LinkedAccount,
  LinkedAccountsApi,
  FinancialDataProvidersApi,
  FormattingRulesApi,
  PlaidSettings,
  SystemApi,
  GetAccountsFormattingRulesResponse,
} from "clients";
import { AuthContext } from "contexts";
import { LoadingButton, ColourPicker } from "components";

import { withTheme } from "@rjsf/core";
import type { IChangeEvent } from "@rjsf/core";
import validator from "@rjsf/validator-ajv8";
import { shadcnTheme } from "components/ui/rjsf-theme";
const DataDrivenForm = withTheme(shadcnTheme);
import { toast } from "sonner";
import { Button } from "components/ui/button";
import { Input } from "components/ui/input";
import { Label } from "components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "components/ui/select";
import { Alert, AlertDescription } from "components/ui/alert";
import { PlaidLink } from "react-plaid-link";

const NO_PROVIDER_SELECTED = "NO_PROVIDER_SELECTED";
const PLAID_PROVIDER_ID = "plaid_us";
const FALLBACK_COLOUR = "#FFFFFF";

type FormattingRules = GetAccountsFormattingRulesResponse;
type LinkedAccountCredentials = object;

interface DataDrivenAccountFormProps {
  operation: string | null;
  schema: any;
  onSubmit(credentials: LinkedAccountCredentials): void;
  updateMode: boolean;
}

const DataDrivenAccountForm: React.FC<DataDrivenAccountFormProps> = ({
  operation,
  schema,
  onSubmit,
  updateMode,
}) => {
  return (
    <DataDrivenForm
      schema={schema.json_schema ?? {}}
      uiSchema={schema.ui_schema ?? {}}
      onSubmit={(event: IChangeEvent<LinkedAccountCredentials | null>) => {
        onSubmit(event.formData ?? {});
      }}
      validator={validator}
      showErrorList={false}
    >
      <LoadingButton
        loading={operation !== null}
        type="submit"
        size="sm"
        className="mt-4"
      >
        {operation || (updateMode ? "Update credentials" : "Link account")}
      </LoadingButton>
    </DataDrivenForm>
  );
};

interface PlaidFormProps {
  operation: string | null;
  settings: PlaidSettings;
  onSubmit(data: { public_token: string }): void;
  linkToken: string | null;
}

const PlaidForm: React.FC<PlaidFormProps> = ({
  operation,
  settings,
  onSubmit,
  linkToken,
}) => {
  const updateMode = !!linkToken;

  if (operation !== null) {
    return (
      <LoadingButton size="sm" loading>
        {operation}
      </LoadingButton>
    );
  }

  return (
    <PlaidLink
      clientName="Finbot"
      onSuccess={(public_token: string) => {
        onSubmit({ public_token });
      }}
      onEvent={(
        eventName: string,
        metadata: { error_message?: string | null },
      ) => {
        if (metadata.error_message) {
          toast.error(`Plaid error: ${metadata.error_message}`);
        }
      }}
      token={updateMode ? linkToken! : undefined}
      publicKey={settings.publicKey}
      env={settings.environment}
      countryCodes={["FR"]}
      product={updateMode ? [] : ["transactions", "identity"]}
      style={{
        background: "#3458e6",
        color: "#FFFFFF",
        fontSize: "13px",
        paddingLeft: "0.8em",
        paddingRight: "0.8em",
        fontWeight: 500,
        borderRadius: "0.4em",
      }}
    >
      {updateMode ? "Update" : "Link account"}&nbsp;via Plaid
    </PlaidLink>
  );
};

const isPlaidSelected = (provider?: Provider | null) => {
  return provider && provider.id === PLAID_PROVIDER_ID;
};

const getPlaidLinkToken = (credentials: object): string | null => {
  if ("link_token" in credentials) {
    return credentials.link_token as string;
  }
  return null;
};

export interface LinkAccountProps {
  linkedAccount?: LinkedAccount | null;
  onSuccess?: () => void;
}

export const LinkAccount: React.FC<LinkAccountProps> = (props) => {
  const { userAccountId } = useContext(AuthContext);
  const linkedAccountsApi = useApi(LinkedAccountsApi);
  const providersApi = useApi(FinancialDataProvidersApi);
  const formattingRulesApi = useApi(FormattingRulesApi);
  const systemApi = useApi(SystemApi);

  const [formattingRules, setFormattingRules] =
    useState<FormattingRules | null>(null);
  const [linkedAccount, setLinkedAccount] = useState<LinkedAccount | null>(
    null,
  );
  const [providers, setProviders] = useState<Array<Provider>>([]);
  const [plaidSettings, setPlaidSettings] = useState<PlaidSettings | null>(
    null,
  );
  const [selectedProvider, setSelectedProvider] = useState<Provider | null>(
    null,
  );
  const [accountName, setAccountName] = useState<string | null>(null);
  const [accountColour, setAccountColour] = useState<string | null>(null);
  const [operation, setOperation] = useState<string | null>(null);
  const [linked, setLinked] = useState<boolean>(false);
  const [isDemo, setIsDemo] = useState<boolean>(false);
  const accountNameRef = useRef(accountName);
  const accountColourRef = useRef(accountColour);
  const updateMode = linkedAccount !== null;

  useEffect(() => {
    const fetch = async () => {
      const result = await providersApi.getFinancialDataProviders();
      setProviders(
        result.providers.sort((p1, p2) => {
          return p1.description.localeCompare(p2.description);
        }),
      );
      setPlaidSettings(
        (await providersApi.getPlaidSettings()).settings ?? null,
      );
      setFormattingRules(await formattingRulesApi.getAccountsFormattingRules());
      setIsDemo((await systemApi.getSystemReport()).systemReport.isDemo);
    };
    fetch();
  }, [providersApi, formattingRulesApi, systemApi]);

  useEffect(() => {
    if (props.linkedAccount) {
      const existingLinkedAccount = { ...props.linkedAccount };
      providers.forEach((provider) => {
        if (existingLinkedAccount.providerId === provider.id) {
          setSelectedProvider(provider);
        }
      });
      setLinkedAccount(existingLinkedAccount);
      updateAccountName(existingLinkedAccount.accountName);
      updateAccountColour(existingLinkedAccount.accountColour);
    }
  }, [providers, props.linkedAccount]);

  useEffect(() => {
    if (formattingRules && accountColour === null) {
      const palette = formattingRules.colourPalette;
      updateAccountColour(palette[Math.floor(Math.random() * palette.length)]);
    }
  }, [formattingRules, accountColour]);

  const updateAccountName = (newName: string) => {
    setAccountName(newName);
    accountNameRef.current = newName;
  };

  const updateAccountColour = (newColour: string) => {
    setAccountColour(newColour);
    accountColourRef.current = newColour;
  };

  const onSelectedProviderChanged = (providerId: string) => {
    if (providerId === NO_PROVIDER_SELECTED) {
      setSelectedProvider(null);
      return;
    }
    const provider = providers.find((provider) => {
      return provider.id === providerId;
    });
    updateAccountName(provider!.description);
    setSelectedProvider(provider!);
  };

  const onUpdateExistingAccountMetadata = async () => {
    try {
      const updatedProps: Partial<LinkedAccount> = {};
      if (
        accountNameRef.current &&
        accountNameRef.current !== linkedAccount!.accountName
      ) {
        updatedProps.accountName = accountNameRef.current;
      }
      if (
        accountColourRef.current &&
        accountColourRef.current !== linkedAccount!.accountColour
      ) {
        updatedProps.accountColour = accountColourRef.current;
      }
      await linkedAccountsApi.updateLinkedAccountMetadata({
        userAccountId: userAccountId!,
        linkedAccountId: linkedAccount!.id,
        updateLinkedAccountMetadataRequest: {
          accountName: updatedProps.accountName,
          accountColour: updatedProps.accountColour,
        },
      });
      setLinkedAccount({ ...linkedAccount!, ...updatedProps });
      toast.success(`Linked account updated`);
    } catch (e) {
      toast.error(`Failed to update account: '${e}'`);
    }
  };

  const requestUpdateCredentials = async (
    credentials: LinkedAccountCredentials,
  ) => {
    setOperation("Validating credentials");
    try {
      await linkedAccountsApi.updateLinkedAccountCredentials({
        userAccountId: userAccountId!,
        linkedAccountId: linkedAccount!.id,
        doValidate: true,
        doPersist: false,
        updateLinkedAccountCredentialsRequest: {
          credentials: credentials,
        },
      });
    } catch (e) {
      toast.error(`Error validating credentials: ${e}`);
      setOperation(null);
      return;
    }
    setOperation("Updating credentials");
    try {
      await linkedAccountsApi.updateLinkedAccountCredentials({
        userAccountId: userAccountId!,
        linkedAccountId: linkedAccount!.id,
        doValidate: false,
        doPersist: true,
        updateLinkedAccountCredentialsRequest: {
          credentials: credentials,
        },
      });
      toast.success(
        `Credentials for linked account '${
          linkedAccount!.accountName
        }' updated`,
      );
    } catch (e) {
      toast.error(`Error updating credentials: ${e}`);
    }
    setOperation(null);
  };

  const requestLinkAccount = async (
    provider: Provider,
    credentials: LinkedAccountCredentials,
  ) => {
    const linkRequest = {
      providerId: provider.id,
      credentials: credentials,
      accountName: accountNameRef.current ?? "",
      accountColour: accountColourRef.current ?? FALLBACK_COLOUR,
    };
    setOperation("Validating credentials");
    try {
      await linkedAccountsApi.linkNewAccount({
        userAccountId: userAccountId!,
        doValidate: true,
        doPersist: false,
        linkAccountRequest: linkRequest,
      });
    } catch (e) {
      toast.error(`Error validating credentials: ${e}`);
      setOperation(null);
      return;
    }
    setOperation("Linking account");
    try {
      await linkedAccountsApi.linkNewAccount({
        userAccountId: userAccountId!,
        doValidate: false,
        doPersist: true,
        linkAccountRequest: linkRequest,
      });
    } catch (e) {
      toast.error(`Error updating credentials: ${e}`);
      setOperation(null);
      return;
    }
    setOperation(null);
    setLinked(true);
  };

  if (linked) {
    if (props.onSuccess) {
      props.onSuccess();
      return null;
    }
    return <Navigate to={"/settings/linked"} />;
  }

  return (
    <div className="max-w-lg space-y-6">
      {isDemo && (
        <Alert variant="warning">
          <AlertDescription>
            <strong>Note</strong>: Only fake financial data providers are
            available in the Finbot demo.
          </AlertDescription>
        </Alert>
      )}
      <div className="space-y-2">
        <h5 className="font-medium">Provider selection</h5>
        <Select
          value={(selectedProvider ?? { id: NO_PROVIDER_SELECTED }).id}
          onValueChange={onSelectedProviderChanged}
          disabled={updateMode}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select a provider" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={NO_PROVIDER_SELECTED}>
              Select a provider
            </SelectItem>
            {providers.map((provider) => (
              <SelectItem key={`sel-${provider.id}`} value={provider.id}>
                {provider.description}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      {selectedProvider !== null && (
        <div className="space-y-2">
          <h5 className="font-medium">Account name</h5>
          <div className="flex items-center gap-2">
            <ColourPicker
              presetsColours={formattingRules?.colourPalette}
              colour={accountColour ?? FALLBACK_COLOUR}
              onChange={(newColour) => updateAccountColour(newColour)}
            />
            <Input
              type="text"
              placeholder="Account name"
              value={accountName ?? ""}
              onChange={(event) => {
                updateAccountName(event.target.value);
              }}
            />
            {updateMode &&
              (accountName !== linkedAccount!.accountName ||
                accountColour !== linkedAccount!.accountColour) && (
                <Button size="sm" onClick={onUpdateExistingAccountMetadata}>
                  <Check className="h-4 w-4" />
                </Button>
              )}
          </div>
        </div>
      )}
      {selectedProvider !== null && (
        <div className="space-y-2">
          <h5 className="font-medium">Credentials</h5>
          {!isPlaidSelected(selectedProvider) && (
            <DataDrivenAccountForm
              operation={operation}
              schema={selectedProvider.credentialsSchema}
              updateMode={updateMode}
              onSubmit={(credentials: LinkedAccountCredentials) => {
                if (updateMode) {
                  requestUpdateCredentials(credentials);
                } else {
                  requestLinkAccount({ ...selectedProvider }, credentials);
                }
              }}
            />
          )}
          {isPlaidSelected(selectedProvider) && plaidSettings && (
            <PlaidForm
              operation={operation}
              settings={plaidSettings!}
              linkToken={
                updateMode
                  ? getPlaidLinkToken(linkedAccount!.credentials!)
                  : null
              }
              onSubmit={(credentials) => {
                if (updateMode) {
                  requestUpdateCredentials(credentials);
                } else {
                  requestLinkAccount({ ...selectedProvider! }, credentials);
                }
              }}
            />
          )}
        </div>
      )}
    </div>
  );
};
