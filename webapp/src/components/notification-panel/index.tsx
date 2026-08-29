import React from "react";
import { NavLink } from "react-router-dom";
import { ArrowRight, X } from "lucide-react";

import type { Notification } from "clients";
import {
  activeNotifications,
  lastSuccessAt,
  resolvedNotifications,
  useNotifications,
} from "contexts/notifications";
import { cn } from "lib/utils";

import {
  actionFor,
  attemptsClause,
  resolvedClause,
  sinceClause,
  stakeClause,
} from "./copy";

const SectionHeading: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => (
  <h3 className="px-3.5 pb-1 pt-2.5 text-[10px] font-medium uppercase tracking-[0.12em] text-muted-foreground/70">
    {children}
  </h3>
);

const NotificationRow: React.FC<{
  notification: Notification;
  onNavigate?: () => void;
}> = ({ notification, onNavigate }) => {
  const { dismiss } = useNotifications();
  const isResolved = notification.status === "resolved";
  const unread =
    notification.readAt === null || notification.readAt === undefined;
  const action = isResolved ? null : actionFor(notification);
  const when = isResolved ? null : sinceClause(lastSuccessAt(notification));
  const fixed = isResolved ? resolvedClause(notification) : null;
  const stake = isResolved ? null : stakeClause(notification);
  const attempts = attemptsClause(notification);
  const cause = [notification.body, attempts].filter(Boolean).join(" · ");

  return (
    <div
      className={cn(
        // The rail is the whole good/bad signal, in the same two colours the dashboard's change pills
        // already use. pl-3 + the 2px rail keeps the text on the same line as the panel header.
        "group flex gap-2 border-l-2 py-2.5 pl-3 pr-3.5 transition-colors hover:bg-muted/30",
        // Scoped to the left edge: colouring the whole border would tint the divide-y rule between
        // rows into a full-width red line.
        isResolved ? "border-l-gain" : "border-l-destructive",
        !unread && "opacity-65",
      )}
    >
      <div className="min-w-0 flex-1">
        <p className="text-[13px] leading-snug text-foreground">
          {notification.title}
          {when !== null && (
            <span className="whitespace-nowrap font-normal text-muted-foreground">
              {" "}
              {when}
            </span>
          )}
        </p>
        {fixed !== null && (
          <p className="mt-1 text-[11.5px] leading-snug text-muted-foreground">
            {fixed}
          </p>
        )}
        {stake !== null && (
          <p className="mt-1 text-[11.5px] leading-snug text-foreground/65">
            {stake}
          </p>
        )}
        {cause !== "" && (
          <p className="mt-0.5 text-[11.5px] leading-snug text-muted-foreground">
            {cause}
          </p>
        )}
        {action !== null && (
          <NavLink
            to={action.to}
            onClick={onNavigate}
            className="mt-1.5 inline-flex items-center gap-1 rounded-sm text-[11.5px] font-medium text-primary hover:underline focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring"
          >
            {action.label}
            <ArrowRight className="h-3 w-3" />
          </NavLink>
        )}
      </div>
      <button
        type="button"
        aria-label={`Dismiss: ${notification.title}`}
        onClick={() => dismiss(notification.id)}
        className="-mr-1 mt-[3px] h-5 w-5 shrink-0 rounded-sm text-muted-foreground/50 transition-colors hover:text-foreground focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring"
      >
        <X className="h-3.5 w-3.5" />
      </button>
    </div>
  );
};

export const NotificationPanel: React.FC<{ onNavigate?: () => void }> = ({
  onNavigate,
}) => {
  const { notifications, unreadCount, markAllRead } = useNotifications();
  const active = activeNotifications(notifications);
  const resolved = resolvedNotifications(notifications);
  // Above a lone group the heading states the obvious; it only earns its place when it separates two.
  const showHeadings = active.length > 0 && resolved.length > 0;

  return (
    <div className="flex max-h-[70vh] flex-col">
      <div className="flex h-9 shrink-0 items-center justify-between border-b border-border/60 px-3.5">
        <span className="text-[10px] font-medium uppercase tracking-[0.12em] text-muted-foreground">
          Notifications
        </span>
        {unreadCount > 0 && (
          <button
            type="button"
            onClick={markAllRead}
            className="rounded-sm text-[11px] text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring"
          >
            Mark all read
          </button>
        )}
      </div>

      {notifications.length === 0 ? (
        // States only what is known. An empty panel means nothing was reported -- not that every account
        // synced, which is a claim this component has no data to make.
        <p className="px-3.5 py-3 text-[13px] text-muted-foreground">
          No notifications
        </p>
      ) : (
        <div className="overflow-y-auto">
          {active.length > 0 && (
            <div className="divide-y divide-border/40">
              {showHeadings && <SectionHeading>Needs attention</SectionHeading>}
              {active.map((notification) => (
                <NotificationRow
                  key={notification.id}
                  notification={notification}
                  onNavigate={onNavigate}
                />
              ))}
            </div>
          )}
          {resolved.length > 0 && (
            <div
              className={cn(
                "divide-y divide-border/40",
                active.length > 0 && "border-t border-border/60",
              )}
            >
              {showHeadings && <SectionHeading>Resolved</SectionHeading>}
              {resolved.map((notification) => (
                <NotificationRow
                  key={notification.id}
                  notification={notification}
                  onNavigate={onNavigate}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default NotificationPanel;
