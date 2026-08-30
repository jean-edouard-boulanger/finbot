import React, { useEffect, useMemo, useState } from "react";
import { Building2, ExternalLink, Search, Store } from "lucide-react";
import { DateTime } from "luxon";

import { useApi, MerchantsApi, MerchantEntry } from "clients";
import { useDocumentTitle } from "hooks/use-document-title";
import { Input } from "components/ui/input";
import { Separator } from "components/ui/separator";
import { cn } from "lib/utils";

// Same rotating palette as the spending breakdown chart, so a category reads the same colour
// wherever it appears in the app.
const CATEGORY_COLOURS = [
  "var(--chart-1)",
  "var(--chart-2)",
  "var(--chart-3)",
  "var(--chart-4)",
  "var(--chart-5)",
];

function categoryColour(category: string): string {
  let hash = 0;
  for (let i = 0; i < category.length; i++) {
    hash = (hash * 31 + category.charCodeAt(i)) | 0;
  }
  return CATEGORY_COLOURS[Math.abs(hash) % CATEGORY_COLOURS.length];
}

function formatCategory(value: string): string {
  return value
    .replace(/_/g, " ")
    .toLowerCase()
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function domainOf(url: string | null): string | null {
  if (!url) return null;
  try {
    return new URL(url).hostname;
  } catch {
    return null;
  }
}

function formatDate(value: Date | null): string {
  return value
    ? DateTime.fromJSDate(value).toLocaleString(DateTime.DATETIME_MED)
    : "—";
}

function MerchantAvatar({
  merchant,
  size,
}: {
  merchant: MerchantEntry;
  size: "sm" | "lg";
}) {
  const [errored, setErrored] = useState(false);
  const domain = domainOf(merchant.websiteUrl);
  const accent = merchant.category ? categoryColour(merchant.category) : null;
  const box = size === "lg" ? "h-16 w-16 rounded-xl" : "h-8 w-8 rounded-md";
  const icon = size === "lg" ? "h-7 w-7" : "h-4 w-4";
  return (
    <div
      className={cn(
        "flex shrink-0 items-center justify-center overflow-hidden",
        box,
      )}
      style={{
        backgroundColor: accent ? `hsl(${accent} / 0.14)` : "hsl(var(--muted))",
      }}
    >
      {domain && !errored ? (
        <img
          src={`https://www.google.com/s2/favicons?domain=${domain}&sz=64`}
          alt=""
          className={icon}
          onError={() => setErrored(true)}
        />
      ) : (
        <Building2
          className={icon}
          style={{
            color: accent ? `hsl(${accent})` : "hsl(var(--muted-foreground))",
          }}
        />
      )}
    </div>
  );
}

function CategoryTag({ category }: { category: string }) {
  const accent = categoryColour(category);
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs"
      style={{
        borderColor: `hsl(${accent} / 0.35)`,
        color: `hsl(${accent})`,
        backgroundColor: `hsl(${accent} / 0.1)`,
      }}
    >
      <span
        className="h-1.5 w-1.5 rounded-full"
        style={{ backgroundColor: `hsl(${accent})` }}
      />
      {formatCategory(category)}
    </span>
  );
}

function Field({
  label,
  children,
  className,
}: {
  label: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("space-y-1.5 px-6 py-5", className)}>
      <p className="text-[11px] font-medium uppercase tracking-[0.14em] text-muted-foreground">
        {label}
      </p>
      <div className="text-sm leading-relaxed">{children}</div>
    </div>
  );
}

const NotRecorded = () => (
  <span className="text-muted-foreground">Not recorded</span>
);

