import React, { useEffect, useState, useContext, useRef } from "react";
import { Navigate } from "react-router-dom";

import { AuthContext, ServicesContext } from "contexts";
import { LoadingButton, ColourPicker } from "components";
import {
  LinkedAccount,
  LinkedAccountCredentials,
  PlaidSettings,
  Provider,
  AccountsFormattingRules,
} from "clients/finbot-client/types";

import { default as DataDrivenForm, ISubmitEvent } from "react-jsonschema-form";
import { toast } from "react-toastify";
import { Row, Col, Form, InputGroup, Button } from "react-bootstrap";
import { FaCheck } from "react-icons/fa";
import { PlaidLink } from "react-plaid-link";

const NO_PROVIDER_SELECTED = "NO_PROVIDER_SELECTED";
const PLAID_PROVIDER_ID = "plaid_us";
const FALLBACK_COLOUR = "#FFFFFF";

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
      onSubmit={(event: ISubmitEvent<LinkedAccountCredentials | null>) => {
        onSubmit(event.formData ?? {});
      }}
      showErrorList={false}
    >
      <LoadingButton
        loading={operation !== null}
        variant={"dark"}
        type="submit"
        size={"sm"}
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
      <LoadingButton variant={"dark"} loading={true}>
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
      publicKey={settings.public_key}
      env={settings.environment}
      countryCodes={["GB", "US", "CA", "IE", "FR", "ES", "NL"]}
      product={updateMode ? [] : ["transactions", "identity"]}
    >
      {updateMode ? "Update account" : "Link account"}&nbsp;via Plaid
    </PlaidLink>
  );
};

const isPlaidSelected = (provider?: Provider | null) => {
  return provider && provider.id === PLAID_PROVIDER_ID;
};

export interface LinkAccountProps {
  linkedAccount?: LinkedAccount | null;
}

