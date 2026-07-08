import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button, Card, toast } from "@heroui/react";
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api, type CatalogProduct, type CatalogProductInput } from "../api/client";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { ErrorAlert } from "../components/ErrorAlert";
import { FormField } from "../components/FormField";
import { TablePageSkeleton } from "../components/PageSkeleton";
import { SelectField } from "../components/SelectField";
import { formatCatalogLabel, formatCatalogPrices } from "../lib/catalog";

const DEFAULT_PRICE_LIST_ID = "technology-price-list-070617";

interface ProductFormState {
  price_list_id: string;
  category: string;
  product_name: string;
  option_name: string;
  list_price_nup_usd: string;
  list_price_nup_support_usd: string;
  list_price_processor_usd: string;
  list_price_processor_support_usd: string;
  supports_nup: boolean;
  supports_processor: boolean;
}

const emptyForm = (): ProductFormState => ({
  price_list_id: DEFAULT_PRICE_LIST_ID,
  category: "",
  product_name: "",
  option_name: "",
  list_price_nup_usd: "",
  list_price_nup_support_usd: "",
  list_price_processor_usd: "",
  list_price_processor_support_usd: "",
  supports_nup: false,
  supports_processor: false,
});

function parseOptionalNumber(value: string): number | null {
  const trimmed = value.trim();
  if (!trimmed) {
    return null;
  }
  const parsed = Number(trimmed);
  return Number.isFinite(parsed) ? parsed : null;
}

function formToPayload(form: ProductFormState): CatalogProductInput {
  return {
    price_list_id: form.price_list_id.trim(),
    category: form.category.trim(),
    product_name: form.product_name.trim(),
    option_name: form.option_name.trim() || null,
    list_price_nup_usd: parseOptionalNumber(form.list_price_nup_usd),
    list_price_nup_support_usd: parseOptionalNumber(form.list_price_nup_support_usd),
    list_price_processor_usd: parseOptionalNumber(form.list_price_processor_usd),
    list_price_processor_support_usd: parseOptionalNumber(form.list_price_processor_support_usd),
    supports_nup: form.supports_nup,
    supports_processor: form.supports_processor,
  };
}

function productToForm(product: CatalogProduct): ProductFormState {
  return {
    price_list_id: product.price_list_id,
    category: product.category,
    product_name: product.product_name,
    option_name: product.option_name ?? "",
    list_price_nup_usd:
      product.list_price_nup_usd != null ? String(product.list_price_nup_usd) : "",
    list_price_nup_support_usd:
      product.list_price_nup_support_usd != null
        ? String(product.list_price_nup_support_usd)
        : "",
    list_price_processor_usd:
      product.list_price_processor_usd != null ? String(product.list_price_processor_usd) : "",
    list_price_processor_support_usd:
      product.list_price_processor_support_usd != null
        ? String(product.list_price_processor_support_usd)
        : "",
    supports_nup: product.supports_nup,
    supports_processor: product.supports_processor,
  };
}

