import React, { useState, useMemo } from "react";
import { Button } from "components/ui/button";
import { Input } from "components/ui/input";
import { Checkbox } from "components/ui/checkbox";
import { Popover, PopoverTrigger, PopoverContent } from "components/ui/popover";
import { Slider } from "components/ui/slider";
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
    label: "Last 24h",
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
    label: "Last 30 days",
    getRange: () => {
      const t = today();
      const from = new Date(t);
      from.setDate(from.getDate() - 30);
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
    label: "Last year",
    getRange: () => {
      const t = today();
      const from = new Date(t);
      from.setFullYear(from.getFullYear() - 1);
      return { from: toDateString(from), to: toDateString(t) };
    },
  },
];

function matchPresetLabel(fromDate: string, toDate: string): string | null {
  for (const preset of DATE_PRESETS) {
    const range = preset.getRange();
    if (range.from === fromDate && range.to === toDate) {
      return preset.label;
    }
  }
  return null;
}

interface DateRangeFilterProps {
  fromDate: string;
  toDate: string;
  onFromDateChange: (value: string) => void;
  onToDateChange: (value: string) => void;
}

export const DateRangeFilter: React.FC<DateRangeFilterProps> = ({
  fromDate,
  toDate,
  onFromDateChange,
  onToDateChange,
}) => {
  const isActive = fromDate !== "" || toDate !== "";
  const presetLabel = isActive ? matchPresetLabel(fromDate, toDate) : null;
  const label = presetLabel
    ? presetLabel
    : isActive
      ? `${fromDate || "..."} \u2013 ${toDate || "..."}`
      : "";

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className={`h-8 w-full justify-start gap-1.5 text-xs font-normal ${
            isActive
              ? "border-primary/50 bg-primary/5"
              : "border-dashed text-muted-foreground"
          }`}
        >
          <Calendar className="h-3.5 w-3.5 flex-shrink-0" />
          <span className="truncate">{label || "Date range"}</span>
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-72 p-0">
        <div className="flex">
          <div className="border-r p-2 space-y-0.5">
            {DATE_PRESETS.map((preset) => {
              const range = preset.getRange();
              const isSelected = range.from === fromDate && range.to === toDate;
              return (
                <button
                  key={preset.label}
                  className={`block w-full rounded px-3 py-1.5 text-left text-xs transition-colors ${
                    isSelected
                      ? "bg-primary text-primary-foreground"
                      : "hover:bg-muted"
                  }`}
                  onClick={() => {
                    onFromDateChange(range.from);
                    onToDateChange(range.to);
                  }}
                >
                  {preset.label}
                </button>
              );
            })}
          </div>
          <div className="flex-1 space-y-3 p-3">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">
                From
              </label>
              <Input
                type="date"
                value={fromDate}
                onChange={(e) => onFromDateChange(e.target.value)}
                className="h-8 text-xs"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">
                To
              </label>
              <Input
                type="date"
                value={toDate}
                onChange={(e) => onToDateChange(e.target.value)}
                className="h-8 text-xs"
              />
            </div>
            {isActive && (
              <Button
                variant="ghost"
                size="sm"
                className="h-7 w-full text-xs"
                onClick={() => {
                  onFromDateChange("");
                  onToDateChange("");
                }}
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

interface MultiSelectOption {
  label: string;
  value: string;
  count?: number;
}

interface MultiSelectFilterProps {
  options: MultiSelectOption[];
  selected: Set<string>;
  onToggle: (value: string) => void;
  placeholder: string;
}

export const MultiSelectFilter: React.FC<MultiSelectFilterProps> = ({
  options,
  selected,
  onToggle,
  placeholder,
}) => {
  const [search, setSearch] = useState("");
  const isActive = selected.size > 0;

  const filtered = useMemo(() => {
    if (!search) return options;
    const lower = search.toLowerCase();
    return options.filter((o) => o.label.toLowerCase().includes(lower));
  }, [options, search]);

  const label = isActive ? `${selected.size} selected` : placeholder;

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className={`h-8 w-full justify-between gap-1 text-xs font-normal ${
            isActive
              ? "border-primary/50 bg-primary/5"
              : "border-dashed text-muted-foreground"
          }`}
        >
          <span className="truncate">{label}</span>
          <ChevronDown className="h-3.5 w-3.5 flex-shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-64 space-y-2 p-3">
        <Input
          placeholder={`Search ${placeholder.toLowerCase()}...`}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="h-8 text-xs"
        />
        <div className="max-h-48 overflow-y-auto space-y-0.5">
          {filtered.map((option) => (
            <label
              key={option.value}
              className="flex cursor-pointer items-center gap-2 rounded px-2 py-1.5 hover:bg-muted"
            >
              <Checkbox
                checked={selected.has(option.value)}
                onCheckedChange={() => onToggle(option.value)}
              />
              <span className="flex-1 truncate text-xs">{option.label}</span>
              {option.count !== undefined && (
                <span className="text-xs text-muted-foreground">
                  ({option.count})
                </span>
              )}
            </label>
          ))}
          {filtered.length === 0 && (
            <p className="px-2 py-3 text-center text-xs text-muted-foreground">
              No matches
            </p>
          )}
        </div>
        {isActive && (
          <Button
            variant="ghost"
            size="sm"
            className="h-7 w-full text-xs"
            onClick={() => {
              for (const v of selected) onToggle(v);
            }}
          >
            Clear all
          </Button>
        )}
      </PopoverContent>
    </Popover>
  );
};

interface TextSearchFilterProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}

export const TextSearchFilter: React.FC<TextSearchFilterProps> = ({
  value,
  onChange,
  placeholder = "Search...",
}) => {
  return (
    <Input
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      className={`h-8 text-xs ${
        value ? "border-primary/50 bg-primary/5" : "border-dashed"
      }`}
    />
  );
};

export type AmountSign = "all" | "credit" | "debit";

interface AmountRangeFilterProps {
  min: number | null;
  max: number | null;
  rangeMin: number;
  rangeMax: number;
  sign: AmountSign;
  creditCount: number;
  debitCount: number;
  onMinChange: (value: number | null) => void;
  onMaxChange: (value: number | null) => void;
  onSignChange: (value: AmountSign) => void;
}

export const AmountRangeFilter: React.FC<AmountRangeFilterProps> = ({
  min,
  max,
  rangeMin,
  rangeMax,
  sign,
  creditCount,
  debitCount,
  onMinChange,
  onMaxChange,
  onSignChange,
}) => {
  const isActive = min !== null || max !== null || sign !== "all";
  const effectiveMin = min ?? rangeMin;
  const effectiveMax = max ?? rangeMax;
  const [localSlider, setLocalSlider] = useState<[number, number] | null>(null);

  const displayMin = localSlider ? localSlider[0] : effectiveMin;
  const displayMax = localSlider ? localSlider[1] : effectiveMax;

  const formatLabel = (v: number) => {
    if (Math.abs(v) >= 1000) {
      return `${(v / 1000).toFixed(1)}k`;
    }
    return v.toFixed(0);
  };

  const signLabel =
    sign === "credit" ? "Credit" : sign === "debit" ? "Debit" : null;
  const rangeLabel =
    min !== null || max !== null
      ? `${formatLabel(effectiveMin)} - ${formatLabel(effectiveMax)}`
      : null;
  const label = [signLabel, rangeLabel].filter(Boolean).join(", ") || "Amount";

  const step = Math.max(1, Math.round((rangeMax - rangeMin) / 200));

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className={`h-8 w-full justify-between gap-1 text-xs font-normal ${
            isActive
              ? "border-primary/50 bg-primary/5"
              : "border-dashed text-muted-foreground"
          }`}
        >
          <span className="truncate">{label}</span>
          <ChevronDown className="h-3.5 w-3.5 flex-shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-72 space-y-4 p-4">
        <div className="flex gap-1">
          {[
            {
              label: "All",
              value: "all" as AmountSign,
              count: creditCount + debitCount,
            },
            {
              label: "Credit",
              value: "credit" as AmountSign,
              count: creditCount,
            },
            { label: "Debit", value: "debit" as AmountSign, count: debitCount },
          ].map((opt) => (
            <button
              key={opt.value}
              className={`flex-1 rounded px-2 py-1.5 text-xs transition-colors ${
                sign === opt.value
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted hover:bg-muted/80"
              }`}
              onClick={() => onSignChange(opt.value)}
            >
              {opt.label}
              <span
                className={`ml-1 ${
                  sign === opt.value ? "opacity-70" : "text-muted-foreground"
                }`}
              >
                ({opt.count})
              </span>
            </button>
          ))}
        </div>
        <Slider
          value={[displayMin, displayMax]}
          min={rangeMin}
          max={rangeMax}
          step={step}
          onValueChange={([newMin, newMax]) => {
            setLocalSlider([newMin, newMax]);
          }}
          onValueCommit={([newMin, newMax]) => {
            setLocalSlider(null);
            onMinChange(newMin <= rangeMin ? null : newMin);
            onMaxChange(newMax >= rangeMax ? null : newMax);
          }}
        />
        <div className="flex items-center gap-2">
          <div className="flex-1 space-y-1">
            <label className="text-xs text-muted-foreground">Min</label>
            <Input
              type="number"
              value={min ?? ""}
              placeholder={String(rangeMin)}
              onChange={(e) =>
                onMinChange(e.target.value ? Number(e.target.value) : null)
              }
              className="h-8 text-xs"
            />
          </div>
          <span className="mt-5 text-muted-foreground">-</span>
          <div className="flex-1 space-y-1">
            <label className="text-xs text-muted-foreground">Max</label>
            <Input
              type="number"
              value={max ?? ""}
              placeholder={String(rangeMax)}
              onChange={(e) =>
                onMaxChange(e.target.value ? Number(e.target.value) : null)
              }
              className="h-8 text-xs"
            />
          </div>
        </div>
        {isActive && (
          <Button
            variant="ghost"
            size="sm"
            className="h-7 w-full text-xs"
            onClick={() => {
              onMinChange(null);
              onMaxChange(null);
              onSignChange("all");
            }}
          >
            Clear
          </Button>
        )}
      </PopoverContent>
    </Popover>
  );
};