export const LinkAccount: React.FC<LinkAccountProps> = (props) => {
  const { userAccountId } = useContext(AuthContext);
  const { finbotClient } = useContext(ServicesContext);

  const [formattingRules, setFormattingRules] =
    useState<AccountsFormattingRules | null>(null);
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
  const accountNameRef = useRef(accountName);
  const accountColourRef = useRef(accountColour);
  const updateMode = linkedAccount !== null;

  useEffect(() => {
    const fetch = async () => {
      const providersPayload = await finbotClient!.getProviders();
      setProviders(
        providersPayload.sort((p1, p2) => {
          return p1.description.localeCompare(p2.description);
        }),
      );
      setPlaidSettings(await finbotClient!.getPlaidSettings());
      setFormattingRules(await finbotClient!.getAccountsFormattingRules());
    };
    fetch();
  }, [finbotClient]);

  useEffect(() => {
    if (props.linkedAccount) {
      const existingLinkedAccount = { ...props.linkedAccount };
      providers.forEach((provider) => {
        if (existingLinkedAccount.provider_id === provider.id) {
          setSelectedProvider(provider);
        }
      });
      setLinkedAccount(existingLinkedAccount);
      updateAccountName(existingLinkedAccount.account_name);
      updateAccountColour(existingLinkedAccount.account_colour);
    }
  }, [providers, props.linkedAccount]);

  useEffect(() => {
    if (formattingRules && accountColour === null) {
      const palette = formattingRules.colour_palette;
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
        accountNameRef.current !== linkedAccount!.account_name
      ) {
        updatedProps.account_name = accountNameRef.current;
      }
      if (
        accountColourRef.current &&
        accountColourRef.current !== linkedAccount!.account_colour
      ) {
        updatedProps.account_colour = accountColourRef.current;
      }
      await finbotClient!.updateLinkedAccountMetadata({
        account_id: userAccountId!,
        linked_account_id: linkedAccount!.id,
        account_name: updatedProps.account_name,
        account_colour: updatedProps.account_colour,
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
    const settings = {
      account_id: userAccountId!,
      linked_account_id: linkedAccount!.id,
      credentials: credentials,
    };
    try {
      await finbotClient!.updateLinkedAccountCredentials({
        ...settings,
        validate: true,
        persist: false,
      });
    } catch (e) {
      toast.error(`Error validating credentials: ${e}`);
      setOperation(null);
      return;
    }
    setOperation("Updating credentials");
    try {
      await finbotClient!.updateLinkedAccountCredentials({
        ...settings,
        validate: false,
        persist: true,
      });
      toast.success(
        `Credentials for linked account '${
          linkedAccount!.account_name
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
    const link_settings = {
      provider_id: provider.id,
      account_name: accountNameRef.current ?? "",
      account_colour: accountColourRef.current ?? FALLBACK_COLOUR,
      credentials,
    };
    setOperation("Validating credentials");
    try {
      await finbotClient!.validateLinkedAccountCredentials({
        account_id: userAccountId!,
        ...link_settings,
      });
    } catch (e) {
      toast.error(`Error validating credentials: ${e}`);
      setOperation(null);
      return;
    }
    setOperation("Linking account");
    try {
      await finbotClient!.linkAccount({
        account_id: userAccountId!,
        ...link_settings,
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
    return <Navigate to={"/settings/linked"} />;
  }

  return (
    <>
      <Row>
        <Col>
          <Row className={"mb-4"}>
            <Col>
              <h5>1. Provider selection</h5>
            </Col>
          </Row>
          <Row className={"mb-4"}>
            <Col>
              <Form.Group>
                <Form.Control
                  value={(selectedProvider ?? { id: NO_PROVIDER_SELECTED }).id}
                  as="select"
                  size="sm"
                  onChange={(event) => {
                    onSelectedProviderChanged(event.target.value);
                  }}
                  disabled={updateMode}
                >
                  <option value={NO_PROVIDER_SELECTED}>
                    Select a provider
                  </option>
                  {providers.map((provider) => {
                    return (
                      <option key={`sel-${provider.id}`} value={provider.id}>
                        {provider.description}
                      </option>
                    );
                  })}
                </Form.Control>
              </Form.Group>
            </Col>
          </Row>
          {selectedProvider !== null && (
            <>
              <Row className={"mb-4"}>
                <Col>
                  <h5>2. Account name</h5>
                </Col>
              </Row>
              <Row className={"mb-4"}>
                <Col>
                  <InputGroup>
                    <ColourPicker
                      presetsColours={formattingRules?.colour_palette}
                      colour={accountColour ?? FALLBACK_COLOUR}
                      onChange={(newColour) => updateAccountColour(newColour)}
                    />
                    <Form.Control
                      type="text"
                      placeholder="Account name"
                      value={accountName ?? ""}
                      onChange={(event) => {
                        updateAccountName(event.target.value);
                      }}
                    />
                    {updateMode &&
                      (accountName !== linkedAccount!.account_name ||
                        accountColour !== linkedAccount!.account_colour) && (
                        <Button
                          variant={"primary"}
                          onClick={onUpdateExistingAccountMetadata}
                        >
                          <FaCheck />
                        </Button>
                      )}
                  </InputGroup>
                </Col>
              </Row>
            </>
          )}
          {selectedProvider !== null && !isPlaidSelected(selectedProvider) && (
            <Row className={"mb-4"}>
              <Col>
                <h5>3. Credentials</h5>
              </Col>
            </Row>
          )}
          <Row>
            <Col>
              {selectedProvider !== null &&
                !isPlaidSelected(selectedProvider) && (
                  <DataDrivenAccountForm
                    operation={operation}
                    schema={selectedProvider.credentials_schema}
                    updateMode={updateMode}
                    onSubmit={(credentials: LinkedAccountCredentials) => {
                      if (updateMode) {
                        requestUpdateCredentials(credentials);
                      } else {
                        requestLinkAccount(
                          { ...selectedProvider },
                          credentials,
                        );
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
                      ? (linkedAccount!.credentials!.link_token as string)
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
            </Col>
          </Row>
        </Col>
      </Row>
    </>
  );
};
