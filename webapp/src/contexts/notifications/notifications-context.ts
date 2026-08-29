import { createContext, useContext } from "react";

import type { Notification } from "clients";

export interface LinkedAccountFailurePayload {
  linked_account_id?: number;
  provider_id?: string;
  account_name?: string;
  error_code?: string | null;
  last_success_at?: string | null;
  last_known_value?: number | null;
  valuation_ccy?: string | null;
}

type NotificationsContextProps = {
  notifications: Notification[];
  unreadCount: number;
  loading: boolean;
  markAllRead(): Promise<void>;
  dismiss(notificationId: number): Promise<void>;
  dismissAll(): Promise<void>;
  reload(): Promise<void>;
};

export const NotificationsContext = createContext<NotificationsContextProps>({
  notifications: [],
  unreadCount: 0,
  loading: false,
  markAllRead: async () => {},
  dismiss: async () => {},
  dismissAll: async () => {},
  reload: async () => {},
});

export function useNotifications(): NotificationsContextProps {
  return useContext(NotificationsContext);
}

/** Notifications still needing the user to do something. */
export function activeNotifications(
  notifications: Notification[],
): Notification[] {
  return notifications.filter(
    (notification) => notification.status !== "resolved",
  );
}

/** Problems that fixed themselves and are waiting to be acknowledged. */
export function resolvedNotifications(
  notifications: Notification[],
): Notification[] {
  return notifications.filter(
    (notification) => notification.status === "resolved",
  );
}

export function failurePayload(
  notification: Notification,
): LinkedAccountFailurePayload {
  return (notification.payload ?? {}) as LinkedAccountFailurePayload;
}

/**
 * When this account last reported figures.
 *
 * Read from the payload rather than the notification's own timestamps: dismissing a notification and
 * letting it recur starts a new row, but the data really is still as old as it was, and the interface
 * must not claim otherwise.
 */
export function lastSuccessAt(notification: Notification): Date | null {
  const raw = failurePayload(notification).last_success_at;
  return raw ? new Date(raw) : null;
}

export default NotificationsContext;
