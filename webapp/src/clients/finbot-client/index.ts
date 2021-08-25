import axios, { AxiosResponse } from "axios";

import {
  DeleteAccountPlaidSettingsRequest,
  DeleteLinkedAccountRequest,
  DeleteProviderRequest,
  EarningsReport,
  FinbotErrorMetadata,
  GetAccountHistoricalValuationRequest,
  GetAccountHistoricalValuationResponse,
  GetAccountPlaidSettingsRequest,
  GetAccountPlaidSettingsResponse,
  GetAccountSettingsRequest,
  GetAccountValuationRequest,
  GetAccountValuationResponse,
  GetTracesRequest,
  GetTracesResponse,
  GetLinkedAccountRequest,
  GetLinkedAccountsRequest,
  GetLinkedAccountsValuationRequest,
  GetLinkedAccountsValuationResponse,
  GetProviderRequest,
  GetProvidersResponse,
  GetUserAccountRequest,
  GetUserAccountResponse,
  HoldingsReport,
  IsAccountConfiguredRequest,
  IsAccountConfiguredResponse,
  LinkAccountRequest,
  LoginRequest,
  LoginResponse,
  PlaidSettings,
  Provider,
  RegisterAccountRequest,
  ReportResponse,
  SaveProviderRequest,
  UpdateAccountPlaidSettingsRequest,
  UpdateAccountProfileRequest,
  UpdateAccountProfileResponse,
  UpdateLinkedAccountCredentials,
  UpdateLinkedAccountMetadata,
  UpdateTwilioAccountSettingsRequest,
  UserAccount,
  UserAccountProfile,
  UserAccountValuation,
  ValidateLinkedAccountCredentialsRequest,
  TracesTree,
  RegisterAccountResponse,
  GetAccountSettingsResponse,
  UserAccountSettings,
  UpdateTwilioAccountSettingsResponse,
  TwilioSettings,
  UpdateAccountPlaidSettingsResponse,
  LinkedAccount,
  GetLinkedAccountsResponse,
  GetLinkedAccountResponse,
  SaveProviderResponse,
  GetProviderResponse,
  HistoricalValuation,
  SystemReport,
  GetSystemReportResponse,
  GetUserAccountValuationByAssetTypeRequest,
  UserAccountValuationByAssetType,
  GetUserAccountValuationByAssetTypeResponse,
  LinkedAccountsValuation,
  GetLinkedAccountsHistoricalValuationRequest,
  GetLinkedAccountsHistoricalValuationResponse,
} from "./types";

function getEndpoint(): string {
  const endpoint = process.env.REACT_APP_FINBOT_SERVER_ENDPOINT;
  if (endpoint) {
    return endpoint;
  }
  return "http://127.0.0.1:5003/api/v1";
}

function handleResponse<T>(response: AxiosResponse): T {
  const payload = response.data;
  if (Object.prototype.hasOwnProperty.call(payload, "error")) {
    const error_metadata: FinbotErrorMetadata = payload.error;
    throw new FinbotClientError(error_metadata.user_message, error_metadata);
  }
  return payload;
}

export class FinbotClientError extends Error {
  metadata: FinbotErrorMetadata;

  constructor(user_message: string, metadata: FinbotErrorMetadata) {
    super(user_message);
    this.metadata = metadata;
  }
}

export class FinbotClient {
  endpoint: string;

  constructor() {
    this.endpoint = getEndpoint();
  }

  async getTraces({ guid }: GetTracesRequest): Promise<TracesTree> {
    const endpoint = `${this.endpoint}/admin/traces/${guid}?format=tree`;
    const response = await axios.get(endpoint);
    return handleResponse<GetTracesResponse>(response).tree;
  }

  async registerAccount({
    email,
    full_name,
    password,
    valuation_ccy,
  }: RegisterAccountRequest): Promise<UserAccount> {
    const settings = { valuation_ccy: valuation_ccy };
    const response = await axios.post(`${this.endpoint}/accounts`, {
      email,
      full_name,
      password,
      settings,
    });
    return handleResponse<RegisterAccountResponse>(response).user_account;
  }

  async logInAccount({
    email,
    password,
  }: LoginRequest): Promise<LoginResponse> {
    const response = await axios.post(`${this.endpoint}/auth/login`, {
      email,
      password,
    });
    return handleResponse<LoginResponse>(response);
  }

  async getUserAccount({
    account_id,
  }: GetUserAccountRequest): Promise<UserAccount> {
    const response = await axios.get(`${this.endpoint}/accounts/${account_id}`);
    return handleResponse<GetUserAccountResponse>(response).user_account;
  }