function ProductForm({
  title,
  form,
  setForm,
  onSubmit,
  onCancel,
  isPending,
  submitLabel,
  categories,
}: {
  title: string;
  form: ProductFormState;
  setForm: React.Dispatch<React.SetStateAction<ProductFormState>>;
  onSubmit: () => void;
  onCancel?: () => void;
  isPending: boolean;
  submitLabel: string;
  categories: string[];
}) {
  const canSubmit = Boolean(form.category.trim() && form.product_name.trim() && form.price_list_id.trim());

  const formCategoryOptions = [
    { value: "", label: "Select category..." },
    ...categories.map((name) => ({ value: name, label: name })),
  ];

  return (
    <Card className="space-y-3 p-4">
      <h3 className="font-medium">{title}</h3>
      <div className="grid gap-3 sm:grid-cols-2">
        <FormField
          label="Product name"
          value={form.product_name}
          onChange={(e) => setForm((current) => ({ ...current, product_name: e.target.value }))}
          placeholder="e.g., Oracle Database Enterprise Edition"
        />
        <SelectField
          label="Category"
          value={form.category}
          onChange={(e) => setForm((current) => ({ ...current, category: e.target.value }))}
          options={formCategoryOptions}
        />
        <FormField
          label="Option name"
          value={form.option_name}
          onChange={(e) => setForm((current) => ({ ...current, option_name: e.target.value }))}
          placeholder="e.g., Diagnostics Pack"
        />
        <FormField
          label="Price list id"
          value={form.price_list_id}
          onChange={(e) => setForm((current) => ({ ...current, price_list_id: e.target.value }))}
          placeholder="e.g., technology-price-list-070617"
        />
        <FormField
          label="NUP list price (USD)"
          type="number"
          min="0"
          step="0.01"
          value={form.list_price_nup_usd}
          onChange={(e) =>
            setForm((current) => ({ ...current, list_price_nup_usd: e.target.value }))
          }
          placeholder="e.g., 950.00"
        />
        <FormField
          label="NUP support price (USD)"
          type="number"
          min="0"
          step="0.01"
          value={form.list_price_nup_support_usd}
          onChange={(e) =>
            setForm((current) => ({ ...current, list_price_nup_support_usd: e.target.value }))
          }
          placeholder="e.g., 209.00"
        />
        <FormField
          label="Processor list price (USD)"
          type="number"
          min="0"
          step="0.01"
          value={form.list_price_processor_usd}
          onChange={(e) =>
            setForm((current) => ({ ...current, list_price_processor_usd: e.target.value }))
          }
          placeholder="e.g., 47500.00"
        />
        <FormField
          label="Processor support price (USD)"
          type="number"
          min="0"
          step="0.01"
          value={form.list_price_processor_support_usd}
          onChange={(e) =>
            setForm((current) => ({
              ...current,
              list_price_processor_support_usd: e.target.value,
            }))
          }
          placeholder="e.g., 10450.00"
        />
      </div>
      <div className="flex flex-wrap gap-4 text-sm">
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={form.supports_nup}
            onChange={(e) =>
              setForm((current) => ({ ...current, supports_nup: e.target.checked }))
            }
          />
          Supports NUP licensing
        </label>
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={form.supports_processor}
            onChange={(e) =>
              setForm((current) => ({ ...current, supports_processor: e.target.checked }))
            }
          />
          Supports processor licensing
        </label>
      </div>
      <div className="flex gap-2">
        <Button onPress={onSubmit} isDisabled={!canSubmit || isPending}>
          {submitLabel}
        </Button>
        {onCancel ? (
          <Button variant="secondary" onPress={onCancel} isDisabled={isPending}>
            Cancel
          </Button>
        ) : null}
      </div>
    </Card>
  );
}

