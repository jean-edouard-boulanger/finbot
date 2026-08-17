import React, { useEffect, useRef, useState } from "react";
import { Loader2, Search } from "lucide-react";

import {
  SearchSecuritiesKindEnum,
  SecuritiesApi,
  SecuritySearchResult,
  useApi,
} from "clients";

import { Button } from "components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "components/ui/dialog";
import { Input } from "components/ui/input";
import { cn } from "lib/utils";

const RESULTS_LIMIT = 25;

/**
 * Centred in the fixed-height result area, whatever it has to say. The message is its own element
 * rather than bare children of the flex box, which would drop the spaces around any inline markup.
 */
const EmptyState: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div className="flex h-full items-center justify-center px-6 text-center text-sm text-muted-foreground">
    <p>{children}</p>
  </div>
);

type SearchKind = SearchSecuritiesKindEnum;

const KIND_FILTERS: { value: SearchKind | null; label: string }[] = [
  { value: null, label: "All" },
  { value: SearchSecuritiesKindEnum.Equity, label: "Shares" },
  { value: SearchSecuritiesKindEnum.Etf, label: "ETFs" },
  { value: SearchSecuritiesKindEnum.Mutualfund, label: "Funds" },
  { value: SearchSecuritiesKindEnum.Cryptocurrency, label: "Crypto" },
  { value: SearchSecuritiesKindEnum.Currency, label: "Currencies" },
  { value: SearchSecuritiesKindEnum.Future, label: "Futures" },
  { value: SearchSecuritiesKindEnum.Index, label: "Indices" },
];

const KIND_LABELS: Record<SearchKind, string> = {
  equity: "Share",
  etf: "ETF",
  mutualfund: "Fund",
  index: "Index",
  future: "Future",
  currency: "Currency",
  cryptocurrency: "Crypto",
};

function describe(result: SecuritySearchResult): string {
  return [result.kind ? KIND_LABELS[result.kind] : null, result.exchange]
    .filter(Boolean)
    .join(" · ");
}

export interface SecurityPickerProps {
  open: boolean;
  /** Name of the holding being priced, shown so the dialog says what it is for. */
  holdingName: string;
  /** Symbol the holding already tracks, if any. */
  currentSymbol?: string | null;
  /** Display name of that symbol, when it is known. */
  currentName?: string | null;
  /** Instrument type the results start narrowed to. */
  defaultKind?: SearchKind | null;
  /** Whether the chosen symbol is still being resolved. */
  busy?: boolean;
  onSelect: (symbol: string) => void | Promise<void>;
  onClose: () => void;
}

/**
 * Picks the Yahoo Finance security a holding is priced from.
 *
 * Nobody knows offhand that physical gold is `SGLN.L` on the LSE, so the search stands in for that
 * knowledge. It runs on demand rather than as you type: Yahoo Finance rate-limits, and a search
 * per keystroke would spend that budget on prefixes nobody meant to look up. A known ticker needs
 * no special path — searching for it returns it, and picking it from the results is what proves it
 * is a symbol Yahoo actually quotes.
 */
