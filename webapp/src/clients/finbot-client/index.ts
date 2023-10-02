import axios, { AxiosInstance, AxiosResponse } from "axios";

import {
  DeleteLinkedAccountRequest,
  DeleteProviderRequest,
  EarningsReport,
  FinbotErrorMetadata,
  GetAccountHistoricalValuationRequest,
  GetAccountHistoricalValuationResponse,
  GetAccountSettingsRequest,
  GetAccountValuationRequest,
  GetAccountValuationResponse,
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
  UpdateAccountProfileRequest,
  UpdateAccountProfileResponse,
  UpdateLinkedAccountCredentials,
  UpdateLinkedAccountMetadata,
  UpdateTwilioAccountSettingsRequest,
  UserAccount,
  UserAccountProfile,
  UserAccountValuation,
  ValidateLinkedAccountCredentialsRequest,
  RegisterAccountResponse,
  GetAccountSettingsResponse,
  UserAccountSettings,
  UpdateTwilioAccountSettingsResponse,
  TwilioSettings,
  LinkedAccount,
  GetPlaidSettingsResponse,
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
  UpdateUserAccountPasswordRequest,
  IsEmailAvailableResponse,
  EmailDeliverySettings,
  GetEmailDeliverySettingsResponse,
  EmailDeliveryProvider,
  GetEmailDeliveryProvidersResponse,
} from "./types";
import { FINBOT_SERVER_ENDPOINT } from "utils/env-config";

const DEFAULT_FINBOT_SERVER_ENDPOINT = "http://127.0.0.1:5003/api/v1";

