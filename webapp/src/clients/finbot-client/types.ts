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

export interface UserAccountProfile {
  full_name: string;
  email: string;
  mobile_phone_number: string | null;
}

export interface UpdateAccountProfileRequest
  extends UserAccountResource,
    UserAccountProfile {}

export interface UpdateAccountProfileResponse {
  profile: UserAccountProfile;
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
  twilio_settings: TwilioSettings | null;
}

export interface GetAccountPlaidSettingsRequest extends UserAccountResource {}

export interface PlaidSettings {
  env: string;
  client_id: string;
  public_key: string;
  secret_key: string;
}

export interface GetAccountPlaidSettingsResponse {
  plaid_settings: PlaidSettings;
}

export interface UpdateAccountPlaidSettingsRequest
  extends UserAccountResource,
    PlaidSettings {}

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

export type LinkedAccountCredentials = Record<string, unknown>;

export interface LinkedAccountStatusErrorEntry {
  scope: string;
  error: FinbotErrorMetadata;
}

export interface LinkedAccountStatus {
  status: "stable" | "unstable";
  errors: Array<LinkedAccountStatusErrorEntry>;
}

export interface LinkedAccount {
  id: number;
  user_account_id: number;
  provider_id: string;
  account_name: string;
  credentials: LinkedAccountCredentials | null;
  deleted: boolean;
  status: LinkedAccountStatus | null;
  provider: Provider;
}

export interface ProviderResource {
  provider_id: string;
}

export interface LinkAccountRequest
  extends UserAccountResource,
    ProviderResource {
  credentials: LinkedAccountCredentials | null;
  account_name: string;
}

export interface ValidateLinkedAccountCredentialsRequest
  extends LinkAccountRequest {}

export interface GetLinkedAccountRequest extends LinkedAccountResource {}

export interface UpdateLinkedAccountMetadata extends LinkedAccountResource {
  linked_account_id: number;
  account_name: string;
}

export interface UpdateLinkedAccountCredentials extends LinkedAccountResource {
  credentials: LinkedAccountCredentials | null;
  validate?: boolean;
  persist?: boolean;
}

export interface DeleteLinkedAccountRequest extends LinkedAccountResource {}

export interface Provider {
  id: string;
  description: string;
  website_url: string;
  credentials_schema: Record<string, unknown>;
}

export interface GetProvidersResponse {
  providers: Array<Provider>;
}

export interface GetProviderRequest extends ProviderResource {}

export interface SaveProviderRequest extends Provider {}

export interface DeleteProviderRequest extends ProviderResource {}

export interface EarningsReportAggregation {
  as_str: string;
}

export interface EarningsReportMetrics {
  first_date: string;
  first_value: number;
  last_date: string;
  last_value: number;
  min_value: number;
  max_value: number;
  abs_change: number;
  rel_change: number;
}

export interface EarningsReportEntry {
  aggregation: EarningsReportAggregation;
  metrics: EarningsReportMetrics;
}

export interface EarningsReport {
  currency: string;
  entries: Array<EarningsReportEntry>;
  rollup: EarningsReportMetrics;
}

export interface ReportResponse<ReportType> {
  report: ReportType;
}
