import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Button, Card, toast } from "@heroui/react";
import { api } from "../api/client";
import { useNavigate } from "react-router-dom";
import { useAppTheme } from "../components/ThemeProvider";
import { Sun, Moon, Laptop } from "lucide-react";

export function Settings() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { theme, setTheme } = useAppTheme();

  const seedMutation = useMutation({
    mutationFn: api.seedDatabase,
    onSuccess: () => {
      void queryClient.invalidateQueries(); // invalidate all queries to refresh UI data
      toast.success("Example developer test data seeded successfully!");
      // Redirect to dashboard after a short delay
      setTimeout(() => navigate("/"), 1500);
    },
    onError: (err: any) => {
      const msg = err instanceof Error ? err.message : "Failed to seed database.";
      if (msg.includes("already contains")) {
        toast.danger("Database already contains records; seeding skipped.");
      } else {
        toast.danger(msg);
      }
    },
  });

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="flex flex-col gap-1">
        <h2 className="text-2xl font-bold tracking-tight">System Settings</h2>
        <p className="text-muted text-sm">
          Configure application behavior, view database details, and manage reference or developer data.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card className="p-6 flex flex-col justify-between border border-border/40 bg-gradient-to-br from-surface to-surface/85 shadow-lg relative overflow-hidden group">
          {/* Decorative subtle gradient background ornament */}
          <div className="absolute -top-12 -right-12 w-32 h-32 bg-accent/10 rounded-full blur-xl group-hover:bg-accent/15 transition-all duration-500" />

          <div className="space-y-3 relative z-10">
            <div className="inline-flex items-center justify-center p-2.5 rounded-lg bg-accent/10 text-accent">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
                />
              </svg>
            </div>
            <h3 className="text-lg font-semibold tracking-tight">Demo & Test Data</h3>
            <p className="text-sm text-muted leading-relaxed">
              Quickly populate your local database with mock enterprise records (agreements, products, hosts, and CPU profiles). Perfect for exploring compliance calculation dashboards and exports.
            </p>
            <div className="bg-surface-hover/50 rounded-lg p-3.5 border border-border/30 text-xs text-muted space-y-2 mt-4">
              <div className="font-semibold text-foreground/80">Seeded Records Include:</div>
              <ul className="list-disc pl-4 space-y-1">
                <li>Omni Consumer Products (RAC, Diagnostics, Tuning Packs)</li>
                <li>Weyland-Yutani Corp (WebLogic & standard DB NUP licenses)</li>
                <li>Tyrell Corporation (Under-review Partitioning entitlements)</li>
                <li>Hosts with custom CPU sockets, core factor matching, and NUP counts</li>
              </ul>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-border/30 flex items-center justify-between gap-4">
            <span className="text-xs text-warning/80 flex items-center gap-1.5 font-medium">
              <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
              Only runs when database is empty
            </span>
            <Button
              variant="primary"
              className="font-medium hover:scale-[1.02] active:scale-[0.98] transition-transform duration-200"
              isDisabled={seedMutation.isPending}
              onPress={() => seedMutation.mutate()}
            >
              {seedMutation.isPending ? "Loading..." : "Load Example Data"}
            </Button>
          </div>
        </Card>

        <Card className="p-6 flex flex-col justify-between border border-border/40 bg-gradient-to-br from-surface to-surface/85 shadow-lg relative overflow-hidden group">
          <div className="absolute -top-12 -right-12 w-32 h-32 bg-emerald-500/10 rounded-full blur-xl group-hover:bg-emerald-500/15 transition-all duration-500" />

          <div className="space-y-3 relative z-10">
            <div className="inline-flex items-center justify-center p-2.5 rounded-lg bg-emerald-500/10 text-emerald-400">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                />
              </svg>
            </div>
            <h3 className="text-lg font-semibold tracking-tight">System Info</h3>
            <p className="text-sm text-muted leading-relaxed">
              View system architecture parameters, active database connections, and operational configuration values.
            </p>
            <div className="bg-surface-hover/50 rounded-lg p-3.5 border border-border/30 text-xs font-mono space-y-2 mt-4">
              <div className="flex justify-between">
                <span className="text-muted">Database Engine:</span>
                <span className="text-foreground/80 font-semibold">SQLite (local)</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted">Target Path:</span>
                <span className="text-foreground/80 break-all select-all">data/license_tracker.db</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted">Vite API Host:</span>
                <span className="text-foreground/80">Local Server</span>
              </div>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-border/30 flex items-center justify-between">
            <span className="text-xs text-muted">Version: 0.4.0 (Developer Beta)</span>
            <Button variant="tertiary" className="text-xs font-semibold cursor-default" isDisabled>
              Connection Healthy
            </Button>
          </div>
        </Card>

        <Card className="p-6 border border-border/40 bg-gradient-to-br from-surface to-surface/85 shadow-lg relative overflow-hidden group md:col-span-2">
          {/* Decorative subtle gradient background ornament */}
          <div className="absolute -top-12 -right-12 w-32 h-32 bg-accent/10 rounded-full blur-xl group-hover:bg-accent/15 transition-all duration-500" />

          <div className="space-y-4 relative z-10">
            <div className="inline-flex items-center justify-center p-2.5 rounded-lg bg-accent/10 text-accent">
              <Sun className="w-5 h-5 animate-spin-slow" />
            </div>
            <div>
              <h3 className="text-lg font-semibold tracking-tight">Appearance</h3>
              <p className="text-sm text-muted leading-relaxed">
                Choose how Oracle License Manager looks on your device. Set a preferred color scheme or let it match your system.
              </p>
            </div>

            <div className="grid grid-cols-3 gap-3 pt-2">
              {[
                { value: "light", label: "Light", icon: Sun, color: "text-amber-400" },
                { value: "dark", label: "Dark", icon: Moon, color: "text-indigo-400" },
                { value: "system", label: "System Default", icon: Laptop, color: "text-emerald-400" },
              ].map((option) => {
                const Icon = option.icon;
                const isActive = theme === option.value;
                return (
                  <button
                    key={option.value}
                    onClick={() => setTheme(option.value)}
                    className={`flex flex-col items-center justify-center gap-3 p-4 rounded-xl border transition-all duration-300 cursor-pointer ${
                      isActive
                        ? "border-accent/80 bg-accent/10 shadow-[0_0_12px_color-mix(in_srgb,var(--accent)_20%,transparent)]"
                        : "border-border/30 bg-surface/50 hover:bg-surface-hover/80 hover:border-border/80"
                    }`}
                  >
                    <Icon className={`w-5 h-5 ${option.color} transition-transform duration-300 group-hover:scale-110`} />
                    <span className={`text-xs font-medium ${isActive ? "text-foreground font-semibold" : "text-muted"}`}>
                      {option.label}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