  async updateAccountProfile({
    account_id,
    full_name,
    email,
    mobile_phone_number,
  }: UpdateAccountProfileRequest): Promise<UserAccountProfile> {
    const response = await axios.put(
      `${this.endpoint}/accounts/${account_id}/profile`,
      {
        full_name,
        email,
        mobile_phone_number,
      }
    );
    return handleResponse<UpdateAccountProfileResponse>(response).profile;
  }

  async isAccountConfigured({
    account_id,
  }: IsAccountConfiguredRequest): Promise<boolean> {
    const response = await axios.get(
      `${this.endpoint}/accounts/${account_id}/is_configured`
    );
    return handleResponse<IsAccountConfiguredResponse>(response).configured;
  }

  async getAccountSettings({
    account_id,
  }: GetAccountSettingsRequest): Promise<UserAccountSettings> {
    const response = await axios.get(
      `${this.endpoint}/accounts/${account_id}/settings`
    );
    return handleResponse<GetAccountSettingsResponse>(response).settings;
  }

  async updateTwilioAccountSettings({
    account_id,
    twilio_settings,
  }: UpdateTwilioAccountSettingsRequest): Promise<TwilioSettings> {
    const response = await axios.put(
      `${this.endpoint}/accounts/${account_id}/settings`,
      { twilio_settings }
    );
    return handleResponse<UpdateTwilioAccountSettingsResponse>(response)
      .settings.twilio_settings;
  }

  async getAccountPlaidSettings({
    account_id,
  }: GetAccountPlaidSettingsRequest): Promise<PlaidSettings> {
    const response = await axios.get(
      `${this.endpoint}/accounts/${account_id}/settings/plaid`
    );
    return handleResponse<GetAccountPlaidSettingsResponse>(response)
      .plaid_settings;
  }

  async updateAccountPlaidSettings({
    account_id,
    env,
    client_id,
    public_key,
    secret_key,
  }: UpdateAccountPlaidSettingsRequest): Promise<PlaidSettings> {
    const response = await axios.post(
      `${this.endpoint}/accounts/${account_id}/settings/plaid`,
      {
        env,
        client_id,
        public_key,
        secret_key,
      }
    );
    return handleResponse<UpdateAccountPlaidSettingsResponse>(response)
      .plaid_settings;
  }

  async deleteAccountPlaidSettings({
    account_id,
  }: DeleteAccountPlaidSettingsRequest): Promise<void> {
    const response = await axios.delete(
      `${this.endpoint}/accounts/${account_id}/settings/plaid`
    );
    handleResponse(response);
  }

  async getAccountValuation({
    account_id,
  }: GetAccountValuationRequest): Promise<UserAccountValuation | null> {
    const response = await axios.get(
      `${this.endpoint}/accounts/${account_id}/valuation`
    );
    return handleResponse<GetAccountValuationResponse>(response).valuation;
  }

  async getAccountHistoricalValuation({
    account_id,
    from_time,
    to_time,
    frequency,
  }: GetAccountHistoricalValuationRequest): Promise<HistoricalValuation> {
    const params = {
      from_time: from_time?.toISO(),
      to_time: to_time?.toISO(),
      frequency: frequency,
    };
    const response = await axios.get(
      `${this.endpoint}/accounts/${account_id}/valuation/history`,
      { params }
    );
    return handleResponse<GetAccountHistoricalValuationResponse>(response)
      .historical_valuation;
  }

  async getAccountHistoricalValuationByAssetType({
    account_id,
    from_time,
    to_time,
    frequency,
  }: GetAccountHistoricalValuationRequest): Promise<HistoricalValuation> {
    const params = {
      from_time: from_time?.toISO(),
      to_time: to_time?.toISO(),
      frequency: frequency,
    };
    const response = await axios.get(
      `${this.endpoint}/accounts/${account_id}/valuation/history/by/asset_type`,
      { params }
    );
    return handleResponse<GetAccountHistoricalValuationResponse>(response)
      .historical_valuation;
  }

  async getLinkedAccountsValuation({
    account_id,
  }: GetLinkedAccountsValuationRequest): Promise<LinkedAccountsValuation> {
    const response = await axios.get(
      `${this.endpoint}/accounts/${account_id}/linked_accounts/valuation`
    );
    return handleResponse<GetLinkedAccountsValuationResponse>(response)
      .valuation;
  }

  async getLinkedAccountsHistoricalValuation({
    account_id,
    from_time,
    to_time,
    frequency,
  }: GetLinkedAccountsHistoricalValuationRequest): Promise<HistoricalValuation> {
    const params = {
      from_time: from_time?.toISO(),
      to_time: to_time?.toISO(),
      frequency: frequency,
    };
    const response = await axios.get(
      `${this.endpoint}/accounts/${account_id}/linked_accounts/valuation/history`,
      { params }
    );
    return handleResponse<GetLinkedAccountsHistoricalValuationResponse>(
      response
    ).historical_valuation;
  }

