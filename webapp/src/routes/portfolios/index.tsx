import React, { useCallback, useContext, useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import { Plus, Snowflake } from "lucide-react";

import AuthContext from "contexts/auth/auth-context";
import {
  useApi,
  FormattingRulesApi,
  LinkedAccountsValuationApi,
  PortfoliosApi,
  PortfolioSummary,
} from "clients";
import { formatApiError } from "utils/errors";
import { useDocumentTitle } from "hooks/use-document-title";

import {
  ColourPicker,
  DEFAULT_ACCOUNT_COLOURS,
} from "components/colour-picker";
import { LoadingButton } from "components/loading-button";
import { Button } from "components/ui/button";
import { Input } from "components/ui/input";
import { Skeleton } from "components/ui/skeleton";

/** First palette colour not already spoken for, so a new portfolio is distinguishable by default. */
function nextFreeColour(palette: string[], taken: string[]): string {
  const used = new Set(taken.map((colour) => colour.toLowerCase()));
  return (
    palette.find((colour) => !used.has(colour.toLowerCase())) ??
    palette[0] ??
    DEFAULT_ACCOUNT_COLOURS[0]
  );
}

function formatMoney(amount: number, currency: string): string {
  try {
    return new Intl.NumberFormat(undefined, {
      style: "currency",
      currency,
      maximumFractionDigits: 0,
    }).format(amount);
  } catch {
    return `${amount.toLocaleString()} ${currency}`;
  }
}

const NAME_MAX_LENGTH = 256;

interface NewPortfolioRowProps {
  palette: string[];
  takenNames: string[];
  takenColours: string[];
  onCancel: () => void;
  onCreated: (portfolioId: number) => void;
}

/**
 * Creating a portfolio happens in the list itself: a row you fill in, in the place the finished
 * portfolio will appear.
 */
const NewPortfolioRow: React.FC<NewPortfolioRowProps> = ({
  palette,
  takenNames,
  takenColours,
  onCancel,
  onCreated,
}) => {
  const { userAccountId } = useContext(AuthContext);
  const portfoliosApi = useApi(PortfoliosApi);
  const [name, setName] = useState("");
  const [colour, setColour] = useState(() =>
    nextFreeColour(palette, takenColours),
  );
  const [saving, setSaving] = useState(false);

  const trimmed = name.trim();
  const isDuplicate = takenNames.some(
    (taken) => taken.toLowerCase() === trimmed.toLowerCase(),
  );
  const canSubmit = trimmed.length > 0 && !isDuplicate && !saving;

  const create = async () => {
    if (!canSubmit) {
      return;
    }
    setSaving(true);
    try {
      const response = await portfoliosApi.createPortfolio({
        userAccountId: userAccountId!,
        createPortfolioRequest: { name: trimmed, colour },
      });
      onCreated(response.portfolio.id);
    } catch (e) {
      toast.error(formatApiError(e));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="border-b border-border/50 py-4">
      <div className="flex items-center gap-3">
        <ColourPicker
          colour={colour}
          colours={palette}
          label="Portfolio colour"
          onChange={setColour}
        />
        <Input
          value={name}
          autoFocus
          maxLength={NAME_MAX_LENGTH}
          placeholder="Name this portfolio"
          aria-label="Portfolio name"
          aria-invalid={isDuplicate}
          className="h-9 flex-1"
          onChange={(e) => setName(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") create();
            if (e.key === "Escape") onCancel();
          }}
        />
        <LoadingButton
          type="button"
          size="sm"
          loading={saving}
          disabled={!canSubmit}
          onClick={create}
        >
          Create
        </LoadingButton>
        <Button type="button" size="sm" variant="ghost" onClick={onCancel}>
          Cancel
        </Button>
      </div>
      {isDuplicate && (
        <p className="mt-1.5 pl-10 text-sm text-destructive">
          You already have a portfolio called &apos;{trimmed}&apos;.
        </p>
      )}
    </div>
  );
};

interface PortfolioRowProps {
  portfolio: PortfolioSummary;
  valuation: { value: number; currency: string } | undefined;
  onOpen: () => void;
}

const PortfolioRow: React.FC<PortfolioRowProps> = ({
  portfolio,
  valuation,
  onOpen,
}) => (
  <button
    type="button"
    onClick={onOpen}
    className="group flex w-full items-baseline gap-4 border-b border-border/50 py-5 text-left transition-colors hover:bg-accent/40 focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring"
  >
    <span
      aria-hidden="true"
      className="h-2.5 w-2.5 shrink-0 translate-y-[-1px] rounded-[2px]"
      style={{ backgroundColor: portfolio.colour }}
    />
    <span className="min-w-0 flex-1">
      <span className="block truncate font-register text-[17px] font-semibold tracking-tight">
        {portfolio.name}
      </span>
      <span className="mt-0.5 block text-xs text-muted-foreground">
        {portfolio.entriesCount}{" "}
        {portfolio.entriesCount === 1 ? "holding" : "holdings"} in{" "}
        {portfolio.sectionsCount}{" "}
        {portfolio.sectionsCount === 1 ? "section" : "sections"}
        {portfolio.frozen && (
          <>
            {" · "}
            <Snowflake className="inline h-3 w-3 -translate-y-px" /> Frozen
          </>
        )}
      </span>
    </span>
    <span className="shrink-0 text-right font-mono text-[19px] tabular-nums">
      {portfolio.estimatedValue !== null ? (
        formatMoney(portfolio.estimatedValue, portfolio.valuationCcy)
      ) : valuation ? (
        formatMoney(valuation.value, valuation.currency)
      ) : (
        <span className="text-sm text-muted-foreground">Not yet valued</span>
      )}
    </span>
  </button>
);

export const Portfolios: React.FC = () => {
  const { userAccountId } = useContext(AuthContext);
  const portfoliosApi = useApi(PortfoliosApi);
  const valuationApi = useApi(LinkedAccountsValuationApi);
  const formattingRulesApi = useApi(FormattingRulesApi);
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  useDocumentTitle("Portfolios");

  const [portfolios, setPortfolios] = useState<PortfolioSummary[] | null>(null);
  const [valuations, setValuations] = useState<
    Record<number, { value: number; currency: string }>
  >({});
  const [palette, setPalette] = useState<string[]>(DEFAULT_ACCOUNT_COLOURS);
  // "Create portfolio" in the sidebar lands here with the new row already open.
  const [creating, setCreating] = useState(
    () => searchParams.get("action") === "new",
  );

  const stopCreating = useCallback(() => {
    setCreating(false);
    if (searchParams.get("action") === "new") {
      searchParams.delete("action");
      setSearchParams(searchParams, { replace: true });
    }
  }, [searchParams, setSearchParams]);

  const refresh = useCallback(async () => {
    try {
      const response = await portfoliosApi.getPortfolios({
        userAccountId: userAccountId!,
      });
      setPortfolios(response.portfolios);
    } catch (e) {
      toast.error(formatApiError(e));
      setPortfolios([]);
    }
  }, [portfoliosApi, userAccountId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  useEffect(() => {
    const fetchPalette = async () => {
      try {
        const response = await formattingRulesApi.getAccountsFormattingRules();
        if (response.colourPalette.length > 0) {
          setPalette(response.colourPalette);
        }
      } catch {
        // The built-in palette is a fine fallback, no need to bother anyone.
      }
    };
    fetchPalette();
  }, [formattingRulesApi]);

  useEffect(() => {
    const fetchValuations = async () => {
      try {
        const response = await valuationApi.getLinkedAccountsValuation({
          userAccountId: userAccountId!,
        });
        setValuations(
          Object.fromEntries(
            response.valuation.entries.map((entry) => [
              entry.linkedAccount.id,
              {
                value: entry.valuation.value,
                currency: entry.valuation.currency,
              },
            ]),
          ),
        );
      } catch {
        setValuations({});
      }
    };
    fetchValuations();
  }, [valuationApi, userAccountId]);

  const total = (portfolios ?? []).reduce(
    (sum, portfolio) =>
      sum +
      (portfolio.estimatedValue ??
        valuations[portfolio.linkedAccountId]?.value ??
        0),
    0,
  );
  const currency =
    portfolios?.[0]?.valuationCcy ?? Object.values(valuations)[0]?.currency;

  const newPortfolioRow = creating && (
    <NewPortfolioRow
      palette={palette}
      takenNames={(portfolios ?? []).map((portfolio) => portfolio.name)}
      takenColours={(portfolios ?? []).map((portfolio) => portfolio.colour)}
      onCancel={stopCreating}
      onCreated={(portfolioId) => {
        stopCreating();
        navigate(`/portfolios/${portfolioId}`);
      }}
    />
  );

  return (
    <div className="container mx-auto px-6 pb-48 pt-8">
      <div className="max-w-3xl">
        <header className="mb-8 flex flex-wrap items-start justify-between gap-x-8 gap-y-4">
          <div>
            <h1 className="font-register text-[19px] font-semibold tracking-tight">
              Portfolios
            </h1>
            <p className="mt-1 max-w-md text-sm text-muted-foreground">
              Portfolios you manage yourself. Their value counts towards your
              net worth automatically.
            </p>
            {portfolios !== null && portfolios.length > 1 && currency && (
              <div className="mt-5">
                <span className="text-[10px] font-medium uppercase tracking-[0.11em] text-muted-foreground">
                  Estimated across {portfolios.length} portfolios
                </span>
                <p className="mt-1 font-register text-[36px] font-light leading-none tracking-tight tabular-nums">
                  {formatMoney(total, currency)}
                </p>
              </div>
            )}
          </div>
          <Button
            type="button"
            size="sm"
            disabled={creating}
            onClick={() => setCreating(true)}
          >
            <Plus className="mr-1.5 h-4 w-4" />
            New portfolio
          </Button>
        </header>

        {portfolios === null && (
          <div className="space-y-4">
            <Skeleton className="h-16" />
            <Skeleton className="h-16" />
          </div>
        )}

        {portfolios !== null && (portfolios.length > 0 || creating) && (
          <div className="border-t border-border/50">
            {newPortfolioRow}
            {portfolios.map((portfolio) => (
              <PortfolioRow
                key={portfolio.id}
                portfolio={portfolio}
                valuation={valuations[portfolio.linkedAccountId]}
                onOpen={() => navigate(`/portfolios/${portfolio.id}`)}
              />
            ))}
          </div>
        )}

        {portfolios !== null && portfolios.length === 0 && !creating && (
          <div className="border-y border-dashed border-border py-16 text-center">
            <p className="font-register text-base font-semibold">
              No portfolios yet
            </p>
            <p className="mx-auto mt-1 max-w-sm text-sm text-muted-foreground">
              Create one for your property, metals or anything else you value by
              hand. You can also convert an existing linked account from
              settings.
            </p>
            <Button
              type="button"
              size="sm"
              variant="outline"
              className="mt-4"
              onClick={() => setCreating(true)}
            >
              <Plus className="mr-1.5 h-4 w-4" />
              New portfolio
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};

export default Portfolios;
