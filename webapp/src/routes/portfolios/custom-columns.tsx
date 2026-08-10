import React from "react";
import { ChevronDown, Plus, Trash2 } from "lucide-react";

import { PortfolioCustomColumn } from "clients";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "components/ui/select";

import { EditableCell } from "components/editable-cell";
import { Button } from "components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "components/ui/dropdown-menu";

export type ColumnType = NonNullable<PortfolioCustomColumn["type"]>;

export const COLUMN_TYPES: Array<{ value: ColumnType; label: string }> = [
  { value: "text", label: "Text" },
  { value: "number", label: "Number" },
  { value: "date", label: "Date" },
];

/**
 * Keys address the values stored against each holding and are carried into snapshots, so they are
 * assigned once from the first label and then left alone. Renaming a column changes what you read,
 * not where its values live.
 */
export function makeColumnKey(label: string, taken: string[]): string {
  const base = label.trim().slice(0, 48) || "Column";
  let candidate = base;
  let suffix = 2;
  while (taken.includes(candidate)) {
    candidate = `${base} ${suffix}`;
    suffix += 1;
  }
  return candidate;
}

interface CustomColumnHeaderProps {
  column: PortfolioCustomColumn;
  onRename: (label: string) => Promise<void> | void;
  onTypeChange: (type: ColumnType) => Promise<void> | void;
  onRemove: () => void;
}

/**
 * Column headers are where columns live, so that is where they are edited: the label is
 * click-to-edit and the rest hides behind the header's own menu.
 */
export const CustomColumnHeader: React.FC<CustomColumnHeaderProps> = ({
  column,
  onRename,
  onTypeChange,
  onRemove,
}) => (
  <div className="group/col flex items-center gap-0.5">
    <EditableCell
      value={column.label || column.key}
      onSave={onRename}
      className="font-register text-[13px] italic text-muted-foreground"
    />
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          type="button"
          size="icon"
          variant="ghost"
          aria-label={`Options for the ${column.label || column.key} column`}
          className="h-5 w-5 shrink-0 opacity-0 transition-opacity focus-visible:opacity-100 group-hover/col:opacity-100 data-[state=open]:opacity-100"
        >
          <ChevronDown className="h-3 w-3" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start">
        <DropdownMenuLabel className="text-xs font-normal text-muted-foreground">
          Shows
        </DropdownMenuLabel>
        <DropdownMenuRadioGroup
          value={column.type ?? "text"}
          onValueChange={(value) => onTypeChange(value as ColumnType)}
        >
          {COLUMN_TYPES.map((type) => (
            <DropdownMenuRadioItem key={type.value} value={type.value}>
              {type.label}
            </DropdownMenuRadioItem>
          ))}
        </DropdownMenuRadioGroup>
        <DropdownMenuSeparator />
        <DropdownMenuItem className="text-destructive" onClick={onRemove}>
          <Trash2 className="mr-2 h-3.5 w-3.5" />
          Remove column
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  </div>
);

export const AddColumnButton: React.FC<{ onAdd: () => void }> = ({ onAdd }) => (
  <Button
    type="button"
    size="icon"
    variant="ghost"
    aria-label="Add a custom column"
    title="Add a custom column"
    className="h-6 w-6 text-muted-foreground"
    onClick={onAdd}
  >
    <Plus className="h-3.5 w-3.5" />
  </Button>
);

interface InlineSelectProps {
  label: string;
  value: string;
  options: Array<{ value: string; label: string }>;
  onChange: (value: string) => Promise<void> | void;
}

/**
 * A select that reads as plain text until you reach for it, for the descriptive fields that sit
 * alongside a heading rather than in a form.
 */
export const InlineSelect: React.FC<InlineSelectProps> = ({
  label,
  value,
  options,
  onChange,
}) => (
  <Select value={value} onValueChange={onChange}>
    <SelectTrigger
      aria-label={label}
      className="h-auto w-auto justify-start gap-0.5 border-0 bg-transparent px-1 py-0 text-[11px] leading-tight text-muted-foreground shadow-none hover:text-foreground focus:ring-0 focus-visible:ring-2 focus-visible:ring-ring [&>svg]:h-3 [&>svg]:w-3 [&>svg]:opacity-40"
    >
      <SelectValue />
    </SelectTrigger>
    <SelectContent>
      {options.map((option) => (
        <SelectItem key={option.value} value={option.value}>
          {option.label}
        </SelectItem>
      ))}
    </SelectContent>
  </Select>
);
