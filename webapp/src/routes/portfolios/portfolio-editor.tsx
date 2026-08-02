import React, { useCallback, useContext, useEffect, useState } from "react";
import { useNavigate, useParams, NavLink } from "react-router-dom";
import { toast } from "sonner";
import { DateTime } from "luxon";
import { ArrowLeft, MoreHorizontal, Plus, Trash2 } from "lucide-react";

import AuthContext from "contexts/auth/auth-context";
import {
  useApi,
  AccountSubTypes,
  AccountType,
  AssetClassFormattingRule,
  AssetTypeFormattingRule,
  FormattingRulesApi,
  LinkedAccountsValuationApi,
  Portfolio,
  PortfolioCustomColumn,
  PortfolioEntry,
  PortfolioEntryPayload,
  PortfoliosApi,
  PortfolioSection,
  PortfolioSectionPayload,
} from "clients";
import { formatApiError } from "utils/errors";
import { useDocumentTitle } from "hooks/use-document-title";

import {
  ColourPicker,
  DEFAULT_ACCOUNT_COLOURS,
} from "components/colour-picker";
import { Combobox, ComboboxGroup } from "components/combobox";
import { EditableCell } from "components/editable-cell";
import { Button } from "components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "components/ui/dropdown-menu";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "components/ui/select";
import { Skeleton } from "components/ui/skeleton";
import { cn } from "lib/utils";

import { freshnessOf, needsReview } from "./attestation";
import { currencyGroups } from "./currencies";
import { PriceCell } from "./price-cell";
import { PortfolioViewSwitch } from "./view-switch";
import {
  AddColumnButton,
  ColumnType,
  CustomColumnHeader,
  makeColumnKey,
} from "./custom-columns";
import {
  HOLDING_KINDS,
  HoldingKind,
  applyKind,
  entryToPayload,
  getKind,
  kindOfEntry,
  suggestedKind,
} from "./holding-kinds";

type AccountSubTypesMap = Partial<Record<AccountType, string[]>>;

const ACCOUNT_KIND_SEPARATOR = "\u0000";

/** Account type and sub type travel as one value so they can be picked as one question. */
function accountKindValue(type: string, subType: string | null): string {
  return `${type}${ACCOUNT_KIND_SEPARATOR}${subType ?? ""}`;
}

function parseAccountKind(value: string): [AccountType, string | null] {
  const [type, subType] = value.split(ACCOUNT_KIND_SEPARATOR);
  return [type as AccountType, subType ? subType : null];
}

function buildAccountKindGroups(subTypes: AccountSubTypesMap): ComboboxGroup[] {
  return Object.values(AccountType).map((accountType) => {
    const options = subTypes[accountType] ?? [];
    return {
      label: accountType,
      options:
        options.length > 0
          ? options.map((subType) => ({
              value: accountKindValue(accountType, subType),
              label: subType,
              hint: accountType,
            }))
          : [
              {
                value: accountKindValue(accountType, null),
                label: accountType,
              },
            ],
    };
  });
}

/** "other" says nothing in particular, which is the right default; "529" is not. */
function defaultSubType(subTypes: string[]): string | null {
  return subTypes.find((subType) => subType === "other") ?? subTypes[0] ?? null;
}

function formatMoney(
  amount: number,
  currency: string,
  maximumFractionDigits = 2,
): string {
  try {
    return new Intl.NumberFormat(undefined, {
      style: "currency",
      currency,
      maximumFractionDigits,
    }).format(amount);
  } catch {
    return `${amount.toLocaleString()} ${currency}`;
  }
}

function formatUnits(units: number): string {
  return Number.isInteger(units)
    ? String(units)
    : units.toLocaleString(undefined, { maximumFractionDigits: 4 });
}

interface AssetFormatting {
  classes: Record<string, AssetClassFormattingRule>;
  types: Record<string, AssetTypeFormattingRule>;
}

/**
 * Entries carry their own currency, so a section subtotal is only meaningful per currency: FX
 * conversion happens in the valuation pipeline, and the editor holds no rates of its own.
 */
