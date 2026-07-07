import { createContext, useContext, type ReactNode } from "react";
import { useTheme as useHeroTheme } from "@heroui/react";

interface ThemeContextType {
  theme: string;
  resolvedTheme: string | undefined;
  setTheme: (theme: string) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: ReactNode }) {
  // We use HeroUI's useTheme, defaulting to "dark" as the application originally did
  const themeState = useHeroTheme("dark");

  return (
    <ThemeContext.Provider value={themeState}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useAppTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useAppTheme must be used within a ThemeProvider");
  }
  return context;
}
