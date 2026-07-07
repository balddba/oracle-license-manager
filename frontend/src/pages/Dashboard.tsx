import { useQuery } from "@tanstack/react-query";
import { Alert, Button, Card } from "@heroui/react";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api, type ProductLicenseSummary } from "../api/client";
import { ErrorAlert } from "../components/ErrorAlert";
import { DashboardSkeleton } from "../components/PageSkeleton";

type RenewalUrgency = "danger" | "warning" | "default";

function StatCard({
  label,
  value,
  valueClassName,
}: {
  label: string;
  value: number;
  valueClassName?: string;
}) {
  return (
    <Card className="p-4">
      <p className="text-sm text-muted">{label}</p>
      <p className={`mt-2 text-3xl font-semibold tabular-nums ${valueClassName ?? ""}`}>
        {value}
      </p>
    </Card>
  );
}

function RenewalStatCard({
  label,
  value,
  urgency,
}: {
  label: string;
  value: number;
  urgency: RenewalUrgency;
}) {
  const valueClassName =
    urgency === "danger"
      ? "text-danger"
      : urgency === "warning"
        ? "text-warning"
        : undefined;

  return <StatCard label={label} value={value} valueClassName={valueClassName} />;
}

function formatBalance(balance: number): { label: string; className: string } {
  if (balance < 0) {
    return {
      label: `Shortfall of ${Math.abs(balance)}`,
      className: "font-medium text-danger",
    };
  }
  if (balance > 0) {
    return {
      label: `Surplus of ${balance}`,
      className: "font-medium text-warning",
    };
  }
  return {
    label: "Balanced",
    className: "font-medium text-success",
  };
}

function LicenseRow({ row }: { row: ProductLicenseSummary }) {
  const balance = formatBalance(row.balance);

  return (
    <tr className="border-t border-separator">
      <td className="px-4 py-2">
        <Link
          to={`/products?search=${encodeURIComponent(row.product_name)}`}
          className="text-link hover:underline"
        >
          {row.product_name}
        </Link>
      </td>
      <td className="px-4 py-2 text-right tabular-nums">{row.cores_licensed}</td>
      <td className="px-4 py-2 text-right tabular-nums">{row.nups_licensed}</td>
      <td className="px-4 py-2 text-right tabular-nums">
        <Link to="/hosts" className="text-link hover:underline" title="View hosts">
          {row.cores_in_use}
        </Link>
      </td>
      <td className="px-4 py-2 text-right tabular-nums text-muted">
        {row.nups_in_use ?? "—"}
      </td>
      <td className={`px-4 py-2 text-right tabular-nums ${balance.className}`}>
        {balance.label}
      </td>
    </tr>
  );
}

export function Dashboard() {
  const [shortfallsOnly, setShortfallsOnly] = useState(false);

  const { data, isLoading, error } = useQuery({
    queryKey: ["dashboard"],
    queryFn: api.getDashboard,
  });

  const shortfallCount = useMemo(
    () => data?.license_inventory.filter((row) => row.balance < 0).length ?? 0,
    [data],
  );

  const visibleInventory = useMemo(() => {
    if (!data) {
      return [];
    }
    if (!shortfallsOnly) {
      return data.license_inventory;
    }
    return data.license_inventory.filter((row) => row.balance < 0);
  }, [data, shortfallsOnly]);

  if (isLoading) {
    return <DashboardSkeleton />;
  }
  if (error || !data) {
    return <ErrorAlert title="Dashboard unavailable" message="Failed to load dashboard." />;
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold">Dashboard</h2>

      {shortfallCount > 0 ? (
        <Alert status="danger">
          <Alert.Indicator />
          <Alert.Content>
            <Alert.Title>
              {shortfallCount} product{shortfallCount === 1 ? "" : "s"} under-licensed
            </Alert.Title>
            <Alert.Description>
              Review the license inventory below and add entitlements or reduce server assignments.
            </Alert.Description>
          </Alert.Content>
          <Button
            size="sm"
            variant="danger"
            onPress={() => setShortfallsOnly(true)}
            className={shortfallsOnly ? "hidden" : undefined}
          >
            Show shortfalls
          </Button>
        </Alert>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Agreements" value={data.agreement_count} />
        <StatCard label="Products" value={data.product_count} />
        <StatCard label="Hosts" value={data.host_count} />
        <StatCard label="Physical cores" value={data.total_physical_cores} />
      </div>
      <div className="grid gap-4 sm:grid-cols-3">
        <RenewalStatCard
          label="Renewals (30 days)"
          value={data.renewals_30_days}
          urgency="danger"
        />
        <RenewalStatCard
          label="Renewals (60 days)"
          value={data.renewals_60_days}
          urgency="warning"
        />
        <RenewalStatCard label="Renewals (90 days)" value={data.renewals_90_days} urgency="default" />
      </div>

      <div className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h3 className="text-lg font-medium">License inventory</h3>
          {data.license_inventory.length > 0 ? (
            <Button
              size="sm"
              variant={shortfallsOnly ? "primary" : "secondary"}
              onPress={() => setShortfallsOnly((current) => !current)}
            >
              {shortfallsOnly ? "Show all products" : "Shortfalls only"}
            </Button>
          ) : null}
        </div>
        <p className="text-sm text-muted">
          All products pooled across CSI agreements. Core and NUP in-use counts reflect assigned
          server inventory.
        </p>

        {data.license_inventory.length === 0 ? (
          <Card className="p-4">
            <p className="text-sm text-muted">
              No product entitlements yet. Add products to agreements to see license inventory here.
            </p>
          </Card>
        ) : visibleInventory.length === 0 ? (
          <Card className="p-4">
            <p className="text-sm text-success">No products are currently under-licensed.</p>
          </Card>
        ) : (
          <div className="overflow-hidden rounded-lg border border-border bg-surface">
            <table className="min-w-full text-sm">
              <thead className="bg-default text-left">
                <tr>
                  <th className="px-4 py-2">Product</th>
                  <th className="px-4 py-2 text-right">Cores licensed</th>
                  <th className="px-4 py-2 text-right">NUPs licensed</th>
                  <th className="px-4 py-2 text-right">Cores in use</th>
                  <th className="px-4 py-2 text-right">NUPs in use</th>
                  <th className="px-4 py-2 text-right">Surplus / shortfall</th>
                </tr>
              </thead>
              <tbody>
                {visibleInventory.map((row) => (
                  <LicenseRow key={row.product_name} row={row} />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
