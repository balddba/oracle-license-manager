import { useQuery } from "@tanstack/react-query";
import { Button, Card } from "@heroui/react";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  api,
  formatHostEnvironment,
  formatHostLicenseType,
  type HostListItem,
  type LicenseDetail,
  type ProductLicenseSummary,
} from "../api/client";
import { ErrorAlert } from "../components/ErrorAlert";
import { ReportCharts } from "../components/ReportCharts";
import { TablePageSkeleton } from "../components/PageSkeleton";
import { formatLicenseMetric } from "../lib/licenseMetrics";

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

function ComplianceTable({ rows }: { rows: ProductLicenseSummary[] }) {
  if (rows.length === 0) {
    return (
      <Card className="p-4">
        <p className="text-sm text-muted">No product compliance rows match the current filter.</p>
      </Card>
    );
  }

  return (
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
          {rows.map((row) => {
            const balance = formatBalance(row.balance);
            return (
              <tr key={row.product_name} className="border-t border-separator">
                <td className="px-4 py-2">{row.product_name}</td>
                <td className="px-4 py-2 text-right tabular-nums">{row.cores_licensed}</td>
                <td className="px-4 py-2 text-right tabular-nums">{row.nups_licensed}</td>
                <td className="px-4 py-2 text-right tabular-nums">{row.cores_in_use}</td>
                <td className="px-4 py-2 text-right tabular-nums">{row.nups_in_use ?? "—"}</td>
                <td className={`px-4 py-2 text-right tabular-nums ${balance.className}`}>
                  {balance.label}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function AgreementsTable({ agreements }: { agreements: LicenseDetail[] }) {
  if (agreements.length === 0) {
    return (
      <Card className="p-4">
        <p className="text-sm text-muted">No license agreements recorded.</p>
      </Card>
    );
  }

  return (
    <div className="overflow-hidden rounded-lg border border-border bg-surface">
      <table className="min-w-full text-sm">
        <thead className="bg-default text-left">
          <tr>
            <th className="px-4 py-2">CSI</th>
            <th className="px-4 py-2">Customer</th>
            <th className="px-4 py-2">Status</th>
            <th className="px-4 py-2">Renewal</th>
            <th className="px-4 py-2">Entitlements</th>
          </tr>
        </thead>
        <tbody>
          {agreements.map((agreement) => (
            <tr key={agreement.id} className="border-t border-separator">
              <td className="px-4 py-2">
                <Link className="text-link hover:underline" to={`/agreements/${agreement.id}`}>
                  {agreement.csi}
                </Link>
              </td>
              <td className="px-4 py-2">{agreement.customer_name}</td>
              <td className="px-4 py-2">{agreement.status}</td>
              <td className="px-4 py-2">{agreement.renewal_date ?? "—"}</td>
              <td className="max-w-lg px-4 py-2">
                {agreement.products.length === 0 ? (
                  <span className="text-muted">No products</span>
                ) : (
                  <ul className="space-y-1">
                    {agreement.products.map((product) => (
                      <li key={product.id}>
                        {product.product_name}
                        {product.option_name ? ` (${product.option_name})` : ""}: {product.quantity}{" "}
                        {formatLicenseMetric(product.metric)}
                      </li>
                    ))}
                  </ul>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function HostsTable({ hosts }: { hosts: HostListItem[] }) {
  if (hosts.length === 0) {
    return (
      <Card className="p-4">
        <p className="text-sm text-muted">No hosts in inventory.</p>
      </Card>
    );
  }

  return (
    <div className="overflow-hidden rounded-lg border border-border bg-surface">
      <table className="min-w-full text-sm">
        <thead className="bg-default text-left">
          <tr>
            <th className="px-4 py-2">Hostname</th>
            <th className="px-4 py-2">Environment</th>
            <th className="px-4 py-2">License type</th>
            <th className="px-4 py-2">Assigned products</th>
            <th className="px-4 py-2 text-right">Physical cores</th>
            <th className="px-4 py-2 text-right">Licenses required</th>
          </tr>
        </thead>
        <tbody>
          {hosts.map((host) => (
            <tr key={host.id} className="border-t border-separator">
              <td className="px-4 py-2">
                <Link className="text-link hover:underline" to={`/hosts/${host.id}`}>
                  {host.hostname}
                </Link>
              </td>
              <td className="px-4 py-2">{formatHostEnvironment(host.environment)}</td>
              <td className="px-4 py-2">{formatHostLicenseType(host.license_type)}</td>
              <td className="max-w-md px-4 py-2">
                {host.assigned_products.length === 0 ? (
                  <span className="text-muted">None</span>
                ) : (
                  host.assigned_products.join(" · ")
                )}
              </td>
              <td className="px-4 py-2 text-right tabular-nums">
                {host.physical_cores != null ? (
                  host.physical_cores
                ) : (
                  <span className="text-muted">—</span>
                )}
              </td>
              <td className="px-4 py-2 text-right tabular-nums">
                {host.licenses_required_label ?? "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function Reports() {
  const [shortfallsOnly, setShortfallsOnly] = useState(false);
  const [exporting, setExporting] = useState(false);

  const { data, isLoading, error } = useQuery({
    queryKey: ["report", shortfallsOnly],
    queryFn: () => api.getFullReport({ shortfallsOnly }),
  });

  const generatedAt = useMemo(() => {
    if (!data) {
      return null;
    }
    return new Date(data.generated_at).toLocaleString();
  }, [data]);

  async function handleExport(format: "csv" | "pdf") {
    setExporting(true);
    try {
      await api.downloadFullReport({ format, shortfallsOnly });
    } finally {
      setExporting(false);
    }
  }

  if (isLoading) {
    return <TablePageSkeleton />;
  }
  if (error || !data) {
    return <ErrorAlert title="Report unavailable" message="Failed to load the license report." />;
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold">License Report</h2>
          <p className="mt-1 text-sm text-muted">
            Contracts, purchased entitlements, host usage, and compliance. Generated {generatedAt}.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            size="sm"
            variant={shortfallsOnly ? "primary" : "secondary"}
            onPress={() => setShortfallsOnly((current) => !current)}
          >
            {shortfallsOnly ? "Show all products" : "Shortfalls only"}
          </Button>
          <Button
            size="sm"
            variant="secondary"
            onPress={() => void handleExport("csv")}
            isDisabled={exporting}
          >
            {exporting ? "Exporting…" : "Export CSV"}
          </Button>
          <Button
            size="sm"
            variant="secondary"
            onPress={() => void handleExport("pdf")}
            isDisabled={exporting}
          >
            {exporting ? "Exporting…" : "Export PDF"}
          </Button>
        </div>
      </div>

      <section className="space-y-3">
        <h3 className="text-lg font-medium">Summary</h3>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Card className="p-4">
            <p className="text-sm text-muted">Agreements</p>
            <p className="mt-2 text-3xl font-semibold tabular-nums">{data.summary.agreement_count}</p>
          </Card>
          <Card className="p-4">
            <p className="text-sm text-muted">Products</p>
            <p className="mt-2 text-3xl font-semibold tabular-nums">{data.summary.product_count}</p>
          </Card>
          <Card className="p-4">
            <p className="text-sm text-muted">Hosts</p>
            <p className="mt-2 text-3xl font-semibold tabular-nums">{data.summary.host_count}</p>
          </Card>
          <Card className="p-4">
            <p className="text-sm text-muted">Physical cores</p>
            <p className="mt-2 text-3xl font-semibold tabular-nums">
              {data.summary.total_physical_cores}
            </p>
          </Card>
        </div>
      </section>

      <ReportCharts productCompliance={data.product_compliance} />

      <section className="space-y-3">
        <h3 className="text-lg font-medium">Contracts and entitlements</h3>
        <p className="text-sm text-muted">All CSI agreements with purchased product entitlements.</p>
        <AgreementsTable agreements={data.agreements} />
      </section>

      <section className="space-y-3">
        <h3 className="text-lg font-medium">Host usage</h3>
        <p className="text-sm text-muted">
          Server inventory with assigned products and calculated license requirements.
        </p>
        <HostsTable hosts={data.hosts} />
      </section>

      <section className="space-y-3">
        <h3 className="text-lg font-medium">Product compliance</h3>
        <p className="text-sm text-muted">
          Pooled license inventory compared to in-use counts across all hosts.
        </p>
        <ComplianceTable rows={data.product_compliance} />
      </section>
    </div>
  );
}