  async getUserAccountValuationByAssetType({
    account_id,
  }: GetUserAccountValuationByAssetTypeRequest): Promise<UserAccountValuationByAssetType> {
    const response = await axios.get(
      `${this.endpoint}/accounts/${account_id}/valuation/by/asset_type`
    );
    return handleResponse<GetUserAccountValuationByAssetTypeResponse>(response)
      .valuation;
  }

  async getLinkedAccounts({
    account_id,
  }: GetLinkedAccountsRequest): Promise<Array<LinkedAccount>> {
    const response = await axios.get(
      `${this.endpoint}/accounts/${account_id}/linked_accounts`
    );
    return handleResponse<GetLinkedAccountsResponse>(response).linked_accounts;
  }

  async getLinkedAccount({
    account_id,
    linked_account_id,
  }: GetLinkedAccountRequest): Promise<LinkedAccount> {
    const response = await axios.get(
      `${this.endpoint}/accounts/${account_id}/linked_accounts/${linked_account_id}`
    );
    return handleResponse<GetLinkedAccountResponse>(response).linked_account;
  }

  async updateLinkedAccountMetadata({
    account_id,
    linked_account_id,
    account_name,
  }: UpdateLinkedAccountMetadata): Promise<void> {
    const response = await axios.put(
      `${this.endpoint}/accounts/${account_id}/linked_accounts/${linked_account_id}/metadata`,
      {
        account_name,
      }
    );
    return handleResponse(response);
  }

  async updateLinkedAccountCredentials({
    account_id,
    linked_account_id,
    validate,
    persist,
    credentials,
  }: UpdateLinkedAccountCredentials): Promise<void> {
    const response = await axios.put(
      `${
        this.endpoint
      }/accounts/${account_id}/linked_accounts/${linked_account_id}/credentials?validate=${
        validate ?? 0
      }&persist=${persist ?? 0}`,
      {
        credentials,
      }
    );
    return handleResponse(response);
  }

  async deleteLinkedAccount({
    account_id,
    linked_account_id,
  }: DeleteLinkedAccountRequest): Promise<void> {
    const response = await axios.delete(
      `${this.endpoint}/accounts/${account_id}/linked_accounts/${linked_account_id}`
    );
    handleResponse(response);
  }

  async getProviders(): Promise<Array<Provider>> {
    const response = await axios.get(`${this.endpoint}/providers`);
    return handleResponse<GetProvidersResponse>(response).providers;
  }

  async saveProvider(provider: SaveProviderRequest): Promise<Provider> {
    const response = await axios.put(`${this.endpoint}/providers`, provider);
    return handleResponse<SaveProviderResponse>(response).provider;
  }

  async deleteProvider({ provider_id }: DeleteProviderRequest): Promise<void> {
    const response = await axios.delete(
      `${this.endpoint}/providers/${provider_id}`
    );
    handleResponse(response);
  }

  async getProvider({ provider_id }: GetProviderRequest): Promise<Provider> {
    const response = await axios.get(
      `${this.endpoint}/providers/${provider_id}`
    );
    return handleResponse<GetProviderResponse>(response).provider;
  }

  async validateLinkedAccountCredentials({
    account_id,
    provider_id,
    credentials,
    account_name,
  }: ValidateLinkedAccountCredentialsRequest): Promise<void> {
    const response = await axios.post(
      `${this.endpoint}/accounts/${account_id}/linked_accounts?persist=0`,
      { provider_id, credentials, account_name }
    );
    handleResponse<void>(response);
  }

  async linkAccount({
    account_id,
    provider_id,
    credentials,
    account_name,
  }: LinkAccountRequest): Promise<void> {
    const response = await axios.post(
      `${this.endpoint}/accounts/${account_id}/linked_accounts?validate=0`,
      { provider_id, credentials, account_name }
    );
    handleResponse<void>(response);
  }

  async getHoldingsReport(): Promise<HoldingsReport> {
    const response = await axios.get(`${this.endpoint}/reports/holdings`);
    return handleResponse<ReportResponse<HoldingsReport>>(response).report;
  }

  async getEarningsReport(): Promise<EarningsReport> {
    const response = await axios.get(`${this.endpoint}/reports/earnings`);
    return handleResponse<ReportResponse<EarningsReport>>(response).report;
  }

  async getSystemReport(): Promise<SystemReport> {
    const response = await axios.get(`${this.endpoint}/system_report`);
    return handleResponse<GetSystemReportResponse>(response).system_report;
  }
}
