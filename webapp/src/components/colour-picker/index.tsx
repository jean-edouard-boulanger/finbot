import React, { useId, useState } from "react";

import { Popover, PopoverContent, PopoverTrigger } from "components/ui/popover";
import { cn } from "lib/utils";

/**
 * Mirrors ACCOUNTS_PALETTE server side, used when the caller has not loaded the formatting rules
 * yet so the control is never empty.
 */
export const DEFAULT_ACCOUNT_COLOURS = [
  "#ef233c",
  "#0A9396",
  "#f72585",
  "#52b788",
  "#07E4A2",
  "#480ca8",
  "#9B2226",
  "#ff9f1c",
  "#2b2d42",
];

export interface ColourPickerProps {
  colour: string;
  onChange?: (newColour: string) => void;
  /** Palette to choose from. Defaults to the accounts palette. */
  colours?: Array<string>;
  /** Describes what is being coloured, e.g. "Portfolio colour". */
  label?: string;
  disabled?: boolean;
  /** Set this to point a <Label htmlFor> at the control. */
  id?: string;
}

/**
 * Picks one colour from a fixed palette.
 *
 * Deliberately not a free colour picker: these colours key accounts to their series in every chart
 * in the app, so they have to come from the shared palette to stay distinguishable.
 */
export const ColourPicker: React.FC<ColourPickerProps> = ({
  colour,
  onChange,
  colours = DEFAULT_ACCOUNT_COLOURS,
  label = "Colour",
  disabled,
  id,
}) => {
  const [open, setOpen] = useState(false);
  const groupName = useId();

  const select = (newColour: string) => {
    onChange?.(newColour);
    setOpen(false);
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button
          type="button"
          id={id}
          disabled={disabled}
          aria-label={`${label}: ${colour}`}
          className={cn(
            "flex h-7 w-7 items-center justify-center rounded-md border border-border transition-colors",
            "hover:bg-accent focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring",
            "disabled:pointer-events-none disabled:opacity-50",
          )}
        >
          <span
            aria-hidden="true"
            className="h-3.5 w-3.5 rounded-full"
            style={{ backgroundColor: colour }}
          />
        </button>
      </PopoverTrigger>
      <PopoverContent align="start" className="w-auto p-2">
        <div
          role="radiogroup"
          aria-label={label}
          className="grid grid-cols-5 gap-1.5"
        >
          {colours.map((candidate) => {
            const selected =
              candidate.toLowerCase() === (colour ?? "").toLowerCase();
            return (
              <label
                key={candidate}
                className="cursor-pointer"
                title={candidate}
              >
                <input
                  type="radio"
                  name={groupName}
                  value={candidate}
                  checked={selected}
                  onChange={() => select(candidate)}
                  className="peer sr-only"
                />
                <span
                  aria-hidden="true"
                  className={cn(
                    "block h-6 w-6 rounded-md ring-offset-2 ring-offset-popover transition-shadow",
                    "peer-focus-visible:ring-2 peer-focus-visible:ring-ring",
                    selected && "ring-2 ring-foreground",
                  )}
                  style={{ backgroundColor: candidate }}
                />
              </label>
            );
          })}
        </div>
      </PopoverContent>
    </Popover>
  );
};

export default ColourPicker;
