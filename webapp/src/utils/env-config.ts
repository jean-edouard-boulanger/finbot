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
