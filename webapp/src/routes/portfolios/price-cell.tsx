import React, { useState } from "react";
import { toast } from "sonner";
import { ChevronDown, Loader2 } from "lucide-react";

import {
  useApi,
  PortfolioEntry,
  PortfolioEntryPayload,
  SecuritiesApi,
} from "clients";
import { formatApiError } from "utils/errors";

import { Combobox } from "components/combobox";
import { EditableCell } from "components/editable-cell";
import { Button } from "components/ui/button";
import { Input } from "components/ui/input";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "components/ui/dropdown-menu";

import { Attestation } from "./attestation";
import { currencyGroups } from "./currencies";
import { HoldingKind } from "./holding-kinds";

interface PriceCellProps {
  entry: PortfolioEntry;
  kind: HoldingKind;
  /** Currencies already used nearby, offered before the full ISO list. */
  currenciesInUse: string[];
  /** Label the amount as a total when the holding cannot be divided. */
  showUnits: boolean;
  formatMoney: (amount: number, currency: string) => string;
  onPatch: (changes: Partial<PortfolioEntryPayload>) => Promise<void>;
}

/**
 * Everything about how a holding is priced, in the cell that shows the price: the amount, the
 * currency, which security stands in for it, and which of the two is in charge.
 */
export const PriceCell: React.FC<PriceCellProps> = ({
  entry,
  kind,
  currenciesInUse,
  showUnits,
  formatMoney,
  onPatch,
}) => {
  const securitiesApi = useApi(SecuritiesApi);
  const [resolving, setResolving] = useState(false);
  // A holding cannot be stored as tracked until it has a symbol to track, so choosing to track is
  // a state of this cell until the symbol resolves.
  const [enteringSymbol, setEnteringSymbol] = useState(false);
  const isProxy = entry.priceSource === "proxy";

  const trackSymbol = async (symbol: string) => {
    const trimmed = symbol.trim();
    if (!trimmed) {
      return;
    }
    setResolving(true);
    try {
      // Checking first means a typo is caught here rather than silently valuing at nothing.
      const { quote } = await securitiesApi.resolveSecurity({
        symbol: trimmed,
      });
      await onPatch({
        priceSource: "proxy",
        proxySymbol: trimmed,
        currency: quote.currency,
        manualUnitPrice: null,
      });
      toast.success(`Tracking ${quote.name ?? quote.symbol}`);
      setEnteringSymbol(false);
    } catch (e) {
      toast.error(formatApiError(e));
    } finally {
      setResolving(false);
    }
  };

  const setOwnPrice = () => {
    setEnteringSymbol(false);
    return onPatch({
      priceSource: "manual",
      proxySymbol: null,
      // Freeze the last price read so the holding keeps its value.
      manualUnitPrice: entry.lastResolvedUnitPrice ?? 0,
    });
  };

  return (
    <div className="group/price flex items-start justify-end gap-0.5">
      <div className="min-w-0 flex-1 text-right">
        {enteringSymbol && !isProxy ? (
          <Input
            autoFocus
            aria-label={`Symbol to track for ${entry.name}`}
            placeholder="GC=F, SGLN.L…"
            disabled={resolving}
            className="h-7 text-right font-mono text-[13px]"
            onBlur={(e) =>
              e.target.value.trim()
                ? trackSymbol(e.target.value)
                : setEnteringSymbol(false)
            }
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                trackSymbol((e.target as HTMLInputElement).value);
              }
              if (e.key === "Escape") {
                setEnteringSymbol(false);
              }
            }}
          />
        ) : isProxy ? (
          <>
            <EditableCell
              value={entry.proxySymbol ?? ""}
              display={
                entry.lastResolvedUnitPrice !== null ? (
                  formatMoney(entry.lastResolvedUnitPrice, entry.currency)
                ) : (
                  <span className="text-muted-foreground">Set a symbol</span>
                )
              }
              placeholder="Symbol"
              align="right"
              className="font-mono text-[13px] tabular-nums"
              onSave={trackSymbol}
            />
            <span className="block px-1">
              {resolving ? (
                <span className="flex items-center justify-end gap-1 text-[11px] text-muted-foreground">
                  <Loader2 className="h-3 w-3 animate-spin" />
                  Checking…
                </span>
              ) : (
                <Attestation
                  priceSource="proxy"
                  proxySymbol={entry.proxySymbol}
                  attestedAt={null}
                  resolvedAt={entry.lastResolvedPriceAt}
                />
              )}
            </span>
          </>
        ) : (
          <>
            <div className="flex items-center justify-end gap-1">
              <EditableCell
                value={
                  entry.manualUnitPrice === null
                    ? ""
                    : String(entry.manualUnitPrice)
                }
                display={
                  entry.manualUnitPrice !== null
                    ? formatMoney(entry.manualUnitPrice, entry.currency)
                    : undefined
                }
                placeholder={showUnits ? "Unit price" : "Value"}
                align="right"
                type="number"
                className="font-mono text-[13px] tabular-nums"
                onSave={(price) =>
                  onPatch({
                    manualUnitPrice: price === "" ? null : Number(price),
                  })
                }
              />
              <Combobox
                value={entry.currency}
                groups={currencyGroups([entry.currency, ...currenciesInUse])}
                label={`Currency for ${entry.name}`}
                searchPlaceholder="Find a currency"
                align="end"
                triggerClassName="shrink-0 font-mono text-[11px] uppercase text-muted-foreground hover:text-foreground"
                onChange={(currency) => onPatch({ currency })}
              />
            </div>
            <span className="block px-1">
              <Attestation
                priceSource="manual"
                proxySymbol={null}
                attestedAt={entry.manualPriceUpdatedAt}
                resolvedAt={null}
              />
            </span>
          </>
        )}
      </div>
      {kind.proxyable && (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              type="button"
              size="icon"
              variant="ghost"
              aria-label={`How ${entry.name} is priced`}
              className="mt-0.5 h-5 w-5 shrink-0 opacity-0 transition-opacity focus-visible:opacity-100 group-hover/price:opacity-100 data-[state=open]:opacity-100"
            >
              <ChevronDown className="h-3 w-3" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            {isProxy ? (
              <DropdownMenuItem onClick={setOwnPrice}>
                Set the price myself
              </DropdownMenuItem>
            ) : (
              <DropdownMenuItem onClick={() => setEnteringSymbol(true)}>
                Track a security instead
              </DropdownMenuItem>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      )}
    </div>
  );
};
