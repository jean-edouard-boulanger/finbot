import axios from 'axios';


class FinbotClient {
    constructor(settings) {
      settings = settings || {};
      this.endpoint = settings.endpoint || "http://127.0.0.1:5003/api/v1"
    }
  
    handle_response(response) {
      const app_data = response.data;
      if(app_data.hasOwnProperty("error")) {
        throw app_data.error.debug_message;
      }
      return app_data;
    }
  
    async getAccount(settings) {
      const {account_id} = settings;
      const response = await axios.get(`${this.endpoint}/accounts/${account_id}`);
      return this.handle_response(response).result;
    }
  
    async getAccountHistoricalValuation(settings) {
      const {account_id} = settings;
      const response = await axios.get(`${this.endpoint}/accounts/${account_id}/history`);
      return this.handle_response(response).historical_valuation;
    }
  
    async getLinkedAccounts(settings) {
      const {account_id} = settings;
      const response = await axios.get(`${this.endpoint}/accounts/${account_id}/linked_accounts`);
      return this.handle_response(response).linked_accounts;
    }
  };


  export default FinbotClient;
