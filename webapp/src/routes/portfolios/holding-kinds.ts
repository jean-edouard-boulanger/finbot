import {
  AssetClass,
  AssetType,
  PortfolioEntry,
  PortfolioEntryPayload,
  SearchSecuritiesKindEnum,
} from "clients";

/**
 * The asset class/type taxonomy is Finbot's, not the user's: nobody thinks of their flat as
 * "real_estate / residential_property". These presets ask the one question people can answer and
 * derive the pair, which also makes nonsensical combinations impossible to pick.
 *
 * `custom` is the escape hatch for anything the presets do not cover, and reveals the raw selects.
 */
export interface HoldingKind {
  id: string;
  label: string;
  group: "Assets" | "Liabilities" | "Other";
  itemType: "asset" | "liability";
  assetClass?: AssetClass;
  assetType?: AssetType;
  liabilityType?: string;
  /** Whether a quantity is meaningful. A house is always one house. */
  divisible: boolean;
  /** Whether tracking a market price via a proxy security makes sense. */
  proxyable: boolean;
  /**
   * Instrument type the symbol search starts narrowed to. Left unset where the answer is not one
   * type: gold is tracked through futures as readily as through an ETC.
   */
  searchKind?: SearchSecuritiesKindEnum;
  /**
   * Asset types this preset recognises when reading an existing holding. A fund imported as
   * equities/ETF and one created here as multi_asset/generic_fund are both "Fund or ETF" to a
   * person, so both land on the same preset.
   */
  matches?: AssetType[];
}

export const HOLDING_KINDS: HoldingKind[] = [
  {
    id: "home",
    label: "Home or residential property",
    group: "Assets",
    itemType: "asset",
    assetClass: AssetClass.RealEstate,
    assetType: AssetType.ResidentialProperty,
    divisible: false,
    proxyable: false,
    matches: [AssetType.ResidentialProperty],
  },
  {
    id: "commercial",
    label: "Commercial property",
    group: "Assets",
    itemType: "asset",
    assetClass: AssetClass.RealEstate,
    assetType: AssetType.CommercialProperty,
    divisible: false,
    proxyable: false,
    matches: [AssetType.CommercialProperty],
  },
  {
    id: "land",
    label: "Land",
    group: "Assets",
    itemType: "asset",
    assetClass: AssetClass.RealEstate,
    assetType: AssetType.LandProperty,
    divisible: false,
    proxyable: false,
    matches: [AssetType.LandProperty],
  },
  {
    id: "metal",
    label: "Precious metal",
    group: "Assets",
    itemType: "asset",
    assetClass: AssetClass.Commodities,
    assetType: AssetType.PreciousMetal,
    divisible: true,
    proxyable: true,
    matches: [AssetType.PreciousMetal],
  },
  {
    id: "shares",
    label: "Shares",
    group: "Assets",
    itemType: "asset",
    assetClass: AssetClass.Equities,
    assetType: AssetType.Stock,
    divisible: true,
    proxyable: true,
    searchKind: SearchSecuritiesKindEnum.Equity,
    matches: [AssetType.Stock],
  },
  {
    id: "fund",
    label: "Fund or ETF",
    group: "Assets",
    itemType: "asset",
    assetClass: AssetClass.MultiAsset,
    assetType: AssetType.GenericFund,
    divisible: true,
    proxyable: true,
    searchKind: SearchSecuritiesKindEnum.Etf,
    matches: [
      AssetType.GenericFund,
      AssetType.Etf,
      AssetType.Etn,
      AssetType.Etc,
    ],
  },
  {
    id: "crypto",
    label: "Crypto",
    group: "Assets",
    itemType: "asset",
    assetClass: AssetClass.Crypto,
    assetType: AssetType.CryptoCurrency,
    divisible: true,
    proxyable: true,
    searchKind: SearchSecuritiesKindEnum.Cryptocurrency,
    matches: [
      AssetType.CryptoCurrency,
      AssetType.UtilityToken,
      AssetType.SecurityToken,
      AssetType.StableCoin,
    ],
  },
  {
    id: "cash",
    label: "Cash",
    group: "Assets",
    itemType: "asset",
    assetClass: AssetClass.Currency,
    assetType: AssetType.Cash,
    divisible: false,
    proxyable: false,
    matches: [AssetType.Cash],
  },
  {
    id: "mortgage",
    label: "Mortgage",
    group: "Liabilities",
    itemType: "liability",
    liabilityType: "mortgage",
    divisible: false,
    proxyable: false,
  },
  {
    id: "loan",
    label: "Loan",
    group: "Liabilities",
    itemType: "liability",
    liabilityType: "loan",
    divisible: false,
    proxyable: false,
  },
  {
    id: "other-liability",
    label: "Other liability",
    group: "Liabilities",
    itemType: "liability",
    liabilityType: "other",
    divisible: false,
    proxyable: false,
  },
  {
    id: "custom",
    label: "Something else…",
    group: "Other",
    itemType: "asset",
    divisible: true,
    proxyable: true,
  },
];

