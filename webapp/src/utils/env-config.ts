interface FinbotEnv {
  FINBOT_SERVER_ENDPOINT?: string;
}

declare global {
  interface Window {
    __finbot_env?: FinbotEnv;
  }
}

const env = window.__finbot_env ?? {};

export const FINBOT_SERVER_ENDPOINT =
  env.FINBOT_SERVER_ENDPOINT ?? "/api/v1";
export const APP_SERVICE_ENDPOINT = FINBOT_SERVER_ENDPOINT;
