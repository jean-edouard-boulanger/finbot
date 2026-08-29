import React, {
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import { AuthContext } from "contexts/auth";
import { useNotifyValuationRefreshed } from "contexts/valuation";

import EventsContext, { type EventHandler } from "./events-context";
import {
  type ConnectionStatus,
  eventsSubprotocols,
  eventsWebsocketUrl,
  parseEvent,
  reconnectDelayMs,
} from "./events-stream";

interface EventsProviderProps {
  children?: React.ReactNode;
}

/**
 * Holds the websocket that carries server-pushed events, and reconnects it for as long as the user is
 * signed in. Must be mounted inside both AuthProvider (it needs the access token) and
 * ValuationRefreshProvider (a valuation event moves every valuation-derived view through it).
 */
export const EventsProvider: React.FC<EventsProviderProps> = ({ children }) => {
  const { accessToken } = useContext(AuthContext);
  const notifyValuationRefreshed = useNotifyValuationRefreshed();
  const [status, setStatus] = useState<ConnectionStatus>("idle");
  const handlersRef = useRef(new Set<EventHandler>());

  const subscribe = useCallback((handler: EventHandler) => {
    const handlers = handlersRef.current;
    handlers.add(handler);
    return () => {
      handlers.delete(handler);
    };
  }, []);

  useEffect(() => {
    if (!accessToken) {
      setStatus("idle");
      return;
    }

    let socket: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let attempt = 0;
    let cancelled = false;

    const connect = () => {
      if (cancelled) {
        return;
      }
      setStatus(attempt === 0 ? "connecting" : "reconnecting");
      socket = new WebSocket(
        eventsWebsocketUrl(),
        eventsSubprotocols(accessToken),
      );

      socket.onopen = () => {
        if (cancelled) {
          return;
        }
        attempt = 0;
        setStatus("open");
      };

      socket.onmessage = (message: MessageEvent<string>) => {
        const event = parseEvent(message.data);
        if (event === null || event.type === "ping") {
          return;
        }
        if (event.type === "valuation.updated") {
          // Every valuation-derived view already lists this version as a fetch dependency, so one call
          // moves the whole dashboard onto the new snapshot.
          notifyValuationRefreshed();
        }
        handlersRef.current.forEach((handler) => handler(event));
      };

      socket.onclose = () => {
        if (cancelled) {
          return;
        }
        setStatus("reconnecting");
        const delay = reconnectDelayMs(attempt);
        attempt += 1;
        reconnectTimer = setTimeout(connect, delay);
      };

      // An error is always followed by a close, which is where reconnection is handled.
      socket.onerror = () => {};
    };

    connect();

    return () => {
      cancelled = true;
      if (reconnectTimer !== null) {
        clearTimeout(reconnectTimer);
      }
      if (socket !== null) {
        socket.onclose = null;
        socket.close();
      }
      setStatus("idle");
    };
  }, [accessToken, notifyValuationRefreshed]);

  const value = useMemo(() => ({ status, subscribe }), [status, subscribe]);
  return (
    <EventsContext.Provider value={value}>{children}</EventsContext.Provider>
  );
};

export default EventsProvider;
