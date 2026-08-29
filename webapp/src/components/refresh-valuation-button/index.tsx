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

const POLL_INTERVAL_MS = 2_000;
const POLL_TIMEOUT_MS = 180_000;

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export type ValuationJobStatus = "running" | "succeeded" | "failed";

export interface RefreshValuationButtonProps {
  /** Kicks off the valuation workflow and returns a job id to poll for its outcome. */
  onTrigger: () => Promise<string>;
  /** Polls the outcome of the job `onTrigger` started. */
  onCheckStatus: (jobId: string) => Promise<ValuationJobStatus>;
  /** Re-fetches the valuation and commits it to the caller's state. */
  onReload: () => Promise<Date | null>;
  disabled?: boolean;
  disabledReason?: string;
}

export const RefreshValuationButton: React.FC<RefreshValuationButtonProps> = ({
  onTrigger,
  onCheckStatus,
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

    let jobId: string;
    try {
      jobId = await onTrigger();
    } catch (e) {
      toast.error(`Failed to start refresh: ${formatApiError(e)}`);
      setRefreshing(false);
      return;
    }

    const deadline = Date.now() + POLL_TIMEOUT_MS;
    while (Date.now() < deadline) {
      await sleep(POLL_INTERVAL_MS);
      if (cancelled.current) {
        return;
      }
      let status: ValuationJobStatus;
      try {
        status = await onCheckStatus(jobId);
      } catch {
        // Transient failure while the refresh is in flight: keep polling.
        continue;
      }
      if (status === "running") {
        continue;
      }
      if (cancelled.current) {
        return;
      }
      if (status === "succeeded") {
        // The workflow landed; a failure to re-fetch it here is a lesser, separate problem than the
        // refresh itself failing, so it does not change the outcome reported to the user.
        await onReload().catch(() => undefined);
        setRefreshing(false);
        // The caller only reloaded its own figure; move the rest of the page with it.
        notifyValuationRefreshed();
        toast.success("Valuation refreshed");
        return;
      }
      setRefreshing(false);
      toast.error(
        "Valuation refresh failed. Check your notifications for details.",
      );
      return;
    }

    if (cancelled.current) {
      return;
    }
    // The job is still running -- genuinely still in progress, not a failure we missed.
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