function sectionTotals(section: PortfolioSection): Array<[string, number]> {
  const totals = new Map<string, number>();
  for (const entry of section.entries) {
    if (entry.value === null) {
      continue;
    }
    totals.set(entry.currency, (totals.get(entry.currency) ?? 0) + entry.value);
  }
  if (totals.size === 0) {
    totals.set(section.currency, 0);
  }
  return [...totals.entries()].sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]));
}

const Eyebrow: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className,
}) => (
  <span
    className={cn(
      "text-[10px] font-medium uppercase tracking-[0.11em] text-muted-foreground",
      className,
    )}
  >
    {children}
  </span>
);

// --- Section table ---

interface SectionTableProps {
  section: PortfolioSection;
  formatting: AssetFormatting | null;
  totals: Array<[string, number]>;
  currenciesInUse: string[];
  onAddEntry: () => void;
  onEntryPatch: (
    entry: PortfolioEntry,
    changes: Partial<PortfolioEntryPayload>,
  ) => Promise<void>;
  onDeleteEntry: (entry: PortfolioEntry) => void;
  onColumnsChange: (columns: PortfolioCustomColumn[]) => Promise<void>;
  onKindChange: (entry: PortfolioEntry, kind: HoldingKind) => Promise<void>;
}

const SectionTable: React.FC<SectionTableProps> = ({
  section,
  formatting,
  totals,
  currenciesInUse,
  onAddEntry,
  onEntryPatch,
  onDeleteEntry,
  onColumnsChange,
  onKindChange,
}) => {
  const customColumns = section.customColumns ?? [];
  // Units only carry information when something is actually divisible: a house is always one
  // house, so a column of 1s is dropped rather than shown.
  const showUnits = section.entries.some(
    (entry) => entry.itemType !== "liability" && entry.units !== 1,
  );
  const columnCount = 3 + (showUnits ? 1 : 0) + customColumns.length;

  const renameColumn = (index: number, label: string) => {
    const current = customColumns[index];
    // The key addresses stored values and travels into snapshots, so it normally stays put. While
    // nothing has been filled in yet there is nothing to orphan, so a freshly added column can
    // take the name it is given.
    const inUse = section.entries.some(
      (entry) => (entry.customValues?.[current.key] ?? "") !== "",
    );
    const key = inUse
      ? current.key
      : makeColumnKey(
          label,
          customColumns.filter((_, i) => i !== index).map((c) => c.key),
        );
    return onColumnsChange(
      customColumns.map((column, i) =>
        i === index ? { ...column, key, label } : column,
      ),
    );
  };
  const retypeColumn = (index: number, type: ColumnType) =>
    onColumnsChange(
      customColumns.map((column, i) =>
        i === index ? { ...column, type } : column,
      ),
    );
  const removeColumn = (index: number) =>
    onColumnsChange(customColumns.filter((_, i) => i !== index));
  const addColumn = () => {
    const label = "New column";
    return onColumnsChange([
      ...customColumns,
      {
        key: makeColumnKey(
          label,
          customColumns.map((column) => column.key),
        ),
        label,
        type: "text",
      },
    ]);
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr className="border-y border-border/50">
            <th className="py-2 pl-2.5 text-left md:pl-3">
              <Eyebrow>Holding</Eyebrow>
            </th>
            {showUnits && (
              <th className="py-2 pr-2 text-right md:pr-4">
                <Eyebrow>Units</Eyebrow>
              </th>
            )}
            <th className="py-2 pr-2 text-right md:pr-4">
              <Eyebrow>Unit price</Eyebrow>
            </th>
            <th className="py-2 pr-2 text-right md:pr-4">
              <Eyebrow>Value</Eyebrow>
            </th>
            {customColumns.map((column, index) => (
              <th
                key={column.key}
                className={cn(
                  "hidden py-2 pr-4 text-left align-middle md:table-cell",
                  index === 0 && "border-l border-border/60 pl-3",
                )}
              >
                <CustomColumnHeader
                  column={column}
                  onRename={(label) => renameColumn(index, label)}
                  onTypeChange={(type) => retypeColumn(index, type)}
                  onRemove={() => removeColumn(index)}
                />
              </th>
            ))}
            <th
              className={cn(
                "hidden w-8 py-2 md:table-cell",
                customColumns.length === 0 && "border-l border-border/60 pl-3",
              )}
            >
              <AddColumnButton onAdd={addColumn} />
            </th>
            <th className="w-8" />
          </tr>
        </thead>
        <tbody>
          {section.entries.map((entry) => {
            const isLiability = entry.itemType === "liability";
            const classRule = entry.assetClass
              ? formatting?.classes[entry.assetClass]
              : undefined;
            const typeRule = entry.assetType
              ? formatting?.types[entry.assetType]
              : undefined;
            const kindLabel = isLiability
              ? kindOfEntry(entry).label
              : (typeRule?.prettyName ?? entry.assetType ?? "");
            return (
              <tr
                key={entry.id}
                className="group border-b border-border/40 last:border-b-0"
              >
                <td className="relative py-2.5 pl-2.5 pr-2 align-middle md:pl-3 md:pr-4">
                  <span
                    aria-hidden="true"
                    className="absolute inset-y-1.5 left-0 w-[2px] rounded-full"
                    style={{
                      backgroundColor: isLiability
                        ? "hsl(var(--muted-foreground) / 0.35)"
                        : (classRule?.dominantColour ??
                          "hsl(var(--muted-foreground) / 0.35)"),
                    }}
                    title={
                      isLiability
                        ? "Liability"
                        : (classRule?.prettyName ?? undefined)
                    }
                  />
                  <EditableCell
                    value={entry.name}
                    onSave={(name) => onEntryPatch(entry, { name })}
                    className="font-medium text-foreground"
                  />
                  <Select
                    value={kindOfEntry(entry).id}
                    onValueChange={(id) => onKindChange(entry, getKind(id))}
                  >
                    <SelectTrigger
                      aria-label={`Kind of ${entry.name}`}
                      className="h-auto w-auto justify-start gap-1 border-0 bg-transparent px-1 py-0 text-[11px] leading-tight text-muted-foreground shadow-none hover:text-foreground focus:ring-0 focus-visible:ring-2 focus-visible:ring-ring [&>svg]:h-3 [&>svg]:w-3 [&>svg]:opacity-0 group-hover:[&>svg]:opacity-60"
                    >
                      {/* Shows the holding's own classification, which may be finer grained than
                          any preset (an imported ETF is not just "Fund or ETF"). */}
                      <SelectValue>{kindLabel}</SelectValue>
                    </SelectTrigger>
                    <SelectContent>
                      {(["Assets", "Liabilities"] as const).map((group) => (
                        <SelectGroup key={group}>
                          <SelectLabel>{group}</SelectLabel>
                          {HOLDING_KINDS.filter((k) => k.group === group).map(
                            (k) => (
                              <SelectItem key={k.id} value={k.id}>
                                {k.label}
                              </SelectItem>
                            ),
                          )}
                        </SelectGroup>
                      ))}
                    </SelectContent>
                  </Select>
                </td>
                {showUnits && (
                  <td className="py-2.5 pr-2 text-right align-middle font-mono text-[12.5px] tabular-nums text-muted-foreground md:pr-4">
                    {isLiability ? (
                      <span className="pr-1">—</span>
                    ) : (
                      <EditableCell
                        value={String(entry.units)}
                        display={formatUnits(entry.units)}
                        align="right"
                        type="number"
                        onSave={(units) =>
                          onEntryPatch(entry, { units: Number(units) })
                        }
                      />
                    )}
                  </td>
                )}
                <td className="py-2.5 pr-2 align-middle md:pr-4">
                  <PriceCell
                    entry={entry}
                    kind={kindOfEntry(entry)}
                    currenciesInUse={currenciesInUse}
                    showUnits={showUnits}
                    formatMoney={(amount, currency) =>
                      formatMoney(amount, currency)
                    }
                    onPatch={(changes) => onEntryPatch(entry, changes)}
                  />
                </td>
                <td
                  className={cn(
                    "py-2.5 pr-2 text-right align-middle font-mono text-[14px] font-semibold tabular-nums md:pr-4",
                    isLiability && "text-muted-foreground",
                  )}
                >
                  {entry.value !== null ? (
                    formatMoney(entry.value, entry.currency, 0)
                  ) : (
                    <span className="text-muted-foreground">—</span>
                  )}
                </td>
                {customColumns.map((column, index) => (
                  <td
                    key={column.key}
                    className={cn(
                      "hidden max-w-[11rem] py-2.5 pr-4 align-middle md:table-cell",
                      index === 0 && "border-l border-border/60 pl-3",
                    )}
                  >
                    <EditableCell
                      value={entry.customValues?.[column.key] ?? ""}
                      type={column.type === "number" ? "number" : "text"}
                      className="text-[12.5px] text-muted-foreground"
                      align={column.type === "number" ? "right" : "left"}
                      onSave={(value) =>
                        onEntryPatch(entry, {
                          customValues: {
                            ...entry.customValues,
                            [column.key]: value,
                          },
                        })
                      }
                    />
                  </td>
                ))}
                <td className="hidden md:table-cell" />
                <td className="py-2.5 pr-0 align-middle md:pr-1">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button
                        size="icon"
                        variant="ghost"
                        aria-label={`Actions for ${entry.name}`}
                        className="h-7 w-7 opacity-0 transition-opacity group-focus-within:opacity-100 group-hover:opacity-100 data-[state=open]:opacity-100"
                      >
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuLabel className="text-xs font-normal text-muted-foreground">
                        Delete {entry.name}?
                      </DropdownMenuLabel>
                      <DropdownMenuItem
                        className="text-destructive"
                        onClick={() => onDeleteEntry(entry)}
                      >
                        <Trash2 className="mr-2 h-3.5 w-3.5" />
                        Delete holding
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </td>
              </tr>
            );
          })}
          {/* The next, empty row: adding a holding happens where the holding will appear. */}
          <tr className="group/add border-b border-border/40">
            <td colSpan={columnCount + 2} className="p-0">
              <button
                type="button"
                onClick={onAddEntry}
                aria-label={
                  section.entries.length === 0
                    ? "Add the first holding"
                    : "Add a holding"
                }
                className="flex w-full items-center gap-1.5 py-2.5 pl-2.5 text-left text-[11px] text-muted-foreground transition-colors hover:bg-accent/40 focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring md:pl-3"
              >
                <Plus className="h-3.5 w-3.5 shrink-0" />
                <span
                  className={cn(
                    "transition-opacity",
                    section.entries.length > 0 &&
                      "opacity-0 group-hover/add:opacity-100",
                  )}
                >
                  {section.entries.length === 0
                    ? "Add the first holding"
                    : "Add a holding"}
                </span>
              </button>
            </td>
          </tr>
        </tbody>
        <tfoot hidden={section.entries.length === 0}>
          <tr className="border-t border-border/50">
            <td
              colSpan={showUnits ? 3 : 2}
              className="py-2.5 pl-2.5 pr-2 text-right md:pl-3 md:pr-4"
            >
              <Eyebrow>Section total</Eyebrow>
            </td>
            <td className="py-2.5 pr-2 text-right align-top md:pr-4">
              {section.estimatedValue !== null ? (
                // Sections report in their own currency, as the header above says they do.
                <span className="block font-mono text-[14px] font-semibold tabular-nums">
                  {formatMoney(section.estimatedValue, section.currency, 0)}
                </span>
              ) : (
                // No rates available: fall back to what can be stated without converting.
                totals.map(([currency, total]) => (
                  <span
                    key={currency}
                    className="block font-mono text-[14px] font-semibold tabular-nums"
                  >
                    {formatMoney(total, currency, 0)}
                  </span>
                ))
              )}
            </td>
            <td
              className="hidden md:table-cell"
              colSpan={columnCount - 3 + 1}
            />
          </tr>
        </tfoot>
      </table>
    </div>
  );
};

