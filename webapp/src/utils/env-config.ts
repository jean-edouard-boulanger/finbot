interface FinbotEnv {
  FINBOT_SERVER_ENDPOINT?: string;
}

declare global {
  interface Window {
    __finbot_env: FinbotEnv;
  }
}

export const DEFAULT_FINBOT_SERVER_ENDPOINT = "http://127.0.0.1:5003/api/v1";
export const FINBOT_SERVER_ENDPOINT =
  window.__finbot_env.FINBOT_SERVER_ENDPOINT ?? DEFAULT_FINBOT_SERVER_ENDPOINT;
