import React from "react";
import { NavLink } from "react-router-dom";

import { cn } from "lib/utils";

export type PortfolioView = "holdings" | "valuation";

interface PortfolioViewSwitchProps {
  portfolioId: number;
  linkedAccountId: number;
  current: PortfolioView;
}

/**
 * A portfolio is two things at once: a set of holdings you maintain, and an account with a
 * valuation over time. This moves between the two views of it.
 */
export const PortfolioViewSwitch: React.FC<PortfolioViewSwitchProps> = ({
  portfolioId,
  linkedAccountId,
  current,
}) => {
  const views: Array<{ view: PortfolioView; label: string; to: string }> = [
    { view: "holdings", label: "Holdings", to: `/portfolios/${portfolioId}` },
    {
      view: "valuation",
      label: "Valuation",
      to: `/dashboard/accounts/${linkedAccountId}`,
    },
  ];

  return (
    <div
      className="inline-flex items-center rounded-md border border-border bg-background p-0.5"
      role="group"
      aria-label="Portfolio view"
    >
      {views.map(({ view, label, to }) => {
        const isCurrent = view === current;
        return (
          <NavLink
            key={view}
            to={to}
            aria-current={isCurrent ? "page" : undefined}
            className={cn(
              "rounded-[5px] px-2.5 py-1 text-sm transition-colors",
              "focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring",
              isCurrent
                ? "bg-accent font-medium text-accent-foreground"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            {label}
          </NavLink>
        );
      })}
    </div>
  );
};
