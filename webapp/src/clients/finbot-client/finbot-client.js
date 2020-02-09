import axios from 'axios';


class FinbotClient {
  constructor(settings) {
    settings = settings || {};
    this.endpoint = settings.endpoint || "http://127.0.0.1:5003/api/v1"
  }

  _handleResponse(response) {
    const app_data = response.data;
    if (app_data.hasOwnProperty("error")) {
      throw app_data.error.debug_message;
    }
    console.log("APPDATERWS", app_data)
    return app_data;
  }

  async registerAccount(data) {
    console.log("in registeraccount")
    const { email, full_name, password } = data;
    const settings = { "valuation_ccy": data.settings }
    const response = await axios.post(
      `${this.endpoint}/accounts`, { email, full_name, password, settings });
    return this._handleResponse(response);
  }

  async getAccount(settings) {
    const { account_id } = settings;
    const response = await axios.get(
      `${this.endpoint}/accounts/${account_id}`);
    return this._handleResponse(response).result;
  }

  async getAccountHistoricalValuation(settings) {
    const { account_id } = settings;
    const response = await axios.get(
      `${this.endpoint}/accounts/${account_id}/history`);
    return this._handleResponse(response).historical_valuation;
  }

  async getProviders() {
    const response = await axios.get(`${this.endpoint}/providers`);
    return this._handleResponse(response).providers;
  }

  async getLinkedAccounts(settings) {
    const { account_id } = settings;
    const response = await axios.get(
      `${this.endpoint}/accounts/${account_id}/linked_accounts`);
    return this._handleResponse(response).linked_accounts;
  }

  async validateExternalAccountCredentials(data) {
    const { provider_id, credentials, account_name } = data;
    const response = await axios.post(
      `${this.endpoint}/accounts/1/linked_accounts?persist=0`, { 
        provider_id, 
        credentials, 
        account_name
      });
    return this._handleResponse(response).result.validated;
  }
};


export { FinbotClient };
