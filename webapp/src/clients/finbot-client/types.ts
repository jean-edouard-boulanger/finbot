export interface DistributedTraceKey {
  guid: string;
  path: string;
}

export interface FinbotErrorMetadata {
  user_message: string;
  debug_message: string | null;
  error_code: string | null;
  exception_type: string | null;
  trace: string | null;
  distributed_trace_key: DistributedTraceKey | null;
}

export interface GetGuidRequest {
  guid: string;
}

export interface RegisterAccountRequest {
  email: string;
  full_name: string;
  password: string;
  valuation_ccy: string;
}

export interface Credentials {
  email: string;
  password: string;
}

export interface LoginRequest extends Credentials {}

export interface Auth {
  access_token: string;
  refresh_token: string;
}

export interface LoginResponse {
  auth: Auth;
  account: UserAccount;
}

export interface UserAccountResource {
  account_id: number;
}

export interface GetUserAccountRequest extends UserAccountResource {}

export interface UserAccount {
  id: number;
  email: string;
  full_name: string;
  mobile_phone_number: string;
}

export interface GetUserAccountResponse {
  user_account: UserAccount;
}

export interface UpdateAccountProfileRequest extends UserAccountResource {
  full_name: string;
  email: string;
  mobile_phone_number: string;
}

export interface GetAccountValuationRequest extends UserAccountResource {}

export interface IsAccountConfiguredRequest extends UserAccountResource {}

export interface GetAccountSettingsRequest extends UserAccountResource {}

export interface TwilioSettings {
  account_sid: string;
  auth_token: string;
  phone_number: string;
}

export interface UpdateTwilioAccountSettingsRequest
  extends UserAccountResource {
  twilio_settings: TwilioSettings;
}

export interface GetAccountPlaidSettingsRequest extends UserAccountResource {}

export interface UpdateAccountPlaidSettingsRequest extends UserAccountResource {
  env: string;
  client_id: string;
  public_key: string;
  secret_key: string;
}

export interface GetAccountHistoricalValuationRequest
  extends UserAccountResource {}

export interface DeleteAccountPlaidSettingsRequest
  extends UserAccountResource {}

export interface GetLinkedAccountsRequest extends UserAccountResource {}

export interface GetLinkedAccountsValuationRequest
  extends UserAccountResource {}

export interface LinkedAccountResource extends UserAccountResource {
  linked_account_id: number;
}

export interface ProviderResource {
  provider_id: string;
}

export interface LinkAccountRequest
  extends UserAccountResource,
    ProviderResource {
  credentials: Record<string, unknown> | null;
  account_name: string;
}

export interface ValidateLinkedAccountCredentialsRequest
  extends LinkAccountRequest {
  credentials: Record<string, unknown> | null;
  account_name: string;
}

export interface GetLinkedAccountRequest extends LinkedAccountResource {}

export interface UpdateLinkedAccountMetadata extends LinkedAccountResource {
  linked_account_id: number;
  account_name: string;
}

export interface UpdateLinkedAccountCredentials extends LinkedAccountResource {
  credentials: Record<string, unknown> | null;
  validate?: boolean;
  persist?: boolean;
}

export interface DeleteLinkedAccountRequest extends LinkedAccountResource {}

export interface GetProviderRequest extends ProviderResource {}

export interface SaveProviderRequest extends ProviderResource {
  description: string;
  website_url: string;
  credentials_schema: Record<string, unknown>;
}

export interface DeleteProviderRequest extends ProviderResource {}
