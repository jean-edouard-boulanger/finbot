import React, { useEffect, useState } from "react";
import { Button } from "components/ui/button";
import { Input } from "components/ui/input";
import { Popover, PopoverTrigger, PopoverContent } from "components/ui/popover";
import { Calendar, ChevronDown } from "lucide-react";

interface DatePreset {
  label: string;
  getRange: () => { from: string; to: string };
}

function toDateString(d: Date): string {
  return d.toISOString().slice(0, 10);
}

const today = () => new Date();

const DATE_PRESETS: DatePreset[] = [
  {
    label: "Last 24 hours",
    getRange: () => {
      const t = today();
      const from = new Date(t);
      from.setDate(from.getDate() - 1);
      return { from: toDateString(from), to: toDateString(t) };
    },
  },
  {
    label: "Last 7 days",
    getRange: () => {
      const t = today();
      const from = new Date(t);
      from.setDate(from.getDate() - 7);
      return { from: toDateString(from), to: toDateString(t) };
    },
  },
  {
    label: "Last 2 weeks",
    getRange: () => {
      const t = today();
      const from = new Date(t);
      from.setDate(from.getDate() - 14);
      return { from: toDateString(from), to: toDateString(t) };
    },
  },
  {
    label: "Last 30 days",
    getRange: () => {
      const t = today();
      const from = new Date(t);
      from.setDate(from.getDate() - 30);
      return { from: toDateString(from), to: toDateString(t) };
    },
  },
  {
    label: "This month",
    getRange: () => {
      const t = today();
      return {
        from: toDateString(new Date(t.getFullYear(), t.getMonth(), 1)),
        to: toDateString(t),
      };
    },
  },
  {
    label: "Last 2 months",
    getRange: () => {
      const t = today();
      const from = new Date(t);
      from.setMonth(from.getMonth() - 2);
      return { from: toDateString(from), to: toDateString(t) };
    },
  },
  {
    label: "Last 3 months",
    getRange: () => {
      const t = today();
      const from = new Date(t);
      from.setMonth(from.getMonth() - 3);
      return { from: toDateString(from), to: toDateString(t) };
    },
  },
  {
    label: "Last 6 months",
    getRange: () => {
      const t = today();
      const from = new Date(t);
      from.setMonth(from.getMonth() - 6);
      return { from: toDateString(from), to: toDateString(t) };
    },
  },
  {
    label: "Last 12 months",
    getRange: () => {
      const t = today();
      const from = new Date(t);
      from.setFullYear(from.getFullYear() - 1);
      return { from: toDateString(from), to: toDateString(t) };
    },
  },
  {
    label: "Last 2 years",
    getRange: () => {
      const t = today();
      const from = new Date(t);
      from.setFullYear(from.getFullYear() - 2);
      return { from: toDateString(from), to: toDateString(t) };
    },
  },
  {
    label: "Last 5 years",
    getRange: () => {
      const t = today();
      const from = new Date(t);
      from.setFullYear(from.getFullYear() - 5);
      return { from: toDateString(from), to: toDateString(t) };
    },
  },
  {
    label: "This year",
    getRange: () => {
      const t = today();
      return {
        from: toDateString(new Date(t.getFullYear(), 0, 1)),
        to: toDateString(t),
      };
    },
  },
  {
    label: "Previous year",
    getRange: () => {
      const t = today();
      const y = t.getFullYear() - 1;
      return {
        from: toDateString(new Date(y, 0, 1)),
        to: toDateString(new Date(y, 11, 31)),
      };
    },
  },
];

const ALL_TIME_LABEL = "All time";

function matchPresetLabel(fromDate: string, toDate: string): string | null {
  if (fromDate === "" && toDate === "") return ALL_TIME_LABEL;
  for (const preset of DATE_PRESETS) {
    const range = preset.getRange();
    if (range.from === fromDate && range.to === toDate) {
      return preset.label;
    }
  }
  return null;
}

export interface DateRangeFilterProps {
  fromDate: string;
  toDate: string;
  onFromDateChange: (value: string) => void;
  onToDateChange: (value: string) => void;
  /** When true, renders a smaller trigger that fits the dashboard widget header. */
  compact?: boolean;
  /** Whether to show an "All time" preset (clears both dates). */
  allowAllTime?: boolean;
  /** Placeholder shown in the trigger when no range is set. */
  placeholder?: string;
}

