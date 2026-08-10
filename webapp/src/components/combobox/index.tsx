import React, { useEffect, useId, useMemo, useRef, useState } from "react";
import { Check } from "lucide-react";

import { Input } from "components/ui/input";
import { Popover, PopoverContent, PopoverTrigger } from "components/ui/popover";
import { cn } from "lib/utils";

export interface ComboboxOption {
  value: string;
  label: string;
  /** Secondary text, searchable but shown quietly. */
  hint?: string;
}

export interface ComboboxGroup {
  label?: string;
  options: ComboboxOption[];
}

export interface ComboboxProps {
  value: string;
  groups: ComboboxGroup[];
  onChange: (value: string) => void | Promise<void>;
  /** Accessible name for the control. */
  label: string;
  searchPlaceholder?: string;
  /** What the closed control shows. Defaults to the selected option's label. */
  display?: React.ReactNode;
  triggerClassName?: string;
  contentClassName?: string;
  align?: "start" | "end";
  disabled?: boolean;
  id?: string;
}

function matches(option: ComboboxOption, query: string): boolean {
  const needle = query.trim().toLowerCase();
  if (!needle) {
    return true;
  }
  return (
    option.label.toLowerCase().includes(needle) ||
    option.value.toLowerCase().includes(needle) ||
    (option.hint ?? "").toLowerCase().includes(needle)
  );
}

/**
 * A select you can type into. Built on the popover rather than a command palette library: the
 * lists here (currencies, account types) are long enough to need search but not so exotic as to
 * justify another dependency.
 */
export const Combobox: React.FC<ComboboxProps> = ({
  value,
  groups,
  onChange,
  label,
  searchPlaceholder = "Search…",
  display,
  triggerClassName,
  contentClassName,
  align = "start",
  disabled,
  id,
}) => {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);
  const listId = useId();
  const listRef = useRef<HTMLDivElement>(null);

  const filtered = useMemo(
    () =>
      groups
        .map((group) => ({
          ...group,
          options: group.options.filter((option) => matches(option, query)),
        }))
        .filter((group) => group.options.length > 0),
    [groups, query],
  );
  const flat = useMemo(
    () => filtered.flatMap((group) => group.options),
    [filtered],
  );

  const selected = useMemo(
    () =>
      groups
        .flatMap((group) => group.options)
        .find((option) => option.value === value),
    [groups, value],
  );

  // Reopening starts from the current selection with a cleared search.
  const openedRef = useRef(false);
  useEffect(() => {
    if (open && !openedRef.current) {
      openedRef.current = true;
      setQuery("");
      const index = flat.findIndex((option) => option.value === value);
      setActiveIndex(index >= 0 ? index : 0);
    }
    if (!open) {
      openedRef.current = false;
    }
  }, [open, flat, value]);

  useEffect(() => {
    setActiveIndex(0);
  }, [query]);

  useEffect(() => {
    listRef.current
      ?.querySelector('[data-active="true"]')
      ?.scrollIntoView({ block: "nearest" });
  }, [activeIndex, filtered]);

  const commit = async (option: ComboboxOption) => {
    setOpen(false);
    await onChange(option.value);
  };

  const onKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      if (flat.length === 0) {
        return;
      }
      const step = event.key === "ArrowDown" ? 1 : -1;
      setActiveIndex((current) => (current + step + flat.length) % flat.length);
    }
    if (event.key === "Enter") {
      event.preventDefault();
      const option = flat[activeIndex];
      if (option) {
        commit(option);
      }
    }
  };

  let optionIndex = -1;

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button
          type="button"
          id={id}
          disabled={disabled}
          aria-label={label}
          className={cn(
            "inline-flex items-center gap-1 rounded px-1 text-left transition-colors",
            "hover:bg-accent/60 focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring",
            "disabled:pointer-events-none disabled:opacity-50",
            triggerClassName,
          )}
        >
          {display ?? selected?.label ?? value}
        </button>
      </PopoverTrigger>
      <PopoverContent
        align={align}
        className={cn("w-56 p-0", contentClassName)}
        onOpenAutoFocus={(event) => {
          // Focus the search box, not the first option.
          event.preventDefault();
          (event.currentTarget as HTMLElement)
            ?.querySelector<HTMLInputElement>("input")
            ?.focus();
        }}
      >
        <div className="border-b border-border p-1.5">
          <Input
            role="combobox"
            aria-expanded="true"
            aria-controls={listId}
            aria-activedescendant={
              flat[activeIndex] ? `${listId}-${activeIndex}` : undefined
            }
            aria-label={searchPlaceholder}
            value={query}
            placeholder={searchPlaceholder}
            className="h-8"
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={onKeyDown}
          />
        </div>
        <div
          ref={listRef}
          id={listId}
          role="listbox"
          aria-label={label}
          className="max-h-64 overflow-y-auto p-1"
        >
          {flat.length === 0 && (
            <p className="px-2 py-3 text-center text-sm text-muted-foreground">
              Nothing matches &apos;{query}&apos;.
            </p>
          )}
          {filtered.map((group, groupIndex) => (
            <div key={group.label ?? groupIndex}>
              {group.label && (
                <p className="px-2 pb-0.5 pt-2 text-[10px] font-medium uppercase tracking-[0.11em] text-muted-foreground">
                  {group.label}
                </p>
              )}
              {group.options.map((option) => {
                optionIndex += 1;
                const index = optionIndex;
                const isSelected = option.value === value;
                const isActive = index === activeIndex;
                return (
                  <button
                    type="button"
                    key={option.value}
                    id={`${listId}-${index}`}
                    role="option"
                    aria-selected={isSelected}
                    data-active={isActive}
                    onMouseEnter={() => setActiveIndex(index)}
                    onClick={() => commit(option)}
                    className={cn(
                      "flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-left text-sm",
                      isActive && "bg-accent text-accent-foreground",
                    )}
                  >
                    <Check
                      className={cn(
                        "h-3.5 w-3.5 shrink-0",
                        isSelected ? "opacity-100" : "opacity-0",
                      )}
                    />
                    <span className="min-w-0 flex-1 truncate">
                      {option.label}
                    </span>
                    {option.hint && (
                      <span className="shrink-0 text-xs text-muted-foreground">
                        {option.hint}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          ))}
        </div>
      </PopoverContent>
    </Popover>
  );
};

export default Combobox;
