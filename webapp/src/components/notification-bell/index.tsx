import React, { useEffect, useRef, useState } from "react";
import { Bell } from "lucide-react";

import { activeNotifications, useNotifications } from "contexts/notifications";
import { NotificationPanel } from "components/notification-panel";
import { Button } from "components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "components/ui/popover";
import { Sheet, SheetContent, SheetTitle } from "components/ui/sheet";
import { cn } from "lib/utils";

/**
 * Entry point to the notification panel.
 *
 * The count carries the app's accent rather than a red dot; red is kept for the case where a refresh failed
 * outright and the figures may be missing a source entirely.
 */
export const NotificationBell: React.FC<{ variant?: "desktop" | "mobile" }> = ({
  variant = "desktop",
}) => {
  const { notifications, unreadCount } = useNotifications();
  const [open, setOpen] = useState(false);
  const hasError = activeNotifications(notifications).some(
    (notification) => notification.severity === "error",
  );

  const label =
    unreadCount > 0 ? `Notifications, ${unreadCount} unread` : "Notifications";

  const trigger = (
    <Button
      variant="ghost"
      size="icon"
      aria-label={label}
      aria-expanded={open}
      className="relative h-8 w-8 text-muted-foreground hover:text-foreground"
      onClick={variant === "mobile" ? () => setOpen(true) : undefined}
    >
      <Bell className="h-4 w-4" />
      {unreadCount > 0 && (
        <span
          aria-hidden="true"
          className={cn(
            "absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full px-1 text-[10px] font-semibold tabular-nums text-background",
            hasError ? "bg-destructive" : "bg-primary",
          )}
        >
          {unreadCount > 9 ? "9+" : unreadCount}
        </span>
      )}
    </Button>
  );

  if (variant === "mobile") {
    return (
      <>
        {trigger}
        <Sheet open={open} onOpenChange={setOpen}>
          <SheetContent side="right" className="w-full p-0 sm:max-w-sm">
            <SheetTitle className="sr-only">Notifications</SheetTitle>
            <NotificationPanel onNavigate={() => setOpen(false)} />
          </SheetContent>
        </Sheet>
      </>
    );
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>{trigger}</PopoverTrigger>
      <PopoverContent
        // Opens over the dashboard rather than over the navigation it is anchored in: a panel that
        // covers the rail hides the very accounts it is complaining about.
        side="right"
        align="start"
        sideOffset={10}
        alignOffset={-8}
        // On a 6%-lightness page a 5% border step and shadow-md are both invisible, so the panel needs a
        // real shadow to read as something floating above the page.
        className="w-[21rem] overflow-hidden p-0 shadow-2xl shadow-black/50"
      >
        <NotificationPanel onNavigate={() => setOpen(false)} />
      </PopoverContent>
    </Popover>
  );
};

/**
 * Announces arrivals to screen readers.
 *
 * Rendered once, separately from the list: making the list itself a live region would re-announce every row
 * whenever anything in it changed.
 */
export const NotificationAnnouncer: React.FC = () => {
  const { notifications } = useNotifications();
  const [message, setMessage] = useState("");
  const known = useRef<Set<number> | null>(null);

  useEffect(() => {
    const ids = new Set(notifications.map((notification) => notification.id));
    if (known.current === null) {
      known.current = ids;
      return;
    }
    const arrived = notifications.filter(
      (notification) => !known.current?.has(notification.id),
    );
    known.current = ids;
    if (arrived.length === 1) {
      setMessage(arrived[0].title);
    } else if (arrived.length > 1) {
      setMessage(`${arrived.length} new notifications`);
    }
  }, [notifications]);

  return (
    <span aria-live="polite" className="sr-only">
      {message}
    </span>
  );
};

export default NotificationBell;
