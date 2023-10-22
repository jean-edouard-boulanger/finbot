import { APP_SERVICE_ENDPOINT } from "utils/env-config";
import { Configuration as AppClientConfig } from "./app-client";

export type Constructible<
  Params extends readonly any[] = any[],
  T = any,
> = new (...params: Params) => T;

export function makeApi<ApiT extends Constructible>(
  apiType: ApiT,
  jwtToken?: string,
): InstanceType<ApiT> {
  const serverUrl = APP_SERVICE_ENDPOINT?.replace("/api/v1", "");
  return new apiType(
    new AppClientConfig({
      accessToken: jwtToken,
      basePath: serverUrl,
    }),
  );
}
