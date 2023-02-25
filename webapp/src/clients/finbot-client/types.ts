import { DateTime } from "luxon";

export interface SeriesXAxisData {
  type: "datetime" | "category";
  categories: Array<string | number>;
}

export interface SeriesYAxisData {
  name: string;
  data: Array<number>;
}

export interface SeriesData {
  x_axis: SeriesXAxisData;
  series: Array<SeriesYAxisData>;
}

export interface DistributedTraceKey {
  guid: string;
  path: string;
}

export interface TimeRange {
  from_time?: DateTime | null;
  to_time?: DateTime | null;
}

export interface FinbotErrorMetadata {
  user_message: string;
  debug_message: string | null;
  error_code: string | null;
  exception_type: string | null;
  trace: string | null;
  distributed_trace_key: DistributedTraceKey | null;
}

export interface GetTracesRequest {
  guid: string;
}

export interface TracesTreeNodeData {
  path: string;
  name: string;
  metadata: Record<string, any>;
  start_time: string;
  end_time: string;
}

export interface TracesTreeNode {
  children: Array<TracesTreeNode>;
  data: TracesTreeNodeData;
  extra_properties: Record<string, any>;
}

export type TracesTree = TracesTreeNode;

export interface GetTracesResponse {
  tree: TracesTree;
}

export interface RegisterAccountRequest {
  email: string;
  full_name: string;
  password: string;
  valuation_ccy: string;
}

export interface IsEmailAvailableResponse {
  available: boolean;
}

