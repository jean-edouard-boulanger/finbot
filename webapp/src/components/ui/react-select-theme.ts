import type { StylesConfig } from "react-select";

export const themedSelectStyles: StylesConfig = {
  control: (base, state) => ({
    ...base,
    backgroundColor: "hsl(var(--background))",
    borderColor: state.isFocused
      ? "hsl(var(--ring))"
      : "hsl(var(--input))",
    borderRadius: "var(--radius)",
    boxShadow: state.isFocused
      ? "0 0 0 2px hsl(var(--ring) / 0.3)"
      : "none",
    "&:hover": {
      borderColor: "hsl(var(--ring))",
    },
    minHeight: "2.5rem",
  }),
  menu: (base) => ({
    ...base,
    backgroundColor: "hsl(var(--popover))",
    border: "1px solid hsl(var(--border))",
    borderRadius: "var(--radius)",
    boxShadow:
      "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)",
    zIndex: 50,
  }),
  option: (base, state) => ({
    ...base,
    backgroundColor: state.isSelected
      ? "hsl(var(--primary))"
      : state.isFocused
        ? "hsl(var(--accent))"
        : "transparent",
    color: state.isSelected
      ? "hsl(var(--primary-foreground))"
      : "hsl(var(--foreground))",
    "&:active": {
      backgroundColor: "hsl(var(--accent))",
    },
  }),
  singleValue: (base) => ({
    ...base,
    color: "hsl(var(--foreground))",
  }),
  input: (base) => ({
    ...base,
    color: "hsl(var(--foreground))",
  }),
  placeholder: (base) => ({
    ...base,
    color: "hsl(var(--muted-foreground))",
  }),
  indicatorSeparator: (base) => ({
    ...base,
    backgroundColor: "hsl(var(--border))",
  }),
  dropdownIndicator: (base) => ({
    ...base,
    color: "hsl(var(--muted-foreground))",
    "&:hover": {
      color: "hsl(var(--foreground))",
    },
  }),
  clearIndicator: (base) => ({
    ...base,
    color: "hsl(var(--muted-foreground))",
    "&:hover": {
      color: "hsl(var(--foreground))",
    },
  }),
  multiValue: (base) => ({
    ...base,
    backgroundColor: "hsl(var(--secondary))",
    borderRadius: "calc(var(--radius) - 4px)",
  }),
  multiValueLabel: (base) => ({
    ...base,
    color: "hsl(var(--secondary-foreground))",
  }),
  multiValueRemove: (base) => ({
    ...base,
    color: "hsl(var(--muted-foreground))",
    "&:hover": {
      backgroundColor: "hsl(var(--destructive))",
      color: "hsl(var(--destructive-foreground))",
    },
  }),
  noOptionsMessage: (base) => ({
    ...base,
    color: "hsl(var(--muted-foreground))",
  }),
  loadingMessage: (base) => ({
    ...base,
    color: "hsl(var(--muted-foreground))",
  }),
};
