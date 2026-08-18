import React, { useEffect, useRef, useState } from "react";
import { RefreshCw } from "lucide-react";
import { toast } from "sonner";

import { cn } from "lib/utils";
import { useNotifyValuationRefreshed } from "contexts";
import { formatApiError } from "utils/errors";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "components/ui/tooltip";

const POLL_INTERVAL_MS = 3_000;
const POLL_TIMEOUT_MS = 180_000;

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export interface RefreshValuationButtonProps {
  /** Timestamp currently displayed: the baseline for "has fresh data landed?". */
  valuationDate: Date | null;
  /** Kicks off the valuation workflow. */
  onTrigger: () => Promise<void>;
  /** Re-fetches the valuation, commits it to the caller's state, and returns its date. */
  onReload: () => Promise<Date | null>;
  disabled?: boolean;
  disabledReason?: string;
}

export const RefreshValuationButton: React.FC<RefreshValuationButtonProps> = ({
  valuationDate,
  onTrigger,
  onReload,
  disabled = false,
  disabledReason,
}) => {
  const [refreshing, setRefreshing] = useState(false);
  const notifyValuationRefreshed = useNotifyValuationRefreshed();
  // Both dashboards can be navigated away from mid-refresh: stop the poll loop when that happens.
  // The mount branch matters under StrictMode, which mounts, cleans up, then mounts again.
  const cancelled = useRef(false);
  useEffect(() => {
    cancelled.current = false;
    return () => {
      cancelled.current = true;
    };
  }, []);

  const handleClick = async () => {
    if (refreshing || disabled) {
      return;
    }
    setRefreshing(true);
    const baseline = valuationDate?.getTime() ?? 0;

    try {
      await onTrigger();
    } catch (e) {
      toast.error(`Failed to start refresh: ${formatApiError(e)}`);
      setRefreshing(false);
      return;
    }

    // Valuation runs as a fire-and-forget workflow with no job handle, so the only way to
    // know it landed is to watch the valuation timestamp move forward.
    const deadline = Date.now() + POLL_TIMEOUT_MS;
    while (Date.now() < deadline) {
      await sleep(POLL_INTERVAL_MS);
      if (cancelled.current) {
        return;
      }
      try {
        const updated = await onReload();
        if (updated !== null && updated.getTime() > baseline) {
          if (cancelled.current) {
            return;
          }
          setRefreshing(false);
          // The caller only reloaded its own figure; move the rest of the page with it.
          notifyValuationRefreshed();
          toast.success("Valuation refreshed");
          return;
        }
      } catch {
        // Transient failure while the refresh is in flight: keep polling.
      }
    }

    if (cancelled.current) {
      return;
    }
    // Polling has stopped here, so the new figure will not arrive on its own.
    setRefreshing(false);
    toast.info(
      "Still refreshing. Reload the page in a few minutes to see the new valuation.",
    );
  };

  const hint = refreshing
    ? "Refreshing…"
    : disabled
      ? (disabledReason ?? "Refresh unavailable")
      : "Refresh valuation";

  return (
    <TooltipProvider delayDuration={200}>
      <Tooltip>
        <TooltipTrigger asChild>
          {/* Wrapper so the tooltip still fires while the button is disabled. */}
          <span className="inline-flex">
            <button
              type="button"
              onClick={handleClick}
              disabled={refreshing || disabled}
              aria-label="Refresh valuation"
              aria-busy={refreshing}
              className={cn(
                // The box matches the 24px text row it sits in; the hit area reaches past it.
                "relative inline-flex h-6 w-6 items-center justify-center rounded-md",
                "after:absolute after:-inset-1.5 after:content-['']",
                "ring-offset-background transition-colors",
                "focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
                refreshing
                  ? // Busy is not unavailable: the spin is the only progress signal, so let it read
                    // louder than the label it sits next to rather than dimmer.
                    "text-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
                disabled && "opacity-50",
              )}
            >
              <RefreshCw
                className={cn(
                  "h-3.5 w-3.5",
                  refreshing &&
                    "animate-spin motion-reduce:[animation-duration:3s]",
                )}
              />
            </button>
          </span>
        </TooltipTrigger>
        {/* Below, so hovering the control never covers the valuation it refreshes. */}
        <TooltipContent side="bottom">{hint}</TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};

export default RefreshValuationButton;
