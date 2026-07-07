import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Button, Card, toast } from "@heroui/react";
import { FormField } from "../components/FormField";
import { ErrorAlert } from "../components/ErrorAlert";
import { TablePageSkeleton } from "../components/PageSkeleton";
import { useState } from "react";
import { api } from "../api/client";
import { formatLicenseMetric } from "../lib/licenseMetrics";

export function AgreementsList() {
  const queryClient = useQueryClient();
  const [csi, setCsi] = useState("");
  const [customerName, setCustomerName] = useState("");

  const { data, isLoading, error } = useQuery({
    queryKey: ["agreements"],
    queryFn: api.listAgreements,
  });

  const createMutation = useMutation({
    mutationFn: () =>
      api.createAgreement({
        csi,
        customer_name: customerName,
        status: "active",
      }),
    onSuccess: () => {
      setCsi("");
      setCustomerName("");
      void queryClient.invalidateQueries({ queryKey: ["agreements"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success("Agreement created");
    },
    onError: () => {
      toast.danger("Failed to create agreement.");
    },
  });

  if (isLoading) {
    return <TablePageSkeleton />;
  }
  if (error) {
    return <ErrorAlert title="Agreements unavailable" message="Failed to load agreements." />;
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold">License Agreements</h2>

      <Card className="space-y-3 p-4">
        <h3 className="font-medium">New agreement</h3>
        <div className="grid gap-3 sm:grid-cols-2">
          <FormField label="CSI" value={csi} onChange={(e) => setCsi(e.target.value)} />
          <FormField
            label="Customer name"
            value={customerName}
            onChange={(e) => setCustomerName(e.target.value)}
          />
        </div>
        <Button
          onPress={() => createMutation.mutate()}
          isDisabled={!csi || !customerName || createMutation.isPending}
        >
          Create agreement
        </Button>
      </Card>

      <div className="overflow-hidden rounded-lg border border-border bg-surface">
        <table className="min-w-full text-sm">
          <thead className="bg-default text-left">
            <tr>
              <th className="px-4 py-2">CSI</th>
              <th className="px-4 py-2">Customer</th>
              <th className="px-4 py-2">Products &amp; license counts</th>
              <th className="px-4 py-2">Renewal</th>
              <th className="px-4 py-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {data?.map((row) => (
              <tr key={row.id} className="border-t border-separator">
                <td className="px-4 py-2">
                  <Link className="text-link hover:underline" to={`/agreements/${row.id}`}>
                    {row.csi}
                  </Link>
                  <p className="text-xs text-muted">
                    {row.product_count} product{row.product_count === 1 ? "" : "s"}
                  </p>
                </td>
                <td className="px-4 py-2">{row.customer_name}</td>
                <td className="px-4 py-2">
                  {row.products.length === 0 ? (
                    <span className="text-muted text-xs">No products</span>
                  ) : (
                    <div className="flex flex-col gap-1 text-xs">
                      {row.products.map((product, i) => (
                        <div key={i} className="whitespace-normal leading-tight">
                          <span className="font-medium text-foreground">{product.product_name}</span>:{" "}
                          <span className="tabular-nums text-muted">{product.quantity} {formatLicenseMetric(product.metric)}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </td>
                <td className="px-4 py-2">{row.renewal_date ?? "—"}</td>
                <td className="px-4 py-2">{row.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