export const CUSTOM_KIND_ID = "custom";

export function getKind(id: string): HoldingKind {
  return HOLDING_KINDS.find((kind) => kind.id === id) ?? HOLDING_KINDS[0];
}

/** Finds the preset matching an existing holding, falling back to the custom escape hatch. */
export function kindOfEntry(entry: PortfolioEntry): HoldingKind {
  if (entry.itemType === "liability") {
    return (
      HOLDING_KINDS.find(
        (kind) =>
          kind.itemType === "liability" &&
          kind.liabilityType === entry.liabilityType,
      ) ?? getKind("other-liability")
    );
  }
  return (
    HOLDING_KINDS.find(
      (kind) =>
        kind.itemType === "asset" &&
        entry.assetType !== null &&
        (kind.matches ?? []).includes(entry.assetType),
    ) ?? getKind(CUSTOM_KIND_ID)
  );
}

/**
 * What to open a fresh holding on: whatever the section already mostly holds, so adding a second
 * gold bar in a metals section does not start on "residential property".
 */
export function suggestedKind(entries: PortfolioEntry[]): HoldingKind {
  const counts = new Map<string, number>();
  for (const entry of entries) {
    const id = kindOfEntry(entry).id;
    counts.set(id, (counts.get(id) ?? 0) + 1);
  }
  let best: string | null = null;
  let bestCount = 0;
  for (const [id, count] of counts) {
    if (count > bestCount) {
      best = id;
      bestCount = count;
    }
  }
  return best ? getKind(best) : getKind("home");
}

/**
 * Applies everything a kind implies to an existing holding: its classification, and the fields
 * that stop making sense with it. Switching a tracked ETF to a house has to drop the proxy, and
 * anything indivisible goes back to a single unit.
 *
 * Only for when the kind actually changes — the dialog enforces the same rules through which
 * fields it shows.
 */
export function applyKind(
  payload: PortfolioEntryPayload,
  kind: HoldingKind,
): PortfolioEntryPayload {
  const isLiability = kind.itemType === "liability";
  const keepsProxy = kind.proxyable && payload.priceSource === "proxy";
  return {
    ...payload,
    itemType: kind.itemType,
    assetClass: isLiability ? null : (kind.assetClass ?? payload.assetClass),
    assetType: isLiability ? null : (kind.assetType ?? payload.assetType),
    liabilityType: isLiability ? (kind.liabilityType ?? "other") : null,
    priceSource: keepsProxy ? "proxy" : "manual",
    proxySymbol: keepsProxy ? payload.proxySymbol : null,
    units: kind.divisible || keepsProxy ? payload.units : 1,
  };
}

/**
 * The full description of a holding, as the API expects it back.
 *
 * `isinCode` is carried through untouched even though nothing in the UI shows or edits it: an
 * imported holding may already have one, it reaches snapshots and the reports built on them, and
 * dropping it here would quietly erase it on the next edit.
 */
export function entryToPayload(entry: PortfolioEntry): PortfolioEntryPayload {
  return {
    itemType: entry.itemType,
    name: entry.name,
    assetClass: entry.assetClass,
    assetType: entry.assetType,
    liabilityType: entry.liabilityType,
    currency: entry.currency,
    units: entry.units,
    priceSource: entry.priceSource,
    manualUnitPrice: entry.manualUnitPrice,
    proxySymbol: entry.proxySymbol,
    isinCode: entry.isinCode,
    customValues: entry.customValues,
  };
}
