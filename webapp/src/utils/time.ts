import { DateTime } from "luxon";

export const asDateTime = (
  value: DateTime | string | null | undefined,
): DateTime | null => {
  if (value === null || value === undefined) {
    return null;
  }
  if (DateTime.isDateTime(value)) {
    return value;
  }
  return DateTime.fromISO(value);
};
