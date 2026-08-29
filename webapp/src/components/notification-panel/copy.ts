import { DateTime } from "luxon";

import type { Notification } from "clients";
import { failurePayload, lastSuccessAt } from "contexts/notifications";

/**
 * What the reader can do about a broken account.
 *
 * The raw provider message and stack trace already live in Settings → Linked accounts, so the panel links
 * there instead of repeating them. The verb here is the verb on the destination: a row that offers "Fix
 * credentials" lands on the credentials form.
 */
export interface NotificationAction {
  label: string;
  to: string;
}

export function actionFor(
  notification: Notification,
): NotificationAction | null {
  const payload = failurePayload(notification);
  if (notification.notificationType !== "linked_account_failure") {
    return null;
  }
  switch (payload.error_code) {
    case "P001":
      return { label: "Fix credentials", to: "/settings/linked" };
    case "P004":
      return { label: "Open settings", to: "/settings/linked" };
    case "P002":
      return { label: "Remove account", to: "/settings/linked" };
    default:
      return payload.linked_account_id
        ? {
            label: "View account",
            to: `/dashboard/accounts/${payload.linked_account_id}`,
          }
        : { label: "View accounts", to: "/settings/linked" };
  }
}

/** "since Tuesday" / "since 4 August" — a date the reader can place, not a duration they have to decode. */
export function sinceClause(at: Date | null): string | null {
  if (at === null) {
    return null;
  }
  const when = DateTime.fromJSDate(at);
  const daysAgo = -when.diffNow("days").days;
  if (daysAgo < 1) {
    return `since ${when.toFormat("HH:mm")}`;
  }
  if (daysAgo < 7) {
    return `since ${when.toFormat("cccc")}`;
  }
  return `since ${when.toFormat("d LLLL")}`;
}

/** "3 days old" — how far behind the figures on screen actually are. */
export function ageClause(at: Date | null): string | null {
  if (at === null) {
    return null;
  }
  const hours = -DateTime.fromJSDate(at).diffNow("hours").hours;
  if (hours < 24) {
    return "less than a day old";
  }
  const days = Math.floor(hours / 24);
  return `${days} ${days === 1 ? "day" : "days"} old`;
}

export function formatMoney(value: number, currency: string | null): string {
  try {
    return new Intl.NumberFormat(undefined, {
      style: "currency",
      currency: currency ?? "GBP",
      maximumFractionDigits: 0,
    }).format(value);
  } catch {
    return `${Math.round(value)}`;
  }
}

/**
 * The line that says what being stale is costing: "£12,340 of net worth is 3 days old".
 *
 * Returns null when there is nothing concrete to say, so the row stays quiet rather than padding itself
 * with a vaguer sentence.
 */
export function stakeClause(notification: Notification): string | null {
  const payload = failurePayload(notification);
  const value = payload.last_known_value;
  const age = ageClause(lastSuccessAt(notification));
  if (value === null || value === undefined || age === null) {
    return null;
  }
  return `${formatMoney(value, payload.valuation_ccy ?? null)} of net worth is ${age}`;
}

/** Supporting detail, never the headline: how long it has been failing is what the reader acts on. */
export function attemptsClause(notification: Notification): string | null {
  if (notification.occurrences <= 1) {
    return null;
  }
  return `${notification.occurrences} attempts`;
}

export function resolvedClause(notification: Notification): string | null {
  if (!notification.resolvedAt) {
    return null;
  }
  return `Fixed ${DateTime.fromJSDate(notification.resolvedAt).toFormat("HH:mm")}`;
}