export const DateRangeFilter: React.FC<DateRangeFilterProps> = ({
  fromDate,
  toDate,
  onFromDateChange,
  onToDateChange,
  compact = false,
  allowAllTime = false,
  placeholder = "Date range",
}) => {
  const isAllTime = fromDate === "" && toDate === "";
  const isActive = !isAllTime;
  const presetLabel = matchPresetLabel(fromDate, toDate);
  const triggerLabel = presetLabel
    ? presetLabel
    : isActive
      ? `${fromDate || "..."} – ${toDate || "..."}`
      : placeholder;

  const [open, setOpen] = useState(false);
  // Local draft state so typing in the From/To inputs doesn't fire onChange on
  // every keystroke. We commit on close (or on preset / clear actions).
  const [localFrom, setLocalFrom] = useState(fromDate);
  const [localTo, setLocalTo] = useState(toDate);

  useEffect(() => {
    if (open) {
      setLocalFrom(fromDate);
      setLocalTo(toDate);
    }
  }, [open, fromDate, toDate]);

  const localPresetLabel = matchPresetLabel(localFrom, localTo);
  const localIsAllTime = localFrom === "" && localTo === "";
  const localIsActive = !localIsAllTime;

  const commit = (from: string, to: string) => {
    if (from !== fromDate) onFromDateChange(from);
    if (to !== toDate) onToDateChange(to);
  };

  const handleOpenChange = (next: boolean) => {
    if (!next) {
      commit(localFrom, localTo);
    }
    setOpen(next);
  };

  const pickPreset = (from: string, to: string) => {
    setLocalFrom(from);
    setLocalTo(to);
    commit(from, to);
    setOpen(false);
  };

  const trigger = compact ? (
    <Button
      variant="outline"
      size="xs"
      className="border-border/50 bg-secondary/50 text-xs font-medium tracking-wide text-muted-foreground hover:text-foreground"
    >
      <Calendar className="mr-1 h-3 w-3" />
      {triggerLabel} <ChevronDown className="ml-1 h-3 w-3" />
    </Button>
  ) : (
    <Button
      variant="outline"
      size="sm"
      className={`h-8 w-full justify-start gap-1.5 text-xs font-normal ${
        isActive
          ? "border-primary/50 bg-primary/5"
          : "border-dashed text-muted-foreground"
      }`}
    >
      <Calendar className="h-3.5 w-3.5 shrink-0" />
      <span className="truncate">{triggerLabel}</span>
    </Button>
  );

  return (
    <Popover open={open} onOpenChange={handleOpenChange}>
      <PopoverTrigger asChild>{trigger}</PopoverTrigger>
      <PopoverContent className="w-[28rem] p-0" align="end">
        <div className="flex">
          <div className="grid grid-cols-2 gap-0.5 border-r p-2">
            {DATE_PRESETS.map((preset) => {
              const isSelected = localPresetLabel === preset.label;
              return (
                <button
                  key={preset.label}
                  className={`block w-full rounded px-3 py-1.5 text-left text-xs transition-colors ${
                    isSelected
                      ? "bg-primary text-primary-foreground"
                      : "hover:bg-muted"
                  }`}
                  onClick={() => {
                    const range = preset.getRange();
                    pickPreset(range.from, range.to);
                  }}
                >
                  {preset.label}
                </button>
              );
            })}
            {allowAllTime && (
              <button
                className={`block w-full rounded px-3 py-1.5 text-left text-xs transition-colors ${
                  localIsAllTime
                    ? "bg-primary text-primary-foreground"
                    : "hover:bg-muted"
                }`}
                onClick={() => pickPreset("", "")}
              >
                {ALL_TIME_LABEL}
              </button>
            )}
          </div>
          <div className="flex-1 space-y-3 p-3">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">
                From
              </label>
              <Input
                type="date"
                value={localFrom}
                onChange={(e) => setLocalFrom(e.target.value)}
                className="h-8 text-xs"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">
                To
              </label>
              <Input
                type="date"
                value={localTo}
                onChange={(e) => setLocalTo(e.target.value)}
                className="h-8 text-xs"
              />
            </div>
            {localIsActive && (
              <Button
                variant="ghost"
                size="sm"
                className="h-7 w-full text-xs"
                onClick={() => pickPreset("", "")}
              >
                Clear
              </Button>
            )}
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
};