export const MerchantsSettings: React.FC<Record<string, never>> = () => {
  useDocumentTitle("Merchants");
  const merchantsApi = useApi(MerchantsApi);
  const [merchants, setMerchants] = useState<MerchantEntry[] | null>(null);
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState<number | null>(null);

  useEffect(() => {
    merchantsApi
      .getMerchants()
      .then((result) => setMerchants(result.merchants));
  }, [merchantsApi]);

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return (merchants ?? []).filter(
      (m) =>
        !needle ||
        m.name.toLowerCase().includes(needle) ||
        (m.category ?? "").toLowerCase().includes(needle) ||
        (m.description ?? "").toLowerCase().includes(needle),
    );
  }, [merchants, query]);

  const selected = useMemo(
    () => (merchants ?? []).find((m) => m.id === selectedId) ?? null,
    [merchants, selectedId],
  );

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            Administration
          </p>
          <h3 className="mt-1 text-2xl font-semibold tracking-tight">
            Merchants
          </h3>
        </div>
        {merchants != null && (
          <span className="font-mono text-xs text-muted-foreground">
            {filtered.length === merchants.length
              ? `${merchants.length} on record`
              : `${filtered.length} of ${merchants.length}`}
          </span>
        )}
      </div>
      <Separator />

      <div className="relative">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search merchants by name, category or description…"
          className="h-11 pl-9"
          aria-label="Search merchants"
          disabled={merchants == null}
        />
      </div>

      <div className="grid min-h-[32rem] grid-cols-1 overflow-hidden rounded-lg border border-border bg-card shadow-xs lg:grid-cols-[minmax(16rem,1fr)_2fr]">
        {/* Index */}
        <div
          role="listbox"
          aria-label="Merchants"
          className="scrollbar-subtle max-h-[36rem] overflow-y-auto border-b border-border lg:max-h-[calc(100vh-20rem)] lg:border-b-0 lg:border-r"
        >
          {merchants == null && (
            <p className="px-4 py-10 text-center text-sm text-muted-foreground">
              Loading merchants…
            </p>
          )}
          {merchants != null && filtered.length === 0 && (
            <p className="px-4 py-10 text-center text-sm text-muted-foreground">
              Nothing matches &apos;{query}&apos;.
            </p>
          )}
          {filtered.map((m) => {
            const active = m.id === selectedId;
            return (
              <button
                key={m.id}
                type="button"
                role="option"
                aria-selected={active}
                onClick={() => setSelectedId(m.id)}
                className={cn(
                  "flex w-full items-center gap-3 border-l-2 px-4 py-2.5 text-left transition-colors",
                  "focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring",
                  active
                    ? "border-l-primary bg-accent"
                    : "border-l-transparent hover:bg-accent/50",
                )}
              >
                <MerchantAvatar merchant={m} size="sm" />
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-sm font-medium">
                    {m.name}
                  </span>
                  <span className="block truncate text-xs text-muted-foreground">
                    {m.category ? formatCategory(m.category) : "Uncategorised"}
                  </span>
                </span>
              </button>
            );
          })}
        </div>

        {/* Record */}
        {selected == null ? (
          <div className="flex flex-col items-center justify-center gap-2 px-6 py-20 text-center">
            <Store className="h-6 w-6 text-muted-foreground" />
            <p className="text-sm font-medium">No merchant selected</p>
            <p className="max-w-xs text-xs text-muted-foreground">
              Pick a merchant from the list to inspect what was auto-extracted
              for it.
            </p>
          </div>
        ) : (
          <div key={selected.id} className="animate-fade-up">
            <div className="flex items-start gap-5 p-6">
              <MerchantAvatar merchant={selected} size="lg" />
              <div className="min-w-0 flex-1">
                <h4 className="font-register truncate text-3xl font-semibold leading-tight tracking-tight">
                  {selected.name}
                </h4>
                <div className="mt-2 flex flex-wrap items-center gap-3">
                  {selected.category ? (
                    <CategoryTag category={selected.category} />
                  ) : (
                    <span className="text-xs text-muted-foreground">
                      Uncategorised
                    </span>
                  )}
                  <span className="font-mono text-xs text-muted-foreground">
                    #{selected.id}
                  </span>
                </div>
              </div>
            </div>
            <div className="grid grid-cols-1 border-t border-border sm:grid-cols-2">
              <Field
                label="Description"
                className="border-b border-border sm:col-span-2"
              >
                {selected.description ?? <NotRecorded />}
              </Field>
              <Field
                label="Website"
                className="border-b border-border sm:col-span-2"
              >
                {selected.websiteUrl ? (
                  <a
                    href={selected.websiteUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex max-w-full items-center gap-1 text-primary hover:underline"
                  >
                    <span className="truncate">{selected.websiteUrl}</span>
                    <ExternalLink className="h-3 w-3 shrink-0" />
                  </a>
                ) : (
                  <NotRecorded />
                )}
              </Field>
              <Field
                label="First seen"
                className="sm:border-r sm:border-border"
              >
                <span className="font-mono text-xs">
                  {formatDate(selected.createdAt)}
                </span>
              </Field>
              <Field label="Last updated">
                <span className="font-mono text-xs">
                  {formatDate(selected.updatedAt)}
                </span>
              </Field>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MerchantsSettings;