// --- Page ---

export const PortfolioEditor: React.FC = () => {
  const { userAccountId } = useContext(AuthContext);
  const { portfolioId: portfolioIdParam } = useParams<{
    portfolioId: string;
  }>();
  const portfolioId = Number(portfolioIdParam);
  const portfoliosApi = useApi(PortfoliosApi);
  const formattingRulesApi = useApi(FormattingRulesApi);
  const valuationApi = useApi(LinkedAccountsValuationApi);
  const navigate = useNavigate();

  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [accountSubTypes, setAccountSubTypes] = useState<AccountSubTypesMap>(
    {},
  );
  const [formatting, setFormatting] = useState<AssetFormatting | null>(null);
  const [palette, setPalette] = useState<string[]>(DEFAULT_ACCOUNT_COLOURS);
  const [valuation, setValuation] = useState<{
    value: number;
    currency: string;
    date: Date;
  } | null>(null);
  useDocumentTitle(portfolio?.name ?? "Portfolio");

  const load = useCallback(async () => {
    try {
      const response = await portfoliosApi.getPortfolio({
        userAccountId: userAccountId!,
        portfolioId,
      });
      setPortfolio(response.portfolio);
    } catch (e) {
      toast.error(formatApiError(e));
    }
  }, [portfoliosApi, userAccountId, portfolioId]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    const fetchReference = async () => {
      try {
        const [subTypes, assets, accounts] = await Promise.all([
          formattingRulesApi.getAccountSubTypes(),
          formattingRulesApi.getAssetsFormattingRules(),
          formattingRulesApi.getAccountsFormattingRules(),
        ]);
        if (accounts.colourPalette.length > 0) {
          setPalette(accounts.colourPalette);
        }
        setAccountSubTypes(
          Object.fromEntries(
            subTypes.accountSubTypes.map((entry: AccountSubTypes) => [
              entry.accountType,
              entry.subTypes,
            ]),
          ),
        );
        setFormatting({
          classes: Object.fromEntries(
            assets.assetClasses.map((rule) => [rule.assetClass, rule]),
          ),
          types: Object.fromEntries(
            assets.assetTypes.map((rule) => [rule.assetType, rule]),
          ),
        });
      } catch (e) {
        toast.error(formatApiError(e));
      }
    };
    fetchReference();
  }, [formattingRulesApi]);

  // The authoritative, currency-converted number comes from the last snapshot: the editor itself
  // has no FX rates, and this is what the rest of Finbot believes the portfolio is worth.
  const loadValuation = useCallback(
    async (linkedAccountId: number) => {
      try {
        const response = await valuationApi.getLinkedAccountsValuation({
          userAccountId: userAccountId!,
        });
        const entry = response.valuation.entries.find(
          (candidate) => candidate.linkedAccount.id === linkedAccountId,
        );
        setValuation(
          entry
            ? {
                value: entry.valuation.value,
                currency: entry.valuation.currency,
                date: entry.valuation.date,
              }
            : null,
        );
      } catch {
        setValuation(null);
      }
    },
    [valuationApi, userAccountId],
  );

  useEffect(() => {
    if (portfolio) {
      loadValuation(portfolio.linkedAccountId);
    }
  }, [portfolio, loadValuation]);

  const runMutation = async (
    action: () => Promise<{ portfolio: Portfolio }>,
    successMessage?: string,
  ) => {
    try {
      const response = await action();
      setPortfolio(response.portfolio);
      if (successMessage) {
        toast.success(successMessage);
      }
    } catch (e) {
      toast.error(formatApiError(e));
      await load();
      throw e;
    }
  };

  const patchEntry = async (
    entry: PortfolioEntry,
    changes: Partial<PortfolioEntryPayload>,
  ) => {
    await runMutation(() =>
      portfoliosApi.updatePortfolioEntry({
        userAccountId: userAccountId!,
        portfolioId,
        entryId: entry.id,
        portfolioEntryPayload: { ...entryToPayload(entry), ...changes },
      }),
    );
  };

  const updateSection = async (
    section: PortfolioSection,
    changes: Partial<PortfolioSectionPayload>,
  ) => {
    await runMutation(() =>
      portfoliosApi.updatePortfolioSection({
        userAccountId: userAccountId!,
        portfolioId,
        sectionId: section.id,
        portfolioSectionPayload: {
          name: section.name,
          currency: section.currency,
          accountType: section.accountType,
          accountSubType: section.accountSubType,
          customColumns: section.customColumns,
          ...changes,
        },
      }),
    );
  };

  /**
   * Reclassifying a holding says what it is, not what it is worth, so the change is made to hold
   * its value steady: a dropped proxy freezes at the last price read, and units folded away by an
   * indivisible kind are folded into the price instead of disappearing.
   */
  const changeKind = async (entry: PortfolioEntry, kind: HoldingKind) => {
    const current = entryToPayload(entry);
    const next = applyKind(current, kind);
    if (next.priceSource === "manual" && next.manualUnitPrice == null) {
      next.manualUnitPrice =
        current.priceSource === "proxy"
          ? (entry.lastResolvedUnitPrice ?? 0)
          : (current.manualUnitPrice ?? 0);
    }
    const previousUnits = current.units ?? 1;
    if (
      (next.units ?? 1) === 1 &&
      previousUnits !== 1 &&
      next.manualUnitPrice != null
    ) {
      next.manualUnitPrice = next.manualUnitPrice * previousUnits;
    }
    // The magnitude is what it is worth; the sign is part of what it is. Crossing between asset
    // and liability keeps the amount and flips the sign, so a converted holding never counts the
    // wrong way in net worth.
    if (next.itemType !== current.itemType && next.manualUnitPrice != null) {
      const magnitude = Math.abs(next.manualUnitPrice);
      next.manualUnitPrice =
        next.itemType === "liability" ? -magnitude : magnitude;
    }
    await patchEntry(entry, next);
  };

  const addSection = async () => {
    const currency =
      portfolio?.sections[0]?.currency ?? portfolio?.valuationCcy ?? "GBP";
    const subTypes = accountSubTypes[AccountType.Investment] ?? [];
    await runMutation(
      () =>
        portfoliosApi.createPortfolioSection({
          userAccountId: userAccountId!,
          portfolioId,
          portfolioSectionPayload: {
            name: "New section",
            currency,
            accountType: AccountType.Investment,
            accountSubType: defaultSubType(subTypes),
            customColumns: [],
          },
        }),
      "Section added, name it above",
    );
  };

  /**
   * New holdings are created straight away and filled in on the row. The kind is taken from what
   * the section already holds, so the common case needs a name and an amount and nothing else.
   */
  const addEntry = async (section: PortfolioSection) => {
    const kind = suggestedKind(section.entries);
    await runMutation(
      () =>
        portfoliosApi.createPortfolioEntry({
          userAccountId: userAccountId!,
          portfolioId,
          sectionId: section.id,
          portfolioEntryPayload: {
            itemType: kind.itemType,
            name: "New holding",
            assetClass: kind.assetClass ?? null,
            assetType: kind.assetType ?? null,
            liabilityType:
              kind.itemType === "liability"
                ? (kind.liabilityType ?? "other")
                : null,
            currency: section.entries[0]?.currency ?? section.currency,
            units: 1,
            priceSource: "manual",
            manualUnitPrice: 0,
            proxySymbol: null,
            customValues: {},
          },
        }),
      "Holding added, fill it in on the row",
    );
  };

  const deleteEntry = async (entry: PortfolioEntry) => {
    const restore = entryToPayload(entry);
    const sectionId = portfolio?.sections.find((section) =>
      section.entries.some((candidate) => candidate.id === entry.id),
    )?.id;
    try {
      await runMutation(() =>
        portfoliosApi.deletePortfolioEntry({
          userAccountId: userAccountId!,
          portfolioId,
          entryId: entry.id,
        }),
      );
      // Deleting a row outright would be unforgiving without a way back.
      toast.success(`Deleted ${entry.name}`, {
        action: sectionId
          ? {
              label: "Undo",
              onClick: () => {
                runMutation(() =>
                  portfoliosApi.createPortfolioEntry({
                    userAccountId: userAccountId!,
                    portfolioId,
                    sectionId,
                    portfolioEntryPayload: restore,
                  }),
                ).catch(() => undefined);
              },
            }
          : undefined,
      });
    } catch {
      // runMutation already reported the failure
    }
  };

  const deleteSection = async (section: PortfolioSection) => {
    await runMutation(
      () =>
        portfoliosApi.deletePortfolioSection({
          userAccountId: userAccountId!,
          portfolioId,
          sectionId: section.id,
        }),
      "Section deleted",
    ).catch(() => undefined);
  };

  const deletePortfolio = async () => {
    try {
      await portfoliosApi.deletePortfolio({
        userAccountId: userAccountId!,
        portfolioId,
      });
      toast.success("Portfolio deleted");
      navigate("/portfolios");
    } catch (e) {
      toast.error(formatApiError(e));
    }
  };

  const updateDetails = async (changes: { name?: string; colour?: string }) => {
    try {
      const response = await portfoliosApi.updatePortfolio({
        userAccountId: userAccountId!,
        portfolioId,
        updatePortfolioRequest: changes,
      });
      setPortfolio(response.portfolio);
    } catch (e) {
      toast.error(formatApiError(e));
    }
  };

  if (portfolio === null) {
    return (
      <div className="container mx-auto space-y-6 px-6 pt-8">
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-20 w-72" />
        <Skeleton className="h-56" />
      </div>
    );
  }

  const allEntries = portfolio.sections.flatMap((section) => section.entries);
  const currenciesInUse = [
    portfolio.valuationCcy,
    ...portfolio.sections.map((section) => section.currency),
    ...allEntries.map((entry) => entry.currency),
  ];
  const accountKindGroups = buildAccountKindGroups(accountSubTypes);
  const reviewCount = allEntries.filter((entry) =>
    needsReview(freshnessOf(entry.priceSource, entry.manualPriceUpdatedAt)),
  ).length;
  const holdingsCount = allEntries.length;

  return (
    <div className="container mx-auto px-6 pb-48 pt-8">
      {/* The portfolio's worth is the thesis of this page, so it leads. */}
      <header className="mb-10">
        <NavLink
          to="/portfolios"
          className="inline-flex items-center gap-1.5 text-xs text-muted-foreground transition-colors hover:text-foreground"
        >
          <ArrowLeft className="h-3 w-3" />
          All portfolios
        </NavLink>

        <div className="mt-3 flex flex-wrap items-start justify-between gap-x-8 gap-y-4">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <ColourPicker
                colour={portfolio.colour}
                colours={palette}
                label="Portfolio colour"
                onChange={(colour) => updateDetails({ colour })}
              />
              <h1 className="min-w-0 font-register text-[19px] font-semibold tracking-tight">
                <EditableCell
                  value={portfolio.name}
                  onSave={(name) => updateDetails({ name })}
                  className="font-register text-[19px] font-semibold"
                />
              </h1>
            </div>

            {/* The live estimate leads, because it is the number that answers what you just
                typed. The confirmed valuation from the last snapshot sits beside it. */}
            <div className="mt-4">
              {portfolio.estimatedValue !== null && (
                <Eyebrow className="block">Estimated value</Eyebrow>
              )}
              <p className="mt-1 font-register text-[44px] font-light leading-none tracking-tight tabular-nums">
                {portfolio.estimatedValue !== null
                  ? formatMoney(
                      portfolio.estimatedValue,
                      portfolio.valuationCcy,
                      0,
                    )
                  : valuation
                    ? formatMoney(valuation.value, valuation.currency, 0)
                    : "—"}
              </p>
            </div>

            <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
              {portfolio.estimatedValue !== null && (
                <>
                  <span>
                    Updates as you edit, using the last prices read for tracked
                    holdings
                  </span>
                  <span aria-hidden="true">·</span>
                </>
              )}
              <span>
                {valuation
                  ? `Confirmed ${DateTime.fromJSDate(valuation.date).toRelative()}`
                  : "Not yet valued"}
              </span>
              <span aria-hidden="true">·</span>
              <span>
                {holdingsCount} {holdingsCount === 1 ? "holding" : "holdings"}{" "}
                in {portfolio.sections.length}{" "}
                {portfolio.sections.length === 1 ? "section" : "sections"}
              </span>
              {reviewCount > 0 && (
                <>
                  <span aria-hidden="true">·</span>
                  <span className="text-attest-stale">
                    {reviewCount}{" "}
                    {reviewCount === 1 ? "valuation is" : "valuations are"} over
                    18 months old
                  </span>
                </>
              )}
            </div>
          </div>

          <div className="flex shrink-0 items-center gap-2">
            <PortfolioViewSwitch
              portfolioId={portfolio.id}
              linkedAccountId={portfolio.linkedAccountId}
              current="holdings"
            />
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  size="icon"
                  variant="ghost"
                  aria-label="Portfolio actions"
                  className="h-8 w-8"
                >
                  <MoreHorizontal className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuLabel className="text-xs font-normal text-muted-foreground">
                  Delete this portfolio? Past valuations are kept.
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  className="text-destructive"
                  onClick={deletePortfolio}
                >
                  <Trash2 className="mr-2 h-3.5 w-3.5" />
                  Delete portfolio
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </header>

      {portfolio.sections.length === 0 && (
        <div className="flex flex-col items-center gap-3 border-y border-dashed border-border py-16 text-center">
          <p className="font-register text-base font-semibold">
            Nothing recorded yet
          </p>
          <p className="max-w-sm text-sm text-muted-foreground">
            Sections group your holdings and are reported as sub-accounts. Add
            one per kind of asset: property, metals, vehicles.
          </p>
          <Button size="sm" variant="outline" onClick={addSection}>
            <Plus className="mr-1.5 h-3.5 w-3.5" />
            Add section
          </Button>
        </div>
      )}

      <div className="space-y-12">
        {portfolio.sections.map((section) => {
          const totals = sectionTotals(section);
          return (
            <section key={section.id}>
              <div className="mb-3 flex flex-wrap items-end justify-between gap-x-6 gap-y-2">
                <div className="min-w-0">
                  <h2 className="font-register text-[17px] font-semibold tracking-tight">
                    <EditableCell
                      value={section.name}
                      className="font-register text-[17px] font-semibold"
                      onSave={(name) => updateSection(section, { name })}
                    />
                  </h2>
                  {/* Everything that describes the section is set here rather than behind a
                      settings screen. */}
                  {/* Everything that describes the section is set here rather than behind a
                      settings screen. Type and sub type are one question, because picking a
                      "brokerage" already tells you the account is an investment. */}
                  <div className="mt-0.5 flex flex-wrap items-center gap-x-1 text-[11px] text-muted-foreground">
                    <span>Reports in</span>
                    <Combobox
                      value={section.currency}
                      groups={currencyGroups([
                        section.currency,
                        portfolio.valuationCcy,
                        ...currenciesInUse,
                      ])}
                      label={`Currency for ${section.name}`}
                      searchPlaceholder="Find a currency"
                      triggerClassName="font-mono uppercase hover:text-foreground"
                      onChange={(currency) =>
                        updateSection(section, { currency })
                      }
                    />
                    <span aria-hidden="true">·</span>
                    <Combobox
                      value={accountKindValue(
                        section.accountType,
                        section.accountSubType,
                      )}
                      groups={accountKindGroups}
                      label={`Account type for ${section.name}`}
                      searchPlaceholder="Find an account type"
                      contentClassName="w-64"
                      display={
                        <span className="truncate">
                          {section.accountType}
                          {section.accountSubType
                            ? ` · ${section.accountSubType}`
                            : ""}
                        </span>
                      }
                      triggerClassName="hover:text-foreground"
                      onChange={(next) => {
                        const [accountType, accountSubType] =
                          parseAccountKind(next);
                        return updateSection(section, {
                          accountType,
                          accountSubType,
                        });
                      }}
                    />
                  </div>
                </div>
                <div className="flex items-end gap-4">
                  <div className="flex items-center gap-1">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button
                          type="button"
                          size="icon"
                          variant="ghost"
                          aria-label={`Actions for ${section.name}`}
                          className="h-8 w-8"
                        >
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuLabel className="text-xs font-normal text-muted-foreground">
                          Delete {section.name} and its {section.entries.length}{" "}
                          {section.entries.length === 1
                            ? "holding"
                            : "holdings"}
                          ?
                        </DropdownMenuLabel>
                        <DropdownMenuItem
                          className="text-destructive"
                          onClick={() => deleteSection(section)}
                        >
                          <Trash2 className="mr-2 h-3.5 w-3.5" />
                          Delete section
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
              </div>

              <SectionTable
                section={section}
                formatting={formatting}
                totals={totals}
                currenciesInUse={currenciesInUse}
                onAddEntry={() => addEntry(section)}
                onEntryPatch={patchEntry}
                onDeleteEntry={deleteEntry}
                onColumnsChange={(customColumns) =>
                  updateSection(section, { customColumns })
                }
                onKindChange={changeKind}
              />
            </section>
          );
        })}

        {portfolio.sections.length > 0 && (
          <Button
            size="sm"
            variant="ghost"
            className="text-muted-foreground"
            onClick={addSection}
          >
            <Plus className="mr-1.5 h-3.5 w-3.5" />
            Add section
          </Button>
        )}
      </div>
    </div>
  );
};

export default PortfolioEditor;
