import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useParams } from "react-router-dom";
import { Button, Card, toast } from "@heroui/react";
import { CatalogProductField } from "../components/CatalogProductField";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { ErrorAlert } from "../components/ErrorAlert";
import { FormField } from "../components/FormField";
import { PageBreadcrumbs } from "../components/PageBreadcrumbs";
import { DetailPageSkeleton } from "../components/PageSkeleton";
import { SelectField } from "../components/SelectField";
import { useEffect, useState } from "react";
import {
  api,
  LICENSE_STATUS_OPTIONS,
  type CatalogProduct,
  type LicenseMetric,
  type LicenseStatus,
  type Product,
} from "../api/client";
import { formatCatalogLabel, formatCatalogPrices, DEFAULT_PRICE_LIST_ID } from "../lib/catalog";
import { formatLicenseMetric, LICENSE_METRIC_OPTIONS } from "../lib/licenseMetrics";

const emptyProductForm = {
  product_name: "",
  option_name: "",
  metric: "processor" as LicenseMetric,
  quantity: "1",
  notes: "",
};

function formatApiError(error: unknown, fallback: string): string {
  if (!(error instanceof Error)) {
    return fallback;
  }
  try {
    const body = JSON.parse(error.message) as { detail?: string };
    if (typeof body.detail === "string") {
      return body.detail;
    }
  } catch {
    // Response body was not JSON.
  }
  return error.message || fallback;
}

