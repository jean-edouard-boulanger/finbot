import axios from 'axios';


class FinbotClient {
  constructor(settings) {
    settings = settings || {};
    this.endpoint = settings.endpoint || "http://127.0.0.1:5003/api/v1"
  }

  handleResponse(response) {
    const app_data = response.data;
    if (app_data.hasOwnProperty("error")) {
      throw app_data.error.debug_message;
    }
    return app_data;
  }

  async getTraces({ guid }) {
    const endpoint = `${this.endpoint}/admin/traces/${guid}`;
    const response = await axios.get(endpoint);
    return this.handleResponse(response);
  }

  async registerAccount({ email, full_name, password, valuation_ccy }) {
    const settings = { "valuation_ccy": valuation_ccy }
    const response = await axios.post(
      `${this.endpoint}/accounts`,
      { email, full_name, password, settings });
    return this.handleResponse(response);
  }

  async logInAccount({ email, password }) {
    const response = await axios.post(
      `${this.endpoint}/auth/login`,
      { email, password });
    return this.handleResponse(response);
  }

  async getAccount({ account_id }) {
    const response = await axios.get(
      `${this.endpoint}/accounts/${account_id}`);
    return this.handleResponse(response).result;
  }

  async isAccountConfigured({ account_id }) {
      const response = await axios.get(
    `${this.endpoint}/accounts/${account_id}/is_configured`);
      return this.handleResponse(response).configured;
  }

  async getAccountSettings({ account_id }) {
    const response = await axios.get(
      `${this.endpoint}/accounts/${account_id}/settings`);
    return this.handleResponse(response).settings;
  }

  async getAccountHistoricalValuation({ account_id }) {
    const response = await axios.get(
      `${this.endpoint}/accounts/${account_id}/history`);
    return this.handleResponse(response).historical_valuation;
  }

  async getLinkedAccounts({ account_id }) {
    const response = await axios.get(
      `${this.endpoint}/accounts/${account_id}/linked_accounts`);
    return this.handleResponse(response).linked_accounts;
  }

  async getLinkedAccountsValuation({ account_id }) {
    const response = await axios.get(
      `${this.endpoint}/accounts/${account_id}/linked_accounts/valuation`);
    return this.handleResponse(response).linked_accounts;
  }

  async deleteLinkedAccount({ account_id, linked_account_id }) {
    const response = await axios.delete(
      `${this.endpoint}/accounts/${account_id}/linked_accounts/${linked_account_id}`);
    return this.handleResponse(response);
  }

  async getProviders() {
    const response = await axios.get(
      `${this.endpoint}/providers`);
    return this.handleResponse(response).providers;
  }

  async saveProvider(provider) {
    const response = await axios.put(
      `${this.endpoint}/providers`,
      provider);
    return this.handleResponse(response);
  }

  async deleteProvider(provider_id) {
    const response = await axios.delete(
      `${this.endpoint}/providers/${provider_id}`);
    return this.handleResponse(response);
  }

  async getProvider(providerId) {
    const response = await axios.get(
      `${this.endpoint}/providers/${providerId}`);
    return this.handleResponse(response);
  }

  async validateExternalAccountCredentials(account_id, data) {
    const { provider_id, credentials, account_name } = data;
    const response = await axios.post(
      `${this.endpoint}/accounts/${account_id}/linked_accounts?persist=0`,
      { provider_id, credentials, account_name });
    return this.handleResponse(response).result.validated;
  }

  async linkAccount(account_id, data) {
    const { provider_id, credentials, account_name } = data;
    const response = await axios.post(
      `${this.endpoint}/accounts/${account_id}/linked_accounts?validate=0`,
      { provider_id, credentials, account_name });
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