export interface RegisterAccountResponse {
  user_account: UserAccount;
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

export interface UpdateUserAccountPasswordRequest extends UserAccountResource {
  old_password: string;
  new_password: string;
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

export interface UserAccountValuation {
  history_entry_id: number;
  date: string;
  currency: string;
  value: number;
  total_liabilities: number;
  change: ValuationChange;
  sparkline: Array<number>;
}

export interface GetAccountValuationResponse {
  valuation: UserAccountValuation | null;
}

export interface IsAccountConfiguredRequest extends UserAccountResource {}

export interface IsAccountConfiguredResponse {
  configured: boolean;
}

export interface GetAccountSettingsRequest extends UserAccountResource {}

export interface UserAccountSettings {
  valuation_ccy: string;
  twilio_settings: TwilioSettings;
}

export interface GetAccountSettingsResponse {
  settings: UserAccountSettings;
}

export interface TwilioSettings {
  account_sid: string;
  auth_token: string;
  phone_number: string;
}

export interface UpdateTwilioAccountSettingsRequest
  extends UserAccountResource {
  twilio_settings: TwilioSettings | null;
}

export interface UpdateTwilioAccountSettingsResponse {
  settings: UserAccountSettings;
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

export interface UpdateAccountPlaidSettingsResponse {
  plaid_settings: PlaidSettings;
}

export interface GetAccountHistoricalValuationRequest
  extends UserAccountResource,
    TimeRange {
  frequency?: string;
}

export interface HistoricalValuation {
  valuation_ccy: string;
  series_data: SeriesData;
}

export interface GetAccountHistoricalValuationResponse {
  historical_valuation: HistoricalValuation;
}

export interface DeleteAccountPlaidSettingsRequest
  extends UserAccountResource {}

export interface GetLinkedAccountsRequest extends UserAccountResource {}

export interface GetLinkedAccountsResponse {
  linked_accounts: Array<LinkedAccount>;
}

export interface GetLinkedAccountsValuationRequest
  extends UserAccountResource {}

export interface LinkedAccountValuation {
  date: string;
  currency: string;
  value: number;
  change: ValuationChange;
}

export interface LinkedAccountsValuationEntry {
  linked_account: LinkedAccount;
  valuation: LinkedAccountValuation;
}

export interface LinkedAccountsValuation {
  valuation_ccy: string;
  entries: Array<LinkedAccountsValuationEntry>;
}

export interface GetLinkedAccountsValuationResponse {
  valuation: LinkedAccountsValuation;
}

export interface GetLinkedAccountsHistoricalValuationRequest
  extends UserAccountResource,
    TimeRange {
  frequency?: string;
}

export interface GetLinkedAccountsHistoricalValuationResponse {
  historical_valuation: HistoricalValuation;
}

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
  description: string;
  deleted: boolean;
  frozen: boolean;
  status: LinkedAccountStatus | null;
  credentials?: LinkedAccountCredentials | null;
  provider?: Provider;
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

export interface GetLinkedAccountResponse {
  linked_account: LinkedAccount;
}

export interface UpdateLinkedAccountMetadata extends LinkedAccountResource {
  linked_account_id: number;
  account_name?: string;
  frozen?: boolean;
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

export interface GetProviderResponse {
  provider: Provider;
}

export interface SaveProviderRequest extends Provider {}

export interface SaveProviderResponse {
  provider: Provider;
}

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

export interface ValuationChange {
  change_1hour: number;
  change_1day: number;
  change_1week: number;
  change_1month: number;
  change_6months: number;
  change_1year: number;
  change_2years: number;
}

export interface GetUserAccountValuationByAssetTypeRequest
  extends UserAccountResource {}

export interface UserAccountValuationByAssetType {
  valuation_ccy: string;
  by_asset_type: Record<string, number>;
}

export interface GetUserAccountValuationByAssetTypeResponse {
  valuation: UserAccountValuationByAssetType;
}

export interface HoldingsReportValuation {
  currency: string;
  value: number;
  change: ValuationChange;
  units?: number;
  sparkline?: Array<number>;
}

export interface HoldingsReportNodeBase<
  Role extends string,
  ChildType = never
> {
  role: Role;
  children?: Array<ChildType>;
}

export interface HoldingsReportValuationNode {
  valuation: HoldingsReportValuation;
}

export type HoldingsReportMetadataNode = HoldingsReportNodeBase<"metadata"> & {
  label: string;
  value: any;
};

export interface HoldingsReportItem {
  name: string;
  type: string;
  sub_type: string;
}

export type HoldingsReportItemNode = HoldingsReportNodeBase<
  "item",
  HoldingsReportMetadataNode
> &
  HoldingsReportValuationNode & { item: HoldingsReportItem };

export interface HoldingsReportSubAccount {
  id: string;
  currency: string;
  description: string;
  type: string;
}

export type HoldingsReportSubAccountNode = HoldingsReportNodeBase<
  "sub_account",
  HoldingsReportItemNode
> &
  HoldingsReportValuationNode & { sub_account: HoldingsReportSubAccount };

export interface HoldingsReportLinkedAccount {
  id: string;
  provider_id: string;
  description: string;
}

export type HoldingsReportLinkedAccountNode = HoldingsReportNodeBase<
  "linked_account",
  HoldingsReportSubAccountNode
> &
  HoldingsReportValuationNode & { linked_account: HoldingsReportLinkedAccount };

export type HoldingsReportUserAccountNode = HoldingsReportNodeBase<
  "user_account",
  HoldingsReportLinkedAccountNode
> &
  HoldingsReportValuationNode;

export type HoldingsReportNode =
  | HoldingsReportMetadataNode
  | HoldingsReportItemNode
  | HoldingsReportSubAccountNode
  | HoldingsReportLinkedAccountNode
  | HoldingsReportUserAccountNode;

export interface HoldingsReport {
  valuation_tree: HoldingsReportUserAccountNode;
}

export interface ReportResponse<ReportType> {
  report: ReportType;
}

export interface SystemReport {
  finbot_version: string;
  runtime: "development" | "production";
}

export interface GetSystemReportResponse {
  system_report: SystemReport;
}

export interface EmailDeliveryProviderSchema {
  settings_schema: any;
  ui_schema?: any;
}

export interface EmailDeliveryProvider {
  provider_id: string;
  description: string;
  schema: EmailDeliveryProviderSchema;
}

export interface GetEmailDeliveryProvidersResponse {
  providers: Array<EmailDeliveryProvider>;
}

export interface EmailDeliverySettings {
  subject_prefix: string;
  sender_name: string;
  provider_id: string;
  provider_settings: any;
}

export interface GetEmailDeliverySettingsResponse {
  settings: EmailDeliverySettings | null;
}
