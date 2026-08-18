import React, { useCallback, useMemo, useState } from "react";

import ValuationRefreshContext from "./valuation-context";

interface ValuationRefreshProviderProps {
  children?: React.ReactNode;
}

export const ValuationRefreshProvider: React.FC<
  ValuationRefreshProviderProps
> = ({ children }) => {
  const [version, setVersion] = useState(0);
  const notifyValuationRefreshed = useCallback(
    () => setVersion((current) => current + 1),
    [],
  );
  const value = useMemo(
    () => ({ version, notifyValuationRefreshed }),
    [version, notifyValuationRefreshed],
  );
  return (
    <ValuationRefreshContext.Provider value={value}>
      {children}
    </ValuationRefreshContext.Provider>
  );
};

export default ValuationRefreshProvider;
