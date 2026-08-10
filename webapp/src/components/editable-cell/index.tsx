import React, { useEffect, useRef, useState } from "react";

import { Input } from "components/ui/input";
import { cn } from "lib/utils";

export interface EditableCellProps {
  value: string;
  onSave: (newValue: string) => Promise<void> | void;
  /** Rendered when not editing. Defaults to the raw value. */
  display?: React.ReactNode;
  placeholder?: string;
  align?: "left" | "right";
  type?: "text" | "number";
  disabled?: boolean;
  className?: string;
}

/**
 * Click-to-edit table cell: Enter or blur saves, Escape reverts.
 *
 * Same interaction as the inline account name editor in the linked accounts settings, generalised
 * so it can be used for every cell of the portfolio tables.
 */
export const EditableCell: React.FC<EditableCellProps> = ({
  value,
  onSave,
  display,
  placeholder,
  align = "left",
  type = "text",
  disabled,
  className,
}) => {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(value);
  const [saving, setSaving] = useState(false);
  const cancelled = useRef(false);

  useEffect(() => {
    if (!editing) {
      setDraft(value);
    }
  }, [value, editing]);

  const save = async () => {
    if (cancelled.current) {
      return;
    }
    setEditing(false);
    if (draft === value) {
      return;
    }
    setSaving(true);
    try {
      await onSave(draft);
    } finally {
      setSaving(false);
    }
  };

  const cancel = () => {
    cancelled.current = true;
    setDraft(value);
    setEditing(false);
  };

  if (disabled) {
    return (
      <span
        className={cn(
          "block truncate text-sm text-muted-foreground",
          className,
        )}
      >
        {display ?? value ?? placeholder}
      </span>
    );
  }

  if (editing) {
    return (
      <Input
        value={draft}
        type={type}
        onChange={(e) => setDraft(e.target.value)}
        onBlur={save}
        onKeyDown={(e) => {
          if (e.key === "Enter") {
            e.preventDefault();
            save();
          }
          if (e.key === "Escape") {
            cancel();
          }
        }}
        autoFocus
        placeholder={placeholder}
        className={cn(
          "h-7 text-sm",
          align === "right" && "text-right",
          className,
        )}
      />
    );
  }

  const isEmpty = value === "" || value === null || value === undefined;
  return (
    <button
      type="button"
      onClick={() => {
        cancelled.current = false;
        setEditing(true);
      }}
      disabled={saving}
      className={cn(
        "w-full truncate rounded px-1 py-0.5 text-sm hover:bg-accent/60 focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring",
        align === "right" ? "text-right" : "text-left",
        isEmpty && "text-muted-foreground",
        saving && "opacity-50",
        className,
      )}
    >
      {display ?? (isEmpty ? (placeholder ?? "—") : value)}
    </button>
  );
};

export default EditableCell;
