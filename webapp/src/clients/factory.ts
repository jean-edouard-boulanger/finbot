import { APP_SERVICE_ENDPOINT } from "utils/env-config";
import { Configuration, Middleware, ResponseContext } from "./app-client";

export type Constructible<
  Params extends readonly any[] = any[],
  T = any,
> = new (...params: Params) => T;

const middleware: Middleware = {
  post: async (context: ResponseContext) => {
    if (context.response.ok) {
      return;
    }
    let payload = null;
    try {
      payload = await context.response.json();
    } catch (e) {
      return;
    }
    if (payload && "error" in payload) {
      throw new Error(payload.error.user_message);
    }
  },
};

export function makeApi<ApiT extends Constructible>(
  apiType: ApiT,
  jwtToken?: string,
): InstanceType<ApiT> {
  const serverUrl = APP_SERVICE_ENDPOINT?.replace("/api/v1", "");
  return new apiType(
    new Configuration({
      accessToken: jwtToken,
      basePath: serverUrl,
      middleware: [middleware],
    }),
  );
}
