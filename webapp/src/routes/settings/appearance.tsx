import React, { useContext } from "react";

import { ThemeContext, Theme } from "contexts";
import { Separator } from "components/ui/separator";
import { cn } from "lib/utils";

interface ThemeCardProps {
  label: string;
  value: Theme;
  active: boolean;
  onClick: () => void;
}

const ThemeCard: React.FC<ThemeCardProps> = ({
  label,
  value,
  active,
  onClick,
}) => {
  const isLight = value === "light";
  return (
    <button
      onClick={onClick}
      className={cn(
        "flex flex-col items-center gap-3 rounded-lg border-2 p-4 transition-colors",
        active
          ? "border-primary bg-primary/5"
          : "border-border hover:border-muted-foreground/30",
      )}
    >
      {/* Mini preview */}
      <div
        className={cn(
          "w-36 rounded-md border p-3",
          isLight
            ? "border-gray-200 bg-gray-50"
            : "border-gray-700 bg-gray-900",
        )}
      >
        <div
          className={cn(
            "mb-2 h-2 w-16 rounded",
            isLight ? "bg-gray-300" : "bg-gray-700",
          )}
        />
        <div
          className={cn(
            "mb-1 h-2 w-full rounded",
            isLight ? "bg-gray-200" : "bg-gray-800",
          )}
        />
        <div
          className={cn(
            "h-2 w-3/4 rounded",
            isLight ? "bg-gray-200" : "bg-gray-800",
          )}
        />
      </div>
      <span className="text-sm font-medium">{label}</span>
    </button>
  );
};

export const AppearanceSettings: React.FC = () => {
  const { theme, setTheme } = useContext(ThemeContext);

  return (
    <>
      <div className="mb-4">
        <h3 className="text-2xl font-semibold">Appearance</h3>
        <Separator className="mt-2" />
      </div>
      <div className="mb-4">
        <h4 className="text-lg font-medium">Theme</h4>
        <p className="text-sm text-muted-foreground mt-1">
          Choose between light and dark mode.
        </p>
      </div>
      <div className="flex gap-4">
        <ThemeCard
          label="Light"
          value="light"
          active={theme === "light"}
          onClick={() => setTheme("light")}
        />
        <ThemeCard
          label="Dark"
          value="dark"
          active={theme === "dark"}
          onClick={() => setTheme("dark")}
        />
      </div>
    </>
  );
};