export const SecurityPicker: React.FC<SecurityPickerProps> = ({
  open,
  holdingName,
  currentSymbol,
  currentName,
  defaultKind = null,
  busy,
  onSelect,
  onClose,
}) => {
  const securitiesApi = useApi(SecuritiesApi);
  const [query, setQuery] = useState("");
  // The query results are showing for, which only moves when a search is actually asked for.
  const [searchedQuery, setSearchedQuery] = useState("");
  const [kind, setKind] = useState<SearchKind | null>(defaultKind);
  const [results, setResults] = useState<SecuritySearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [unavailable, setUnavailable] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!searchedQuery) {
      return;
    }
    // A slower reply to a superseded search must not overwrite the results being looked at.
    let current = true;
    setSearching(true);
    securitiesApi
      .searchSecurities({
        q: searchedQuery,
        kind: kind ?? undefined,
        limit: RESULTS_LIMIT,
      })
      .then((response) => {
        if (!current) {
          return;
        }
        setResults(response.results);
        setUnavailable(!response.providerAvailable);
      })
      .catch(() => {
        if (current) {
          setResults([]);
          setUnavailable(true);
        }
      })
      .finally(() => {
        if (current) {
          setSearching(false);
        }
      });
    return () => {
      current = false;
    };
  }, [securitiesApi, searchedQuery, kind]);

  const runSearch = () => {
    const trimmed = query.trim();
    if (trimmed.length >= 2) {
      setSearchedQuery(trimmed);
    }
  };

  const moveFocus = (step: number, from?: HTMLElement) => {
    const options = Array.from(
      listRef.current?.querySelectorAll<HTMLButtonElement>("[data-result]") ??
        [],
    );
    if (options.length === 0) {
      return;
    }
    const index = from ? options.indexOf(from as HTMLButtonElement) : -1;
    options[(index + step + options.length) % options.length]?.focus();
  };

  const searched = searchedQuery !== "";

  return (
    <Dialog open={open} onOpenChange={(next) => !next && onClose()}>
      <DialogContent className="max-w-xl">
        <DialogHeader>
          <DialogTitle>Track a security</DialogTitle>
          <DialogDescription>
            {holdingName} will be valued from this security&apos;s price, quoted
            by Yahoo Finance.
          </DialogDescription>
        </DialogHeader>

        <div className="flex gap-2">
          <Input
            autoFocus
            aria-label="Search securities by name or symbol"
            placeholder="Gold, Apple, SGLN.L, BTC-USD…"
            value={query}
            className="h-9"
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                runSearch();
              }
              if (e.key === "ArrowDown") {
                e.preventDefault();
                moveFocus(1);
              }
            }}
          />
          <Button
            type="button"
            size="sm"
            className="h-9 shrink-0"
            disabled={query.trim().length < 2 || searching}
            onClick={runSearch}
          >
            {searching ? (
              <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />
            ) : (
              <Search className="mr-1.5 h-3.5 w-3.5" />
            )}
            Search
          </Button>
        </div>

        {/* Narrowing re-runs the search already on screen, and does nothing before there is one:
            picking a filter is not a way to ask for a search. */}
        <div className="flex flex-wrap gap-1">
          {KIND_FILTERS.map((filter) => (
            <button
              key={filter.label}
              type="button"
              aria-pressed={filter.value === kind}
              onClick={() => setKind(filter.value)}
              className={cn(
                "rounded-full px-2.5 py-1 text-[11px] transition-colors",
                filter.value === kind
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground hover:text-foreground",
              )}
            >
              {filter.label}
            </button>
          ))}
        </div>

        {/* Fixed height, not one that grows with the results: the dialog is a place you search
            from repeatedly, and it should not jump under the pointer as answers arrive. */}
        <div
          ref={listRef}
          aria-busy={searching}
          className="h-72 overflow-y-auto rounded-md border border-border p-1"
          onKeyDown={(e) => {
            if (e.key === "ArrowDown" || e.key === "ArrowUp") {
              e.preventDefault();
              moveFocus(
                e.key === "ArrowDown" ? 1 : -1,
                e.target as HTMLElement,
              );
            }
          }}
        >
          {!searched && !currentSymbol && (
            <EmptyState>
              Search for the security this holding tracks.
            </EmptyState>
          )}
          {!searched && currentSymbol && (
            <EmptyState>
              Currently tracking{" "}
              <span className="font-mono text-foreground">{currentSymbol}</span>
              {currentName && (
                <>
                  {" — "}
                  <span className="text-foreground">{currentName}</span>
                </>
              )}
              . Search to replace it.
            </EmptyState>
          )}
          {searched && !searching && unavailable && (
            <EmptyState>
              Yahoo Finance could not be reached. Try again in a moment.
            </EmptyState>
          )}
          {searched && !searching && !unavailable && results.length === 0 && (
            <EmptyState>
              Nothing found for &apos;{searchedQuery}&apos;.
            </EmptyState>
          )}
          <div className={cn(searching && "opacity-50")}>
            {results.map((result) => (
              <button
                data-result
                type="button"
                key={result.symbol}
                disabled={busy}
                onClick={() => onSelect(result.symbol)}
                className="flex w-full items-baseline gap-3 rounded-sm px-2 py-2 text-left hover:bg-accent hover:text-accent-foreground focus-visible:bg-accent focus-visible:outline-hidden"
              >
                <span className="w-28 shrink-0 truncate font-mono text-[13px]">
                  {result.symbol}
                </span>
                <span className="min-w-0 flex-1 truncate text-sm">
                  {result.name}
                </span>
                <span className="shrink-0 text-[11px] text-muted-foreground">
                  {describe(result)}
                </span>
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center justify-between gap-2">
          <span className="text-[11px] text-muted-foreground">
            {busy ? (
              <span className="flex items-center gap-1.5">
                <Loader2 className="h-3 w-3 animate-spin" />
                Checking the symbol…
              </span>
            ) : (
              "Symbols are Yahoo Finance tickers."
            )}
          </span>
          <Button type="button" variant="outline" size="sm" onClick={onClose}>
            Cancel
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default SecurityPicker;
