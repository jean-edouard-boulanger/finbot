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

  async getTraces({guid}) {
    const endpoint = `${this.endpoint}/admin/traces/${guid}`;
    const response = await axios.get(endpoint);
    return this.handleResponse(response);
  }

  async registerAccount(data) {
    const { email, full_name, password } = data;
    const settings = { "valuation_ccy": data.valuation_ccy }
    const response = await axios.post(
      `${this.endpoint}/accounts`,
      { email, full_name, password, settings });
    return this.handleResponse(response);
  }

  async logInAccount(data) {
    const { email, password } = data;
    const response = await axios.post(
      `${this.endpoint}/auth/login`,
      { email, password });
    return this.handleResponse(response);
  }

  async getAccount(settings) {
    const { account_id } = settings;
    const response = await axios.get(
      `${this.endpoint}/accounts/${account_id}`);
    return this.handleResponse(response).result;
  }

  async getAccountSettings(settings) {
    const { account_id } = settings;
    const response = await axios.get(
      `${this.endpoint}/accounts/${account_id}/settings`);
    return this.handleResponse(response).settings;
  }

  async getAccountHistoricalValuation(settings) {
    const { account_id } = settings;
    const response = await axios.get(
      `${this.endpoint}/accounts/${account_id}/history`);
    return this.handleResponse(response).historical_valuation;
  }

  async getLinkedAccounts(settings) {
    const { account_id } = settings;
    const response = await axios.get(
      `${this.endpoint}/accounts/${account_id}/linked_accounts`);
    return this.handleResponse(response).linked_accounts;
  }

  async getProviders() {
    const response = await axios.get(
      `${this.endpoint}/providers`);
    return this.handleResponse(response).providers;
  }

  async validateExternalAccountCredentials(data) {
    const { provider_id, credentials, account_name } = data;
    const response = await axios.post(
      `${this.endpoint}/accounts/1/linked_accounts?persist=0`,
      { provider_id, credentials, account_name });
    return this.handleResponse(response).result.validated;
  }

  async linkAccount(data) {
    const { provider_id, credentials, account_name } = data;
    const response = await axios.post(
      `${this.endpoint}/accounts/1/linked_accounts?validate=0`,
      { provider_id, credentials, account_name });
    return this.handleResponse(response).result;
  }
};


export { FinbotClient };
