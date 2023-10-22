import { useState } from "react";

import { Constructible, makeApi } from "./factory";

export function useApi<ApiT extends Constructible>(
  apiType: ApiT,
): InstanceType<ApiT> {
  const [client] = useState(() => makeApi(apiType));
  return client;
}