export function CatalogProducts() {
  const queryClient = useQueryClient();
  const [searchParams, setSearchParams] = useSearchParams();
  const search = searchParams.get("search") || "";
  const category = searchParams.get("category") || "";
  const [form, setForm] = useState<ProductFormState>(emptyForm);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<CatalogProduct | null>(null);

  const setSearch = (val: string) => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (val) {
        next.set("search", val);
      } else {
        next.delete("search");
      }
      return next;
    }, { replace: true });
  };

  const setCategory = (val: string) => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (val) {
        next.set("category", val);
      } else {
        next.delete("category");
      }
      return next;
    }, { replace: true });
  };

  const { data: categories = [] } = useQuery({
    queryKey: ["catalog-categories"],
    queryFn: api.listCatalogCategories,
  });

  const { data, isLoading, error } = useQuery({
    queryKey: ["catalog-products", search, category],
    queryFn: () =>
      api.listCatalogProducts({
        search: search || undefined,
        category: category || undefined,
        limit: 500,
      }),
  });

  const invalidateCatalog = () => {
    void queryClient.invalidateQueries({ queryKey: ["catalog-products"] });
    void queryClient.invalidateQueries({ queryKey: ["catalog-categories"] });
  };

  const createMutation = useMutation({
    mutationFn: () => api.createCatalogProduct(formToPayload(form)),
    onSuccess: () => {
      setForm(emptyForm());
      invalidateCatalog();
      toast.success("Catalog product created");
    },
    onError: () => {
      toast.danger("Failed to create catalog product.");
    },
  });

  const updateMutation = useMutation({
    mutationFn: () => {
      if (!editingId) {
        throw new Error("No product selected for update");
      }
      return api.updateCatalogProduct(editingId, formToPayload(form));
    },
    onSuccess: () => {
      setEditingId(null);
      setForm(emptyForm());
      invalidateCatalog();
      toast.success("Catalog product updated");
    },
    onError: () => {
      toast.danger("Failed to update catalog product.");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (productId: string) => api.deleteCatalogProduct(productId),
    onSuccess: () => {
      setDeleteTarget(null);
      invalidateCatalog();
      toast.success("Catalog product deleted");
    },
    onError: () => {
      toast.danger("Failed to delete catalog product.");
    },
  });

  useEffect(() => {
    if (editingId && data) {
      const product = data.find((row) => row.id === editingId);
      if (product) {
        setForm(productToForm(product));
      }
    } else {
      setForm(emptyForm());
    }
  }, [editingId, data]);

  if (isLoading) {
    return <TablePageSkeleton />;
  }
  if (error) {
    return <ErrorAlert title="Catalog unavailable" message="Failed to load catalog products." />;
  }

  const categoryOptions = [
    { value: "", label: "All categories" },
    ...categories.map((name) => ({ value: name, label: name })),
  ];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold">Oracle Products</h2>
        <p className="mt-1 text-sm text-muted">
          Manage the Oracle technology price list used when adding entitlements to agreements.
        </p>
      </div>

      <ProductForm
        title={editingId ? `Edit product: ${form.product_name || "Untitled"}` : "New product"}
        form={form}
        setForm={setForm}
        onSubmit={() => {
          if (editingId) {
            updateMutation.mutate();
          } else {
            createMutation.mutate();
          }
        }}
        onCancel={
          editingId
            ? () => {
                setEditingId(null);
                setForm(emptyForm());
              }
            : undefined
        }
        isPending={editingId ? updateMutation.isPending : createMutation.isPending}
        submitLabel={editingId ? "Save changes" : "Create product"}
        categories={categories}
      />

      <Card className="space-y-3 p-4">
        <h3 className="font-medium">Search</h3>
        <div className="grid gap-3 sm:grid-cols-2">
          <FormField
            label="Product search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Database Enterprise"
          />
          <SelectField
            label="Category"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            options={categoryOptions}
          />
        </div>
      </Card>

      <div className="overflow-hidden rounded-lg border border-border bg-surface">
        <table className="min-w-full text-sm">
          <thead className="bg-default text-left">
            <tr>
              <th className="px-4 py-2">Product</th>
              <th className="px-4 py-2">Category</th>
              <th className="px-4 py-2">List prices</th>
              <th className="px-4 py-2">Metrics</th>
              <th className="px-4 py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {data?.map((product) => (
              <tr key={product.id} className="border-t border-separator">
                <td className="px-4 py-2">
                  <p className="font-medium">{formatCatalogLabel(product)}</p>
                  <p className="text-xs text-muted">{product.price_list_id}</p>
                </td>
                <td className="px-4 py-2">{product.category}</td>
                <td className="px-4 py-2">{formatCatalogPrices(product) || "—"}</td>
                <td className="px-4 py-2">
                  {[product.supports_processor ? "Processor" : null, product.supports_nup ? "NUP" : null]
                    .filter(Boolean)
                    .join(", ") || "—"}
                </td>
                <td className="px-4 py-2">
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="secondary"
                      onPress={() => setEditingId(product.id)}
                    >
                      Edit
                    </Button>
                    <Button
                      size="sm"
                      variant="danger"
                      onPress={() => setDeleteTarget(product)}
                      isDisabled={deleteMutation.isPending}
                    >
                      Delete
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <ConfirmDialog
        title="Delete catalog product"
        message={
          deleteTarget
            ? `Delete "${formatCatalogLabel(deleteTarget)}" from the catalog? This cannot be undone.`
            : ""
        }
        confirmLabel="Delete product"
        variant="danger"
        isOpen={deleteTarget != null}
        isPending={deleteMutation.isPending}
        onConfirm={() => {
          if (deleteTarget) {
            deleteMutation.mutate(deleteTarget.id);
          }
        }}
        onClose={() => setDeleteTarget(null)}
      />
    </div>
  );
}