export function AgreementDetail() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [form, setForm] = useState(emptyProductForm);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingAgreement, setEditingAgreement] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  const [agreementForm, setAgreementForm] = useState({
    customer_name: "",
    support_level: "",
    start_date: "",
    renewal_date: "",
    status: "active" as LicenseStatus,
    notes: "",
  });

  const [catalogInput, setCatalogInput] = useState("");
  const [catalogSearch, setCatalogSearch] = useState("");
  const [selectedCatalogId, setSelectedCatalogId] = useState("");

  useEffect(() => {
    const timer = window.setTimeout(() => setCatalogSearch(catalogInput), 300);
    return () => window.clearTimeout(timer);
  }, [catalogInput]);

  const { data, isLoading, error } = useQuery({
    queryKey: ["agreement", id],
    queryFn: () => api.getAgreement(id),
    enabled: Boolean(id),
  });

  useEffect(() => {
    if (data) {
      setAgreementForm({
        customer_name: data.customer_name,
        support_level: data.support_level ?? "",
        start_date: data.start_date ?? "",
        renewal_date: data.renewal_date ?? "",
        status: data.status,
        notes: data.notes ?? "",
      });
    }
  }, [data]);

  const { data: compliance } = useQuery({
    queryKey: ["agreement-compliance", id],
    queryFn: () => api.getAgreementCompliance(id),
    enabled: Boolean(id),
  });

  const { data: catalogProducts } = useQuery({
    queryKey: ["catalog-products", catalogSearch],
    queryFn: () =>
      api.listCatalogProducts({
        search: catalogSearch || undefined,
        limit: 200,
      }),
  });

  const selectedCatalogProduct =
    catalogProducts?.find((product) => product.id === selectedCatalogId) ?? null;

  const applyCatalogProduct = (product: CatalogProduct) => {
    setSelectedCatalogId(product.id);
    setForm((current) => ({
      ...current,
      product_name: product.product_name,
      option_name: product.option_name ?? "",
      metric: product.supports_processor
        ? "processor"
        : product.supports_nup
          ? "named_user_plus"
          : current.metric,
    }));
  };

  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: ["agreement", id] });
    void queryClient.invalidateQueries({ queryKey: ["agreement-compliance", id] });
    void queryClient.invalidateQueries({ queryKey: ["agreements"] });
    void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
  };

  const saveAgreement = useMutation({
    mutationFn: () =>
      api.updateAgreement(id, {
        customer_name: agreementForm.customer_name,
        support_level: agreementForm.support_level || null,
        start_date: agreementForm.start_date || null,
        renewal_date: agreementForm.renewal_date || null,
        status: agreementForm.status,
        notes: agreementForm.notes || null,
      }),
    onSuccess: () => {
      setEditingAgreement(false);
      invalidate();
      toast.success("Agreement updated");
    },
    onError: (mutationError) => {
      toast.danger(formatApiError(mutationError, "Failed to update agreement."));
    },
  });

  const deleteAgreement = useMutation({
    mutationFn: () => api.deleteAgreement(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["agreements"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success("Agreement deleted");
      void navigate("/agreements");
    },
    onError: (mutationError) => {
      toast.danger(formatApiError(mutationError, "Failed to delete agreement."));
    },
  });

  const createCatalogProduct = useMutation({
    mutationFn: (productName: string) =>
      api.createCatalogProduct({
        price_list_id: DEFAULT_PRICE_LIST_ID,
        category: "Custom",
        product_name: productName,
      }),
    onSuccess: (product) => {
      applyCatalogProduct(product);
      setCatalogInput(formatCatalogLabel(product));
      void queryClient.invalidateQueries({ queryKey: ["catalog-products"] });
      toast.success("Product added to catalog");
    },
    onError: (mutationError) => {
      toast.danger(formatApiError(mutationError, "Failed to add product to catalog."));
    },
  });

  const saveProduct = useMutation({
    mutationFn: () => {
      const payload = {
        product_name: form.product_name,
        option_name: form.option_name || null,
        metric: form.metric,
        quantity: Number(form.quantity),
        notes: form.notes || null,
      };
      if (editingId) {
        return api.updateProduct(id, editingId, payload);
      }
      return api.createProduct(id, payload);
    },
    onSuccess: () => {
      setForm(emptyProductForm);
      setEditingId(null);
      setSelectedCatalogId("");
      setCatalogInput("");
      invalidate();
      toast.success(editingId ? "Entitlement updated" : "Entitlement added");
    },
    onError: (mutationError) => {
      toast.danger(formatApiError(mutationError, "Failed to save entitlement."));
    },
  });

  const deleteProduct = useMutation({
    mutationFn: (productId: string) => api.deleteProduct(id, productId),
    onSuccess: () => {
      if (editingId) {
        setEditingId(null);
        setForm(emptyProductForm);
      }
      invalidate();
      toast.success("Entitlement removed");
    },
    onError: (mutationError) => {
      toast.danger(formatApiError(mutationError, "Failed to remove entitlement."));
    },
  });

  const startEdit = (product: Product) => {
    setEditingId(product.id);
    setCatalogInput(product.product_name);
    setSelectedCatalogId("");
    setForm({
      product_name: product.product_name,
      option_name: product.option_name ?? "",
      metric: product.metric,
      quantity: String(product.quantity),
      notes: product.notes ?? "",
    });
  };

  const cancelEdit = () => {
    setEditingId(null);
    setForm(emptyProductForm);
    setSelectedCatalogId("");
    setCatalogInput("");
  };

  const cancelAgreementEdit = () => {
    if (data) {
      setAgreementForm({
        customer_name: data.customer_name,
        support_level: data.support_level ?? "",
        start_date: data.start_date ?? "",
        renewal_date: data.renewal_date ?? "",
        status: data.status,
        notes: data.notes ?? "",
      });
    }
    setEditingAgreement(false);
  };

  if (isLoading) {
    return <DetailPageSkeleton />;
  }
  if (error || !data) {
    return <ErrorAlert title="Agreement not found" message="This agreement could not be loaded." />;
  }

  return (
    <div className="space-y-6">
      <PageBreadcrumbs
        items={[
          { label: "Agreements", to: "/agreements" },
          { label: data.csi },
        ]}
      />

      <Card className="space-y-3 p-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-2xl font-semibold">{data.csi}</h2>
            {!editingAgreement ? (
              <>
                <p>{data.customer_name}</p>
                <p className="text-sm text-muted">
                  Renewal: {data.renewal_date ?? "—"} · Status: {data.status}
                  {data.support_level ? ` · Support: ${data.support_level}` : ""}
                </p>
                {data.notes ? <p className="text-sm text-muted">Notes: {data.notes}</p> : null}
                <p className="text-sm text-muted">
                  {data.products.length} product{data.products.length === 1 ? "" : "s"} tracked
                </p>
              </>
            ) : null}
          </div>
          <div className="flex flex-wrap gap-2">
            {editingAgreement ? null : (
              <>
                <Button size="sm" variant="secondary" onPress={() => setEditingAgreement(true)}>
                  Edit agreement
                </Button>
                <Button size="sm" variant="danger" onPress={() => setShowDeleteDialog(true)}>
                  Delete
                </Button>
              </>
            )}
          </div>
        </div>

        {editingAgreement ? (
          <div className="space-y-3 border-t border-border pt-3">
            <div className="grid gap-3 sm:grid-cols-2">
              <FormField
                label="Customer name"
                value={agreementForm.customer_name}
                onChange={(e) =>
                  setAgreementForm((current) => ({ ...current, customer_name: e.target.value }))
                }
              />
              <FormField
                label="Support level"
                value={agreementForm.support_level}
                onChange={(e) =>
                  setAgreementForm((current) => ({ ...current, support_level: e.target.value }))
                }
                placeholder="e.g. Premier"
              />
              <FormField
                label="Start date"
                type="date"
                value={agreementForm.start_date}
                onChange={(e) =>
                  setAgreementForm((current) => ({ ...current, start_date: e.target.value }))
                }
              />
              <FormField
                label="Renewal date"
                type="date"
                value={agreementForm.renewal_date}
                onChange={(e) =>
                  setAgreementForm((current) => ({ ...current, renewal_date: e.target.value }))
                }
              />
              <SelectField
                label="Status"
                value={agreementForm.status}
                onChange={(e) =>
                  setAgreementForm((current) => ({
                    ...current,
                    status: e.target.value as LicenseStatus,
                  }))
                }
                options={LICENSE_STATUS_OPTIONS.map(({ value, label }) => ({ value, label }))}
              />
              <FormField
                label="Notes"
                className="sm:col-span-2"
                value={agreementForm.notes}
                onChange={(e) =>
                  setAgreementForm((current) => ({ ...current, notes: e.target.value }))
                }
              />
            </div>
            <div className="flex gap-2">
              <Button
                onPress={() => saveAgreement.mutate()}
                isDisabled={!agreementForm.customer_name || saveAgreement.isPending}
              >
                Save agreement
              </Button>
              <Button variant="tertiary" onPress={cancelAgreementEdit}>
                Cancel
              </Button>
            </div>
          </div>
        ) : null}
      </Card>

      {compliance && (
        <Card className="space-y-3 p-4">
          <h3 className="font-medium">Purchased on this CSI</h3>
          <p className="text-sm text-muted">
            Server coverage is tracked organization-wide on the dashboard. Multiple CSIs can
            combine to license the same servers.
          </p>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-lg border border-border p-3">
              <p className="text-sm font-medium">Processor (core-based)</p>
              <p className="mt-1 text-sm text-muted">
                Purchased on this CSI: {compliance.processor_licenses_purchased}
              </p>
            </div>
            <div className="rounded-lg border border-border p-3">
              <p className="text-sm font-medium">Named User Plus (NUP)</p>
              <p className="mt-1 text-sm text-muted">
                Purchased on this CSI: {compliance.named_user_plus_purchased}
              </p>
              <p className="mt-2 text-sm text-muted">
                Named-user usage tracking is not automated yet.
              </p>
            </div>
          </div>
        </Card>
      )}

      <Card className="space-y-3 p-4">
        <h3 className="font-medium">
          {editingId ? "Edit product entitlement" : "Add product entitlement"}
        </h3>
        <p className="text-sm text-muted">
          Choose <strong>Processor (core-based)</strong> for CPU licensing or{" "}
          <strong>Named User Plus</strong> for per-user licensing. Processor requirements are
          calculated from assigned server CPU inventory on the dashboard.
        </p>
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="sm:col-span-2">
            <CatalogProductField
              products={catalogProducts ?? []}
              selectedId={selectedCatalogId}
              inputValue={catalogInput}
              onInputChange={(value) => {
                setCatalogInput(value);
                if (selectedCatalogId) {
                  setSelectedCatalogId("");
                  setForm((current) => ({ ...current, option_name: "" }));
                }
              }}
              onProductNameChange={(productName) => {
                setForm((current) => ({ ...current, product_name: productName }));
              }}
              onProductSelect={(product) => {
                if (product) {
                  applyCatalogProduct(product);
                  setCatalogInput(formatCatalogLabel(product));
                } else {
                  setSelectedCatalogId("");
                  setForm((current) => ({ ...current, option_name: "" }));
                }
              }}
              onCreateProduct={(productName) => createCatalogProduct.mutate(productName)}
              isCreatingProduct={createCatalogProduct.isPending}
            />
          </div>
          <FormField
            label="Option / edition"
            value={form.option_name}
            disabled
            placeholder="Obtained from product selection"
          />
          <SelectField
            label="License type"
            value={form.metric}
            onChange={(e) =>
              setForm((current) => ({ ...current, metric: e.target.value as LicenseMetric }))
            }
            options={LICENSE_METRIC_OPTIONS.map(({ value, label }) => ({ value, label }))}
          />
          <FormField
            label="License count"
            type="number"
            min={0}
            value={form.quantity}
            onChange={(e) => setForm((current) => ({ ...current, quantity: e.target.value }))}
          />
          <FormField
            label="Notes"
            className="sm:col-span-2"
            value={form.notes}
            onChange={(e) => setForm((current) => ({ ...current, notes: e.target.value }))}
          />
        </div>
        {selectedCatalogProduct ? (
          <p className="text-sm text-muted">
            Oracle list prices (USD): {formatCatalogPrices(selectedCatalogProduct)}
          </p>
        ) : null}
        <div className="flex gap-2">
          <Button
            onPress={() => saveProduct.mutate()}
            isDisabled={!form.product_name.trim() || saveProduct.isPending}
          >
            {editingId ? "Save changes" : "Add product"}
          </Button>
          {editingId ? (
            <Button variant="tertiary" onPress={cancelEdit}>
              Cancel
            </Button>
          ) : null}
        </div>
      </Card>

      <div className="overflow-hidden rounded-lg border border-border bg-surface">
        <table className="min-w-full text-sm">
          <thead className="bg-default text-left">
            <tr>
              <th className="px-4 py-2">Product</th>
              <th className="px-4 py-2">Option</th>
              <th className="px-4 py-2">License type</th>
              <th className="px-4 py-2">Count</th>
              <th className="px-4 py-2">Notes</th>
              <th className="px-4 py-2" />
            </tr>
          </thead>
          <tbody>
            {data.products.length === 0 ? (
              <tr>
                <td className="px-4 py-6 text-muted" colSpan={6}>
                  No products yet. Add a product and license count above.
                </td>
              </tr>
            ) : (
              data.products.map((product) => (
                <tr key={product.id} className="border-t border-separator">
                  <td className="px-4 py-2">{product.product_name}</td>
                  <td className="px-4 py-2">{product.option_name ?? "—"}</td>
                  <td className="px-4 py-2">{formatLicenseMetric(product.metric)}</td>
                  <td className="px-4 py-2">{product.quantity}</td>
                  <td className="px-4 py-2">{product.notes ?? "—"}</td>
                  <td className="px-4 py-2 text-right">
                    <div className="flex justify-end gap-2">
                      <Button size="sm" variant="tertiary" onPress={() => startEdit(product)}>
                        Edit
                      </Button>
                      <Button
                        size="sm"
                        variant="tertiary"
                        onPress={() => deleteProduct.mutate(product.id)}
                      >
                        Delete
                      </Button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <ConfirmDialog
        title="Delete agreement"
        message={`Delete agreement ${data.csi}? This removes all entitlements and cannot be undone.`}
        confirmLabel="Delete agreement"
        variant="danger"
        isOpen={showDeleteDialog}
        isPending={deleteAgreement.isPending}
        onConfirm={() => deleteAgreement.mutate()}
        onClose={() => setShowDeleteDialog(false)}
      />
    </div>
  );
}
