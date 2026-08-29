// Websocket consumer for the finbot event bus — keep in sync with finbot/apps/appwsrv/routes/events.py.
//
// The socket is a hint channel, not a source of truth: delivery is best-effort and at-most-once. Every
// degradation path on the server collapses to a `refetch` frame, and so does every reconnect here, so
// consumers only ever need two behaviours — apply an event, or re-read over REST.

import { APP_SERVICE_ENDPOINT } from "utils/env-config";

export const EVENTS_SUBPROTOCOL = "finbot.events.v1";

export type FinbotEventType =
  | "notification.created"
  | "notification.updated"
  | "notification.resolved"
  | "notification.read"
  | "notification.dismissed"
  | "valuation.updated"
  | "refetch"
  | "ping";

export interface FinbotEvent {
  type: FinbotEventType | string;
  user_account_id: number;
  seq: number;
  emitted_at: string;
  data?: Record<string, unknown>;
}

export type ConnectionStatus =
  | "idle"
  | "connecting"
  | "open"
  | "reconnecting"
  | "disabled";

/**
 * The endpoint is either absolute (public/env-config.js, which is how dev and prod both run) or the
 * relative `/api/v1` fallback. Both have to produce a ws:// or wss:// URL on the right origin.
 */
export function eventsWebsocketUrl(): string {
  const base = APP_SERVICE_ENDPOINT.startsWith("http")
    ? APP_SERVICE_ENDPOINT
    : `${window.location.origin}${APP_SERVICE_ENDPOINT}`;
  return `${base.replace(/^http/, "ws")}/events/ws`;
}

/**
 * Browsers cannot set an Authorization header on a websocket, so the access token travels as a second
 * subprotocol value alongside the protocol name the server echoes back.
 */
export function eventsSubprotocols(accessToken: string): string[] {
  return [EVENTS_SUBPROTOCOL, `bearer.${accessToken}`];
}

export function parseEvent(raw: string): FinbotEvent | null {
  try {
    const parsed = JSON.parse(raw) as Partial<FinbotEvent>;
    if (typeof parsed?.type !== "string") {
      return null;
    }
    return parsed as FinbotEvent;
  } catch {
    return null;
  }
}

const BASE_RECONNECT_DELAY_MS = 1_000;
const MAX_RECONNECT_DELAY_MS = 30_000;

/** Exponential backoff with jitter, so a restarted backend does not get a synchronised stampede. */
export function reconnectDelayMs(attempt: number): number {
  const capped = Math.min(
    MAX_RECONNECT_DELAY_MS,
    BASE_RECONNECT_DELAY_MS * 2 ** Math.max(0, attempt),
  );
  return Math.round(capped * (0.5 + Math.random() * 0.5));
}
