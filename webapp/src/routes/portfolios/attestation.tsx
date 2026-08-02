import React from "react";
import { DateTime } from "luxon";

import { cn } from "lib/utils";

/**
 * Holdings in a portfolio have no live feed: a price is either attested by the owner, and ages
 * from the day it was set, or delegated to a proxy security that is re-read on every snapshot.
 * These helpers turn that distinction into the page's main signal.
 */

export type Freshness = "live" | "fresh" | "aging" | "stale" | "unknown";

const AGING_AFTER_MONTHS = 6;
const STALE_AFTER_MONTHS = 18;

export function freshnessOf(
  priceSource: "manual" | "proxy",
  attestedAt: Date | null,
): Freshness {
  if (priceSource === "proxy") {
    return "live";
  }
  if (attestedAt === null) {
    return "unknown";
  }
  const months = -DateTime.fromJSDate(attestedAt).diffNow("months").months;
  if (months >= STALE_AFTER_MONTHS) {
    return "stale";
  }
  if (months >= AGING_AFTER_MONTHS) {
    return "aging";
  }
  return "fresh";
}

export function needsReview(freshness: Freshness): boolean {
  return freshness === "stale" || freshness === "unknown";
}

const METER_SEGMENTS = 4;

const FILLED_SEGMENTS: Record<Freshness, number> = {
  live: 4,
  fresh: 4,
  aging: 2,
  stale: 1,
  unknown: 0,
};

const METER_TONE: Record<Freshness, string> = {
  live: "bg-muted-foreground/45",
  fresh: "bg-muted-foreground/45",
  aging: "bg-attest-aging",
  stale: "bg-attest-stale",
  unknown: "bg-attest-stale",
};

const LABEL_TONE: Record<Freshness, string> = {
  live: "text-muted-foreground",
  fresh: "text-muted-foreground",
  aging: "text-attest-aging",
  stale: "text-attest-stale",
  unknown: "text-attest-stale",
};

/** Four segments that empty and warm as an attested valuation ages. */
export const FreshnessMeter: React.FC<{ freshness: Freshness }> = ({
  freshness,
}) => {
  const filled = FILLED_SEGMENTS[freshness];
  return (
    <span className="inline-flex items-center gap-[2px]" aria-hidden="true">
      {Array.from({ length: METER_SEGMENTS }, (_, index) => (
        <span
          key={index}
          className={cn(
            "h-[3px] w-[5px] rounded-[1px]",
            index < filled ? METER_TONE[freshness] : "bg-border",
          )}
        />
      ))}
    </span>
  );
};

export interface AttestationProps {
  priceSource: "manual" | "proxy";
  proxySymbol: string | null;
  attestedAt: Date | null;
  resolvedAt: Date | null;
}

/**
 * States where a price came from. This is the one thing a portfolio knows that a synced account
 * does not, so it gets to be the most characterful part of the row.
 */
export const Attestation: React.FC<AttestationProps> = ({
  priceSource,
  proxySymbol,
  attestedAt,
  resolvedAt,
}) => {
  if (priceSource === "proxy") {
    return (
      <span className="flex items-center justify-end gap-1.5 text-[11px] text-muted-foreground">
        <span className="font-mono tracking-tight text-foreground/70">
          {proxySymbol}
        </span>
        <span
          className="h-1 w-1 rounded-full bg-gain"
          title={
            resolvedAt
              ? `Read ${DateTime.fromJSDate(resolvedAt).toRelative()}`
              : "Read on every snapshot"
          }
        />
      </span>
    );
  }

  const freshness = freshnessOf(priceSource, attestedAt);
  return (
    <span
      className={cn(
        "flex items-center justify-end gap-1.5 text-[11px]",
        LABEL_TONE[freshness],
      )}
    >
      <FreshnessMeter freshness={freshness} />
      {attestedAt
        ? `you, ${DateTime.fromJSDate(attestedAt).toRelative({ style: "narrow" })}`
        : "never valued"}
    </span>
  );
};