function getEndpoint(): string {
  return FINBOT_SERVER_ENDPOINT ?? DEFAULT_FINBOT_SERVER_ENDPOINT;
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
  axiosInstance: AxiosInstance;

  constructor() {
    this.axiosInstance = axios.create({
      baseURL: getEndpoint(),
    });
  }

  async registerAccount({
    email,
    full_name,
    password,
    valuation_ccy,
  }: RegisterAccountRequest): Promise<UserAccount> {
    const settings = { valuation_ccy };
    const response = await this.axiosInstance.post(`/accounts/`, {
      email,
      full_name,
      password,
      settings,
    });
    return handleResponse<RegisterAccountResponse>(response).user_account;
  }

  async isEmailAvailable(email: string): Promise<boolean> {
    const params = { email };
    const response = await this.axiosInstance.get(
      `/accounts/email_available/`,
      {
        params,
      }
    );
    return handleResponse<IsEmailAvailableResponse>(response).available;
  }

  async logInAccount({
    email,
    password,
  }: LoginRequest): Promise<LoginResponse> {
    const response = await this.axiosInstance.post(`/auth/login/`, {
      email,
      password,
    });
    return handleResponse<LoginResponse>(response);
  }

  async getUserAccount({
    account_id,
  }: GetUserAccountRequest): Promise<UserAccount> {
    const response = await this.axiosInstance.get(`/accounts/${account_id}/`);
    return handleResponse<GetUserAccountResponse>(response).user_account;
  }

  async updateUserAccountPassword({
    account_id,
    old_password,
    new_password,
  }: UpdateUserAccountPasswordRequest): Promise<void> {
    const response = await this.axiosInstance.put(
      `/accounts/${account_id}/password/`,
      {
        old_password,
        new_password,
      }
    );
    return handleResponse<void>(response);
  }

  async updateAccountProfile({
    account_id,
    full_name,
    email,
    mobile_phone_number,
  }: UpdateAccountProfileRequest): Promise<UserAccountProfile> {
    const response = await this.axiosInstance.put(
      `/accounts/${account_id}/profile/`,
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
    const response = await this.axiosInstance.get(
      `/accounts/${account_id}/is_configured/`
    );
    return handleResponse<IsAccountConfiguredResponse>(response).configured;
  }

  async getAccountSettings({
    account_id,
  }: GetAccountSettingsRequest): Promise<UserAccountSettings> {
    const response = await this.axiosInstance.get(
      `/accounts/${account_id}/settings/`
    );
    return handleResponse<GetAccountSettingsResponse>(response).settings;
  }

  async updateTwilioAccountSettings({
    account_id,
    twilio_settings,
  }: UpdateTwilioAccountSettingsRequest): Promise<TwilioSettings> {
    const response = await this.axiosInstance.put(
      `/accounts/${account_id}/settings/`,
      { twilio_settings }
    );
    return handleResponse<UpdateTwilioAccountSettingsResponse>(response)
      .settings.twilio_settings;
  }

  async getPlaidSettings(): Promise<PlaidSettings | null> {
    const response = await this.axiosInstance.get(`/admin/plaid/settings/`);
    return handleResponse<GetPlaidSettingsResponse>(response).settings;
  }

  async getAccountValuation({
    account_id,
  }: GetAccountValuationRequest): Promise<UserAccountValuation | null> {
    const response = await this.axiosInstance.get(
      `/accounts/${account_id}/valuation/`
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
    const response = await this.axiosInstance.get(
      `/accounts/${account_id}/valuation/history/`,
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
    const response = await this.axiosInstance.get(
      `/accounts/${account_id}/valuation/history/by/asset_type/`,
      { params }
    );
    return handleResponse<GetAccountHistoricalValuationResponse>(response)
      .historical_valuation;
  }

  async getLinkedAccountsValuation({
    account_id,
  }: GetLinkedAccountsValuationRequest): Promise<LinkedAccountsValuation> {
    const response = await this.axiosInstance.get(
      `/accounts/${account_id}/linked_accounts/valuation/`
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
    const response = await this.axiosInstance.get(
      `/accounts/${account_id}/linked_accounts/valuation/history/`,
      { params }
    );
    return handleResponse<GetLinkedAccountsHistoricalValuationResponse>(
      response
    ).historical_valuation;
  }

  async getUserAccountValuationByAssetType({
    account_id,
  }: GetUserAccountValuationByAssetTypeRequest): Promise<UserAccountValuationByAssetType> {
    const response = await this.axiosInstance.get(
      `/accounts/${account_id}/valuation/by/asset_type/`
    );
    return handleResponse<GetUserAccountValuationByAssetTypeResponse>(response)
      .valuation;
  }

  async getLinkedAccounts({
    account_id,
  }: GetLinkedAccountsRequest): Promise<Array<LinkedAccount>> {
    const response = await this.axiosInstance.get(
      `/accounts/${account_id}/linked_accounts/`
    );
    return handleResponse<GetLinkedAccountsResponse>(response).linked_accounts;
  }

  async getLinkedAccount({
    account_id,
    linked_account_id,
  }: GetLinkedAccountRequest): Promise<LinkedAccount> {
    const response = await this.axiosInstance.get(
      `/accounts/${account_id}/linked_accounts/${linked_account_id}/`
    );
    return handleResponse<GetLinkedAccountResponse>(response).linked_account;
  }

  async updateLinkedAccountMetadata({
    account_id,
    linked_account_id,
    account_name,
    frozen,
  }: UpdateLinkedAccountMetadata): Promise<void> {
    const response = await this.axiosInstance.put(
      `/accounts/${account_id}/linked_accounts/${linked_account_id}/metadata/`,
      {
        account_name,
        frozen,
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
    const response = await this.axiosInstance.put(
      `/accounts/${account_id}/linked_accounts/${linked_account_id}/credentials/?validate=${
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
    const response = await this.axiosInstance.delete(
      `/accounts/${account_id}/linked_accounts/${linked_account_id}/`
    );
    handleResponse(response);
  }

  async getProviders(): Promise<Array<Provider>> {
    const response = await this.axiosInstance.get(`/providers/`);
    return handleResponse<GetProvidersResponse>(response).providers;
  }

  async saveProvider(provider: SaveProviderRequest): Promise<Provider> {
    const response = await this.axiosInstance.put(`/providers/`, provider);
    return handleResponse<SaveProviderResponse>(response).provider;
  }

  async deleteProvider({ provider_id }: DeleteProviderRequest): Promise<void> {
    const response = await this.axiosInstance.delete(
      `/providers/${provider_id}/`
    );
    handleResponse(response);
  }

  async getProvider({ provider_id }: GetProviderRequest): Promise<Provider> {
    const response = await this.axiosInstance.get(`/providers/${provider_id}/`);
    return handleResponse<GetProviderResponse>(response).provider;
  }

  async validateLinkedAccountCredentials({
    account_id,
    provider_id,
    credentials,
    account_name,
  }: ValidateLinkedAccountCredentialsRequest): Promise<void> {
    const response = await this.axiosInstance.post(
      `/accounts/${account_id}/linked_accounts/?persist=0`,
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
    const response = await this.axiosInstance.post(
      `/accounts/${account_id}/linked_accounts/?validate=0`,
      { provider_id, credentials, account_name }
    );
    handleResponse<void>(response);
  }

  async getHoldingsReport(): Promise<HoldingsReport> {
    const response = await this.axiosInstance.get(`/reports/holdings/`);
    return handleResponse<ReportResponse<HoldingsReport>>(response).report;
  }

  async getEarningsReport(): Promise<EarningsReport> {
    const response = await this.axiosInstance.get(`/reports/earnings/`);
    return handleResponse<ReportResponse<EarningsReport>>(response).report;
  }

  async getSystemReport(): Promise<SystemReport> {
    const response = await this.axiosInstance.get(`/system_report/`);
    return handleResponse<GetSystemReportResponse>(response).system_report;
  }

  async getEmailDeliveryProviders(): Promise<Array<EmailDeliveryProvider>> {
    const response = await this.axiosInstance.get(
      `/admin/settings/email_delivery/providers/`
    );
    return handleResponse<GetEmailDeliveryProvidersResponse>(response)
      .providers;
  }

  async getEmailDeliverySettings(): Promise<EmailDeliverySettings | null> {
    const response = await this.axiosInstance.get(
      `/admin/settings/email_delivery/`
    );
    return handleResponse<GetEmailDeliverySettingsResponse>(response).settings;
  }

  async setEmailDeliverySettings(
    settings: EmailDeliverySettings,
    validate?: boolean
  ): Promise<void> {
    const params = { validate: validate ?? false };
    const response = await this.axiosInstance.put(
      `/admin/settings/email_delivery/`,
      settings,
      { params }
    );
    return handleResponse<void>(response);
  }

  async disableEmailDelivery(): Promise<void> {
    const response = await this.axiosInstance.delete(
      `/admin/settings/email_delivery/`
    );
    return handleResponse<void>(response);
  }
}
