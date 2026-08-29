import React, {
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { toast } from "sonner";

import { AuthContext } from "contexts/auth";
import { useEventSubscription, useEventsStatus } from "contexts/events";
import type { FinbotEvent } from "contexts/events";
import { useApi, UserAccountsNotificationsApi } from "clients";
import type { Notification } from "clients";

import NotificationsContext from "./notifications-context";

interface NotificationsProviderProps {
  children?: React.ReactNode;
}

export const NotificationsProvider: React.FC<NotificationsProviderProps> = ({
  children,
}) => {
  const { userAccountId } = useContext(AuthContext);
  const notificationsApi = useApi(UserAccountsNotificationsApi);
  const eventsStatus = useEventsStatus();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  // Keyed by id, valued by `lastSeenAt` as of the last reload: recurrence bumps the same row's
  // `lastSeenAt` rather than creating a new one, so tracking ids alone would only ever toast once per
  // notification, silently missing every recurrence after the first.
  const knownLastSeen = useRef(new Map<number, string>());
  const primed = useRef(false);

  const reload = useCallback(async () => {
    if (userAccountId === null || userAccountId === undefined) {
      return;
    }
    setLoading(true);
    try {
      const result = await notificationsApi.getNotifications({ userAccountId });
      // Only toast for something that appeared or recurred while the user was watching. On the first
      // load everything is new to us but old to them, so announcing them would be noise.
      if (primed.current) {
        result.notifications
          .filter((notification) => {
            const lastSeenAt = notification.lastSeenAt.toISOString();
            return (
              notification.severity === "error" &&
              notification.status === "active" &&
              knownLastSeen.current.get(notification.id) !== lastSeenAt
            );
          })
          .forEach((notification) => toast.error(notification.title));
      }
      knownLastSeen.current = new Map(
        result.notifications.map((notification) => [
          notification.id,
          notification.lastSeenAt.toISOString(),
        ]),
      );
      primed.current = true;
      setNotifications(result.notifications);
      setUnreadCount(result.unreadCount);
    } catch {
      // The panel keeps whatever it last had. The next event or reconnect retries.
    }
    setLoading(false);
  }, [notificationsApi, userAccountId]);

  useEffect(() => {
    primed.current = false;
    knownLastSeen.current = new Map();
    reload();
  }, [reload]);

  // Events say only that something moved; REST stays the source of truth for what it moved to.
  const onEvent = useCallback(
    (event: FinbotEvent) => {
      if (event.type.startsWith("notification.") || event.type === "refetch") {
        reload();
      }
    },
    [reload],
  );
  useEventSubscription(onEvent);

  // Anything raised while the socket was down never arrived, so a fresh connection re-reads.
  useEffect(() => {
    if (eventsStatus === "open") {
      reload();
    }
  }, [eventsStatus, reload]);

  const markAllRead = useCallback(async () => {
    if (userAccountId === null || userAccountId === undefined) {
      return;
    }
    setUnreadCount(0);
    try {
      await notificationsApi.markNotificationsRead({
        userAccountId,
        markNotificationsReadRequest: { notificationIds: null },
      });
    } finally {
      await reload();
    }
  }, [notificationsApi, userAccountId, reload]);

  const dismiss = useCallback(
    async (notificationId: number) => {
      if (userAccountId === null || userAccountId === undefined) {
        return;
      }
      setNotifications((current) =>
        current.filter((notification) => notification.id !== notificationId),
      );
      try {
        await notificationsApi.dismissNotification({
          userAccountId,
          notificationId,
        });
      } finally {
        await reload();
      }
    },
    [notificationsApi, userAccountId, reload],
  );

  const dismissAll = useCallback(async () => {
    if (userAccountId === null || userAccountId === undefined) {
      return;
    }
    setNotifications([]);
    try {
      await notificationsApi.dismissAllNotifications({ userAccountId });
    } finally {
      await reload();
    }
  }, [notificationsApi, userAccountId, reload]);

  const value = useMemo(
    () => ({
      notifications,
      unreadCount,
      loading,
      markAllRead,
      dismiss,
      dismissAll,
      reload,
    }),
    [
      notifications,
      unreadCount,
      loading,
      markAllRead,
      dismiss,
      dismissAll,
      reload,
    ],
  );

  return (
    <NotificationsContext.Provider value={value}>
      {children}
    </NotificationsContext.Provider>
  );
};

export default NotificationsProvider;
