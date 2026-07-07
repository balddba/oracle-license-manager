import { Link, NavLink } from "react-router-dom";
import logoLight from "../assets/logo.png";
import logoDark from "../assets/logo_dark.png";
import { useAppTheme } from "./ThemeProvider";
import { Sun, Moon } from "lucide-react";

const links = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/agreements", label: "Agreements", end: false },
  { to: "/products", label: "Products", end: false },
  { to: "/hosts", label: "Hosts", end: false },
  { to: "/reports", label: "Reports", end: false },
  { to: "/settings", label: "Settings", end: false },
];

function navLinkClass({ isActive }: { isActive: boolean }) {
  return isActive
    ? "font-medium text-foreground"
    : "text-muted hover:text-foreground";
}

export function Layout({ children }: { children: React.ReactNode }) {
  const { setTheme, resolvedTheme } = useAppTheme();

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border bg-surface">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Link to="/" className="flex items-center gap-2">
            <img
              src={resolvedTheme === "dark" ? logoDark : logoLight}
              alt="Oracle License Manager"
              className="h-20 w-auto object-contain"
            />
          </Link>
          <div className="flex items-center gap-6">
            <nav className="flex gap-4 text-sm">
              {links.map((link) => (
                <NavLink key={link.to} to={link.to} end={link.end} className={navLinkClass}>
                  {link.label}
                </NavLink>
              ))}
            </nav>
            <div className="h-4 w-[1px] bg-border/60" />
            <button
              onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}
              className="p-2 text-muted hover:text-foreground rounded-lg hover:bg-surface-hover/60 border border-border/30 hover:border-border transition-all duration-200 flex items-center justify-center cursor-pointer"
              aria-label="Toggle Theme"
            >
              {resolvedTheme === "dark" ? (
                <Sun className="h-4 w-4 text-amber-400" />
              ) : (
                <Moon className="h-4 w-4 text-indigo-400" />
              )}
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
    </div>
  );
}
