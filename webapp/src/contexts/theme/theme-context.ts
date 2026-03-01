import { createContext } from "react";

export type Theme = "light" | "dark";

type ThemeContextProps = {
  theme: Theme;
  setTheme(theme: Theme): void;
};

export const ThemeContext = createContext<ThemeContextProps>({
  theme: "dark",
  setTheme: () => {},
});

export default ThemeContext;
