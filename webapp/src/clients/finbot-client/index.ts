import axios, { AxiosResponse } from "axios";

import {
  DeleteAccountPlaidSettingsRequest,
  DeleteLinkedAccountRequest,
  DeleteProviderRequest,
  EarningsReport,
  FinbotErrorMetadata,
  GetAccountHistoricalValuationRequest,
  GetAccountPlaidSettingsRequest,
  GetAccountPlaidSettingsResponse,
  GetAccountSettingsRequest,
  GetAccountValuationRequest,
  GetGuidRequest,
  GetLinkedAccountRequest,
  GetLinkedAccountsRequest,
  GetLinkedAccountsValuationRequest,
  GetProviderRequest,
  GetProvidersResponse,
  GetUserAccountRequest,
  GetUserAccountResponse,
  IsAccountConfiguredRequest,
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
  ValidateLinkedAccountCredentialsRequest,
} from "./types";

function getEndpoint(): string {
  const endpoint = process.env.REACT_APP_FINBOT_SERVER_ENDPOINT;
  if (endpoint) {
    return endpoint;
  }
  return "http://127.0.0.1:5003/api/v1";
}

function handleResponse<T = any>(response: AxiosResponse): T {
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

  async getTraces({ guid }: GetGuidRequest) {
    const endpoint = `${this.endpoint}/admin/traces/${guid}?format=tree`;
    const response = await axios.get(endpoint);
    return handleResponse(response);
  }

  async registerAccount({
    email,
    full_name,
    password,
    valuation_ccy,
  }: RegisterAccountRequest) {
    const settings = { valuation_ccy: valuation_ccy };
    const response = await axios.post(`${this.endpoint}/accounts`, {
      email,
      full_name,
      password,
      settings,
    });
    return handleResponse(response);
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

  async getAccountValuation({ account_id }: GetAccountValuationRequest) {
    const response = await axios.get(
      `${this.endpoint}/accounts/${account_id}/valuation`
    );
    return handleResponse(response).valuation;
  }

  async isAccountConfigured({ account_id }: IsAccountConfiguredRequest) {
    const response = await axios.get(
      `${this.endpoint}/accounts/${account_id}/is_configured`
    );
    return handleResponse(response).configured;
  }

  async getAccountSettings({ account_id }: GetAccountSettingsRequest) {
    const response = await axios.get(
      `${this.endpoint}/accounts/${account_id}/settings`
    );
    return handleResponse(response).settings;
  }

  async updateTwilioAccountSettings({
    account_id,
    twilio_settings,
  }: UpdateTwilioAccountSettingsRequest) {
    const response = await axios.put(
      `${this.endpoint}/accounts/${account_id}/settings`,
      { twilio_settings }
    );
    return handleResponse(response).settings;
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
  }: UpdateAccountPlaidSettingsRequest) {
    const response = await axios.post(
      `${this.endpoint}/accounts/${account_id}/settings/plaid`,
      {
        env,
        client_id,
        public_key,
        secret_key,
      }
    );
    return handleResponse(response).plaid_settings;
  }

  async deleteAccountPlaidSettings({
    account_id,
  }: DeleteAccountPlaidSettingsRequest) {
    const response = await axios.delete(
      `${this.endpoint}/accounts/${account_id}/settings/plaid`
    );
    return handleResponse(response);
  }

  async getAccountHistoricalValuation({
    account_id,
  }: GetAccountHistoricalValuationRequest) {
    const response = await axios.get(
      `${this.endpoint}/accounts/${account_id}/history`
    );
    return handleResponse(response).historical_valuation;
  }

  async getLinkedAccounts({ account_id }: GetLinkedAccountsRequest) {
    const response = await axios.get(
      `${this.endpoint}/accounts/${account_id}/linked_accounts`
    );
    return handleResponse(response).linked_accounts;
  }

  async getLinkedAccount({
    account_id,
    linked_account_id,
  }: GetLinkedAccountRequest) {
    const response = await axios.get(
      `${this.endpoint}/accounts/${account_id}/linked_accounts/${linked_account_id}`
    );
    return handleResponse(response).linked_account;
  }

  async getLinkedAccountsValuation({
    account_id,
  }: GetLinkedAccountsValuationRequest) {
    const response = await axios.get(
      `${this.endpoint}/accounts/${account_id}/linked_accounts/valuation`
    );
    return handleResponse(response).linked_accounts;
  }

  async updateLinkedAccountMetadata({
    account_id,
    linked_account_id,
    account_name,
  }: UpdateLinkedAccountMetadata) {
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
  }: UpdateLinkedAccountCredentials) {
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
  }: DeleteLinkedAccountRequest) {
    const response = await axios.delete(
      `${this.endpoint}/accounts/${account_id}/linked_accounts/${linked_account_id}`
    );
    return handleResponse(response);
  }

  async getProviders(): Promise<Array<Provider>> {
    const response = await axios.get(`${this.endpoint}/providers`);
    return handleResponse<GetProvidersResponse>(response).providers;
  }

  async saveProvider(provider: SaveProviderRequest) {
    const response = await axios.put(`${this.endpoint}/providers`, provider);
    return handleResponse(response);
  }

  async deleteProvider({ provider_id }: DeleteProviderRequest) {
    const response = await axios.delete(
      `${this.endpoint}/providers/${provider_id}`
    );
    return handleResponse(response);
  }

  async getProvider({ provider_id }: GetProviderRequest) {
    const response = await axios.get(
      `${this.endpoint}/providers/${provider_id}`
    );
    return handleResponse(response);
  }

  async validateLinkedAccountCredentials({
    account_id,
    provider_id,
    credentials,
    account_name,
  }: ValidateLinkedAccountCredentialsRequest) {
    const response = await axios.post(
      `${this.endpoint}/accounts/${account_id}/linked_accounts?persist=0`,
      { provider_id, credentials, account_name }
    );
    return handleResponse(response).result.validated;
  }

  async linkAccount({
    account_id,
    provider_id,
    credentials,
    account_name,
  }: LinkAccountRequest) {
    const response = await axios.post(
      `${this.endpoint}/accounts/${account_id}/linked_accounts?validate=0`,
      { provider_id, credentials, account_name }
    );
    return handleResponse(response).result;
  }

  async getHoldingsReport() {
    const response = await axios.get(`${this.endpoint}/reports/holdings`);
    return handleResponse(response).report;
  }

  async getEarningsReport(): Promise<EarningsReport> {
    const response = await axios.get(`${this.endpoint}/reports/earnings`);
    return handleResponse<ReportResponse<EarningsReport>>(response).report;
  }
}
