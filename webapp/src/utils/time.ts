import { DateTime } from "luxon";

export const asDateTime = (
  value: DateTime | Date | string | null | undefined,
): DateTime | null => {
  if (value === null || value === undefined) {
    return null;
  }
  if (value instanceof Date) {
    return DateTime.fromJSDate(value);
  }
  if (DateTime.isDateTime(value)) {
    return value;
  }
  return DateTime.fromISO(value);
};
