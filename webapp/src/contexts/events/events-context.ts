import { createContext, useContext, useEffect } from "react";

import type { ConnectionStatus, FinbotEvent } from "./events-stream";

export type EventHandler = (event: FinbotEvent) => void;

type EventsContextProps = {
  /**
   * Connection state of the event socket. `disabled` means no provider is mounted — the guest routes
   * render shared chrome without one, and consumers fall back to their own polling in that case.
   */
  status: ConnectionStatus;
  subscribe(handler: EventHandler): () => void;
};

export const EventsContext = createContext<EventsContextProps>({
  status: "disabled",
  subscribe: () => () => {},
});

export function useEventsStatus(): ConnectionStatus {
  return useContext(EventsContext).status;
}

/**
 * Run `handler` for every event that arrives. The handler is re-subscribed whenever it changes, so
 * callers should wrap it in `useCallback` if it closes over anything that moves.
 */
export function useEventSubscription(handler: EventHandler): void {
  const { subscribe } = useContext(EventsContext);
  useEffect(() => subscribe(handler), [subscribe, handler]);
}

export default EventsContext;
