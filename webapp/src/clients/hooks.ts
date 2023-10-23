import { useState, useEffect, useContext } from "react";

import { Constructible, makeApi } from "./factory";
import { AuthContext } from "contexts";

export function useApi<ApiT extends Constructible>(
  apiType: ApiT,
): InstanceType<ApiT> {
  const { accessToken } = useContext(AuthContext);
  const [api, setApi] = useState(() =>
    makeApi(apiType, accessToken ?? undefined),
  );
  useEffect(() => {
    setApi(makeApi(apiType, accessToken ?? undefined));
  }, [accessToken]);
  return api;
}
