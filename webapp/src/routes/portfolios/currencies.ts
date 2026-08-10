import { ComboboxGroup } from "components/combobox";

/** Enough to keep the picker usable if the browser cannot enumerate ISO 4217 itself. */
const FALLBACK_CURRENCIES = [
  "AUD",
  "CAD",
  "CHF",
  "CNY",
  "EUR",
  "GBP",
  "HKD",
  "INR",
  "JPY",
  "NOK",
  "NZD",
  "SEK",
  "SGD",
  "USD",
  "ZAR",
];

function allCurrencies(): string[] {
  const supported = (
    Intl as unknown as { supportedValuesOf?: (key: string) => string[] }
  ).supportedValuesOf;
  try {
    return supported ? supported("currency") : FALLBACK_CURRENCIES;
  } catch {
    return FALLBACK_CURRENCIES;
  }
}

function currencyName(code: string): string | undefined {
  try {
    return new Intl.DisplayNames(undefined, { type: "currency" }).of(code);
  } catch {
    return undefined;
  }
}

/**
 * Currencies to choose from, with the ones already in play first: whatever this portfolio and
 * account use is nearly always what is wanted, and the rest are a search away.
 */
export function currencyGroups(inUse: string[]): ComboboxGroup[] {
  const seen = new Set<string>();
  const nearby = inUse
    .map((code) => code.toUpperCase())
    .filter((code) => {
      if (!code || seen.has(code)) {
        return false;
      }
      seen.add(code);
      return true;
    });

  const toOption = (code: string) => ({
    value: code,
    label: code,
    hint: currencyName(code),
  });

  const rest = allCurrencies()
    .filter((code) => !seen.has(code))
    .map(toOption);

  return [
    ...(nearby.length > 0
      ? [{ label: "In use", options: nearby.map(toOption) }]
      : []),
    { label: nearby.length > 0 ? "All currencies" : undefined, options: rest },
  ];
}
