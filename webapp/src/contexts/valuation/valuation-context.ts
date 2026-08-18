import { createContext, useContext } from "react";

type ValuationRefreshContextProps = {
  /**
   * Bumped every time a manual valuation refresh lands. Views that render
   * valuation-derived data list it as a fetch dependency so the whole page moves
   * to the new snapshot together instead of showing two valuations at once.
   */
  version: number;
  notifyValuationRefreshed(): void;
};

export const ValuationRefreshContext =
  createContext<ValuationRefreshContextProps>({
    version: 0,
    notifyValuationRefreshed: () => {},
  });

export function useValuationVersion(): number {
  return useContext(ValuationRefreshContext).version;
}

export function useNotifyValuationRefreshed(): () => void {
  return useContext(ValuationRefreshContext).notifyValuationRefreshed;
}

export default ValuationRefreshContext;
