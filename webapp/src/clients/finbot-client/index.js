import axios from "axios";

function getEndpoint() {
  const endpoint = process.env.REACT_APP_FINBOT_SERVER_ENDPOINT;
  if (endpoint !== undefined) {
    return endpoint;
  }
  return "http://127.0.0.1:5003/api/v1";
}

class FinbotClient {
  constructor() {
    this.endpoint = getEndpoint();
  }

  handleResponse(response) {
    const app_data = response.data;
    if (Object.prototype.hasOwnProperty.call(app_data, "error")) {
      throw app_data.error.debug_message;
    }
    return app_data;
  }

  async getTraces({ guid }) {
    const endpoint = `${this.endpoint}/admin/traces/${guid}?format=tree`;
    const response = await axios.get(endpoint);
    return this.handleResponse(response);
  }

  async registerAccount({ email, full_name, password, valuation_ccy }) {
    const settings = { valuation_ccy: valuation_ccy };
    const response = await axios.post(`${this.endpoint}/accounts`, {
      email,
      full_name,
      password,
      settings,
    });
    return this.handleResponse(response);
  }

  async logInAccount({ email, password }) {
    const response = await axios.post(`${this.endpoint}/auth/login`, {
      email,
      password,
    });
    return this.handleResponse(response);
  }

  async getAccount({ account_id }) {
    const response = await axios.get(`${this.endpoint}/accounts/${account_id}`);
    return this.handleResponse(response).user_account;
  }

  async updateAccountProfile({
    account_id,
    full_name,
    email,
    mobile_phone_number,
  }) {
    const response = await axios.put(
      `${this.endpoint}/accounts/${account_id}/profile`,
      {
        full_name,
        email,
        mobile_phone_number,
      }
    );
    return this.handleResponse(response).user_account;
  }

  async getAccountValuation({ account_id }) {
    const response = await axios.get(
      `${this.endpoint}/accounts/${account_id}/valuation`
    );
    return this.handleResponse(response).valuation;
  }

  async isAccountConfigured({ account_id }) {
    const response = await axios.get(
      `${this.endpoint}/accounts/${account_id}/is_configured`
    );
    return this.handleResponse(response).configured;
  }

  async getAccountSettings({ account_id }) {
    const response = await axios.get(
      `${this.endpoint}/accounts/${account_id}/settings`
    );
    return this.handleResponse(response).settings;
  }

  async updateTwilioAccountSettings({ account_id, twilio_settings }) {
    const response = await axios.put(
      `${this.endpoint}/accounts/${account_id}/settings`,
      { twilio_settings }
    );
    return this.handleResponse(response).settings;
  }

  async getAccountPlaidSettings({ account_id }) {
    const response = await axios.get(
      `${this.endpoint}/accounts/${account_id}/settings/plaid`
    );
    return this.handleResponse(response).plaid_settings;
  }

  async updateAccountPlaidSettings({
    account_id,
    env,
    client_id,
    public_key,
    secret_key,
  }) {
    const response = await axios.post(
      `${this.endpoint}/accounts/${account_id}/settings/plaid`,
      {
        env,
        client_id,
        public_key,
        secret_key,
      }
    );
    return this.handleResponse(response).plaid_settings;
  }

  async deleteAccountPlaidSettings({ account_id }) {
    const response = await axios.delete(
      `${this.endpoint}/accounts/${account_id}/settings/plaid`
    );
    return this.handleResponse(response);
  }

  async getAccountHistoricalValuation({ account_id }) {
    const response = await axios.get(
      `${this.endpoint}/accounts/${account_id}/history`
    );
    return this.handleResponse(response).historical_valuation;
  }

  async getLinkedAccounts({ account_id }) {
    const response = await axios.get(
      `${this.endpoint}/accounts/${account_id}/linked_accounts`
    );
    return this.handleResponse(response).linked_accounts;
  }

  async getLinkedAccount({ account_id, linked_account_id }) {
    const response = await axios.get(
      `${this.endpoint}/accounts/${account_id}/linked_accounts/${linked_account_id}`
    );
    return this.handleResponse(response).linked_account;
  }

  async getLinkedAccountsValuation({ account_id }) {
    const response = await axios.get(
      `${this.endpoint}/accounts/${account_id}/linked_accounts/valuation`
    );
    return this.handleResponse(response).linked_accounts;
  }

  async updateLinkedAccountMetadata({
    account_id,
    linked_account_id,
    account_name,
  }) {
    const response = await axios.put(
      `${this.endpoint}/accounts/${account_id}/linked_accounts/${linked_account_id}/metadata`,
      {
        account_name,
      }
    );
    return this.handleResponse(response);
  }

  async updateLinkedAccountCredentials({
    account_id,
    linked_account_id,
    validate,
    persist,
    credentials,
  }) {
    const response = await axios.put(
      `${
        this.endpoint
      }/accounts/${account_id}/linked_accounts/${linked_account_id}/credentials?validate=${
        validate | 0
      }&persist=${persist | 0}`,
      {
        credentials,
      }
    );
    return this.handleResponse(response);
  }

  async deleteLinkedAccount({ account_id, linked_account_id }) {
    const response = await axios.delete(
      `${this.endpoint}/accounts/${account_id}/linked_accounts/${linked_account_id}`
    );
    return this.handleResponse(response);
  }

  async getProviders() {
    const response = await axios.get(`${this.endpoint}/providers`);
    return this.handleResponse(response).providers;
  }

  async saveProvider(provider) {
    const response = await axios.put(`${this.endpoint}/providers`, provider);
    return this.handleResponse(response);
  }

  async deleteProvider(provider_id) {
    const response = await axios.delete(
      `${this.endpoint}/providers/${provider_id}`
    );
    return this.handleResponse(response);
  }

  async getProvider(providerId) {
    const response = await axios.get(
      `${this.endpoint}/providers/${providerId}`
    );
    return this.handleResponse(response);
  }

  async validateExternalAccountCredentials(account_id, data) {
    const { provider_id, credentials, account_name } = data;
    const response = await axios.post(
      `${this.endpoint}/accounts/${account_id}/linked_accounts?persist=0`,
      { provider_id, credentials, account_name }
    );
    return this.handleResponse(response).result.validated;
  }

  async linkAccount(account_id, data) {
    const { provider_id, credentials, account_name } = data;
    const response = await axios.post(
      `${this.endpoint}/accounts/${account_id}/linked_accounts?validate=0`,
      { provider_id, credentials, account_name }
    );
    return this.handleResponse(response).result;
  }

  async getHoldingsReport() {
    const response = await axios.get(`${this.endpoint}/reports/holdings`);
    return this.handleResponse(response).report;
  }

  async getEarningsReport() {
    const response = await axios.get(`${this.endpoint}/reports/earnings`);
    return this.handleResponse(response).report;
  }
}

export { FinbotClient };
