interface FinbotEnv {
  FINBOT_SERVER_ENDPOINT?: string;
}

declare global {
  interface Window {
    __finbot_env: FinbotEnv;
  }
}

export const FINBOT_SERVER_ENDPOINT =
  window.__finbot_env.FINBOT_SERVER_ENDPOINT;
export const APP_SERVICE_ENDPOINT = FINBOT_SERVER_ENDPOINT;
