import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { Button, Card, toast } from "@heroui/react";
import { CatalogProductField } from "../components/CatalogProductField";
import { ErrorAlert } from "../components/ErrorAlert";
import { FormField } from "../components/FormField";
import { PageBreadcrumbs } from "../components/PageBreadcrumbs";
import { DetailPageSkeleton } from "../components/PageSkeleton";
import {
  formatProcessorFamilyLabel,
  ProcessorFamilyField,
} from "../components/ProcessorFamilyField";
import { SelectField } from "../components/SelectField";
import { useEffect, useState } from "react";
import {
  api,
  formatHostLicenseType,
  HOST_ENVIRONMENT_OPTIONS,
  HOST_LICENSE_TYPE_OPTIONS,
  type CatalogProduct,
  type HostEnvironment,
  type HostLicenseType,
} from "../api/client";
import { DEFAULT_PRICE_LIST_ID, formatCatalogLabel } from "../lib/catalog";
import { formatProcessorLicenseCalc, calculateNamedUsersRequired } from "../lib/licenseMetrics";

const environmentOptions = [
  { value: "", label: "Select environment" },
  ...HOST_ENVIRONMENT_OPTIONS,
];

const licenseTypeOptions = [...HOST_LICENSE_TYPE_OPTIONS];

function assignmentKey(product: {
  product_name: string;
  option_name: string | null;
}): string {
  return `${product.product_name}|${product.option_name ?? ""}`;
}

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

export function HostDetail() {
  const { id = "" } = useParams();
  const queryClient = useQueryClient();

  const [cpuModel, setCpuModel] = useState("");
  const [coreFactorOverride, setCoreFactorOverride] = useState("");
  const [useCoreFactorOverride, setUseCoreFactorOverride] = useState(false);
  const [socketCount, setSocketCount] = useState("");
  const [coresPerSocket, setCoresPerSocket] = useState("");
  const [threadsPerCore, setThreadsPerCore] = useState("");
  const [environment, setEnvironment] = useState("");
  const [licenseType, setLicenseType] = useState<HostLicenseType>("cpu");
  const [assignProductName, setAssignProductName] = useState("");
  const [assignOptionName, setAssignOptionName] = useState("");
  const [catalogInput, setCatalogInput] = useState("");
  const [catalogSearch, setCatalogSearch] = useState("");
  const [selectedCatalogId, setSelectedCatalogId] = useState("");
  const [selectedFactorId, setSelectedFactorId] = useState("");
  const [processorFamilyInput, setProcessorFamilyInput] = useState("");

  const { data: host, isLoading, error } = useQuery({
    queryKey: ["host", id],
    queryFn: () => api.getHost(id),
    enabled: Boolean(id),
  });

  useEffect(() => {
    const timer = window.setTimeout(() => setCatalogSearch(catalogInput), 300);
    return () => window.clearTimeout(timer);
  }, [catalogInput]);

  const { data: catalogProducts } = useQuery({
    queryKey: ["catalog-products", catalogSearch],
    queryFn: () =>
      api.listCatalogProducts({
        search: catalogSearch || undefined,
        limit: 25,
      }),
  });

  const {
    data: cpuProfile,
    isError: cpuProfileMissing,
    isFetched: cpuProfileFetched,
  } = useQuery({
    queryKey: ["cpu-profile", id],
    queryFn: () => api.getCpuProfile(id),
    enabled: Boolean(id),
    retry: false,
  });

  const { data: cpuHistory } = useQuery({
    queryKey: ["cpu-history", id],
    queryFn: () => api.getCpuHistory(id),
    enabled: Boolean(id),
  });

  const { data: hostProducts = [] } = useQuery({
    queryKey: ["host-products", id],
    queryFn: () => api.listHostProducts(id),
    enabled: Boolean(id),
  });

  const { data: coreFactors = [] } = useQuery({
    queryKey: ["core-factors"],
    queryFn: api.listCoreFactors,
  });

  const trimmedCpuModel = cpuModel.trim();
  const { data: resolvedFactor } = useQuery({
    queryKey: ["core-factor-resolve", trimmedCpuModel],
    queryFn: () => api.resolveCoreFactor(trimmedCpuModel),
    enabled: Boolean(trimmedCpuModel) && !useCoreFactorOverride,
    retry: false,
  });

  useEffect(() => {
    if (host) {
      setEnvironment(host.environment ?? "");
      setLicenseType(host.license_type);
    }
  }, [host]);

  useEffect(() => {
    if (cpuProfile) {
      setCpuModel(cpuProfile.cpu_model ?? "");
      const isManualOverride =
        cpuProfile.core_factor != null && cpuProfile.core_factor_name == null;
      setUseCoreFactorOverride(isManualOverride);
      setCoreFactorOverride(
        isManualOverride && cpuProfile.core_factor != null
          ? String(cpuProfile.core_factor)
          : "",
      );
      setSelectedFactorId("");
      setProcessorFamilyInput("");
      setSocketCount(String(cpuProfile.socket_count));
      setCoresPerSocket(String(cpuProfile.cores_per_socket));
      setThreadsPerCore(String(cpuProfile.threads_per_core));
    }
  }, [cpuProfile]);

  const saveHostSettings = useMutation({
    mutationFn: () =>
      api.updateHost(id, {
        environment: (environment || null) as HostEnvironment | null,
        license_type: licenseType,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["host", id] });
      void queryClient.invalidateQueries({ queryKey: ["host-products", id] });
      void queryClient.invalidateQueries({ queryKey: ["hosts"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success("Host settings saved");
    },
    onError: (mutationError) => {
      toast.danger(formatApiError(mutationError, "Failed to save host settings."));
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

  const assignProduct = useMutation({
    mutationFn: (body: { product_name: string; option_name: string | null }) =>
      api.assignHostProduct(id, body),
    onSuccess: () => {
      setAssignProductName("");
      setAssignOptionName("");
      setSelectedCatalogId("");
      setCatalogInput("");
      void queryClient.invalidateQueries({ queryKey: ["host-products", id] });
      void queryClient.invalidateQueries({ queryKey: ["hosts"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success("Product assigned");
    },
    onError: (mutationError) => {
      toast.danger(formatApiError(mutationError, "Failed to assign product."));
    },
  });

  const unassignProduct = useMutation({
    mutationFn: (assignmentId: string) => api.unassignHostProduct(id, assignmentId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["host-products", id] });
      void queryClient.invalidateQueries({ queryKey: ["hosts"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success("Product removed");
    },
    onError: (mutationError) => {
      toast.danger(formatApiError(mutationError, "Failed to remove product."));
    },
  });

  const saveCpu = useMutation({
    mutationFn: () =>
      api.upsertCpuProfile(id, {
        cpu_model: cpuModel || null,
        core_factor:
          useCoreFactorOverride && coreFactorOverride
            ? Number(coreFactorOverride)
            : null,
        socket_count: Number(socketCount),
        cores_per_socket: Number(coresPerSocket),
        threads_per_core: Number(threadsPerCore),
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["cpu-profile", id] });
      void queryClient.invalidateQueries({ queryKey: ["cpu-history", id] });
      void queryClient.invalidateQueries({ queryKey: ["hosts"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success("CPU profile saved");
    },
    onError: (mutationError) => {
      toast.danger(
        formatApiError(
          mutationError,
          "Failed to save CPU profile. Check sockets, cores, and threads are valid numbers.",
        ),
      );
    },
  });

  const cpuFormComplete =
    Number(socketCount) >= 1 &&
    Number(coresPerSocket) >= 1 &&
    Number(threadsPerCore) >= 1 &&
    (!useCoreFactorOverride || Number(coreFactorOverride) > 0);

  const selectableFactors = coreFactors.filter((factor) => !factor.is_default);

  const effectiveFactor = useCoreFactorOverride
    ? coreFactorOverride
      ? {
          name: "Manual override",
          core_factor: Number(coreFactorOverride),
        }
      : null
    : resolvedFactor
      ? {
          name: resolvedFactor.name,
          core_factor: resolvedFactor.core_factor,
        }
      : null;

  const previewPhysicalCores =
    Number(socketCount) >= 1 && Number(coresPerSocket) >= 1
      ? Number(socketCount) * Number(coresPerSocket)
      : null;
  const previewLicensesRequired =
    previewPhysicalCores != null && effectiveFactor != null
      ? Math.ceil(previewPhysicalCores * effectiveFactor.core_factor)
      : null;

  const applyCatalogProduct = (product: CatalogProduct) => {
    setSelectedCatalogId(product.id);
    setAssignProductName(product.product_name);
    setAssignOptionName(product.option_name ?? "");
  };

  if (isLoading) {
    return <DetailPageSkeleton />;
  }
  if (error || !host) {
    return <ErrorAlert title="Host not found" message="This host could not be loaded." />;
  }

  const assignedKeys = new Set(hostProducts.map((product) => assignmentKey(product)));
  const normalizedAssignOption = assignOptionName.trim() || null;
  const trimmedAssignProductName = assignProductName.trim();
  const assignDuplicate =
    trimmedAssignProductName.length > 0 &&
    assignedKeys.has(assignmentKey({
      product_name: trimmedAssignProductName,
      option_name: normalizedAssignOption,
    }));
  const settingsDirty =
    environment !== (host.environment ?? "") || licenseType !== host.license_type;
  const saveHostError = saveHostSettings.isError
    ? formatApiError(saveHostSettings.error, "Failed to save host settings.")
    : null;
  const assignProductError = assignProduct.isError
    ? formatApiError(assignProduct.error, "Failed to assign product.")
    : assignDuplicate
      ? "This product is already assigned to the host."
      : null;

  const previewNamedUsersRequired = calculateNamedUsersRequired(previewLicensesRequired);
  const displayedNamedUsersRequired =
    previewNamedUsersRequired ?? host.named_users_required ?? null;

  return (
    <div className="space-y-6">
      <PageBreadcrumbs
        items={[
          { label: "Hosts", to: "/hosts" },
          { label: host.hostname },
        ]}
      />

      <Card className="space-y-3 p-4">
        <h2 className="text-2xl font-semibold">{host.hostname}</h2>
        <p className="text-sm text-muted">{host.os_name ?? "Unknown OS"}</p>
        <p className="text-sm text-muted">
          This server uses {formatHostLicenseType(host.license_type)} licensing for all assigned
          products.
        </p>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <div className="sm:w-64">
            <SelectField
              label="Environment"
              value={environment}
              onChange={(e) => setEnvironment(e.target.value)}
              options={environmentOptions}
            />
          </div>
          <div className="sm:w-64">
            <SelectField
              label="License type"
              value={licenseType}
              onChange={(e) => {
                setLicenseType(e.target.value as HostLicenseType);
              }}
              options={licenseTypeOptions}
            />
          </div>
          {licenseType === "nup" ? (
            <div className="sm:w-56">
              <p className="mb-1 text-sm font-medium text-foreground">Named users required</p>
              <p className="text-sm text-foreground">
                {displayedNamedUsersRequired != null
                  ? displayedNamedUsersRequired
                  : "Save CPU profile to calculate"}
              </p>
              <p className="mt-1 text-xs text-muted">25 per licensable core (read-only)</p>
            </div>
          ) : null}
          <Button
            onPress={() => saveHostSettings.mutate()}
            isDisabled={saveHostSettings.isPending || !settingsDirty}
          >
            Save settings
          </Button>
        </div>
        {saveHostError ? <p className="text-sm text-danger">{saveHostError}</p> : null}
      </Card>

      <Card className="space-y-3 p-4">
        <h3 className="font-medium">Assigned products</h3>
        <p className="text-sm text-muted">
          Products are licensed as {formatHostLicenseType(host.license_type)} on this server.
          Record what runs here even when you have not purchased matching licenses yet; shortfalls
          appear on the dashboard.
        </p>
        <div className="max-w-xl">
          <CatalogProductField
            products={catalogProducts ?? []}
            selectedId={selectedCatalogId}
            inputValue={catalogInput}
            onInputChange={(value) => {
              setCatalogInput(value);
              if (selectedCatalogId) {
                setSelectedCatalogId("");
                setAssignOptionName("");
              }
            }}
            onProductNameChange={setAssignProductName}
            onProductSelect={(product) => {
              if (product) {
                applyCatalogProduct(product);
                setCatalogInput(formatCatalogLabel(product));
              } else {
                setSelectedCatalogId("");
                setAssignOptionName("");
              }
            }}
            onCreateProduct={(productName) => createCatalogProduct.mutate(productName)}
            isCreatingProduct={createCatalogProduct.isPending}
          />
        </div>
        <div className="flex gap-2">
          <Button
            onPress={() => {
              if (!trimmedAssignProductName || assignDuplicate) {
                return;
              }
              assignProduct.mutate({
                product_name: trimmedAssignProductName,
                option_name: normalizedAssignOption,
              });
            }}
            isDisabled={
              !trimmedAssignProductName || assignDuplicate || assignProduct.isPending
            }
          >
            Assign product
          </Button>
        </div>
        {assignProductError ? <p className="text-sm text-danger">{assignProductError}</p> : null}
        {hostProducts.length === 0 ? (
          <p className="text-sm text-muted">No products assigned to this server yet.</p>
        ) : (
          <div className="overflow-hidden rounded-lg border border-border">
            <table className="min-w-full text-sm">
              <thead className="bg-default text-left">
                <tr>
                  <th className="px-4 py-2">Product</th>
                  <th className="px-4 py-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                {hostProducts.map((product) => (
                  <tr key={product.id} className="border-t border-separator">
                    <td className="px-4 py-2">
                      {product.product_name}
                      {product.option_name ? ` — ${product.option_name}` : ""}
                    </td>
                    <td className="px-4 py-2">
                      <Button
                        size="sm"
                        variant="tertiary"
                        onPress={() => unassignProduct.mutate(product.id)}
                        isDisabled={unassignProduct.isPending}
                      >
                        Remove
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <Card className="space-y-3 p-4">
        <h3 className="font-medium">CPU profile (manual entry)</h3>
        <p className="text-sm text-muted">
          Required for license calculations. Processor licenses and NUP minimums are calculated from
          physical cores multiplied by the Oracle core factor from the Processor Core Factor Table.
          Choose a processor family or type a CPU model to apply the matching multiplier
          automatically. Values appear on the hosts list only after you save.
        </p>
        {cpuProfileFetched && cpuProfileMissing && !cpuProfile ? (
          <p className="rounded-lg border border-warning bg-warning/10 px-3 py-2 text-sm text-warning">
            No CPU profile saved for this host yet. Enter sockets and cores, then click Save CPU
            profile.
          </p>
        ) : null}
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="sm:col-span-2">
            <ProcessorFamilyField
              label="Processor family"
              factors={selectableFactors}
              selectedId={selectedFactorId}
              inputValue={processorFamilyInput}
              onInputChange={(value) => {
                setProcessorFamilyInput(value);
                if (selectedFactorId) {
                  setSelectedFactorId("");
                }
              }}
              onFactorSelect={(factor) => {
                if (factor) {
                  setSelectedFactorId(factor.id);
                  setProcessorFamilyInput(formatProcessorFamilyLabel(factor));
                  setCpuModel(factor.name);
                  setUseCoreFactorOverride(false);
                  setCoreFactorOverride("");
                } else {
                  setSelectedFactorId("");
                }
              }}
            />
          </div>
          <FormField
            label="CPU model"
            value={cpuModel}
            onChange={(e) => {
              setCpuModel(e.target.value);
              setSelectedFactorId("");
              setProcessorFamilyInput("");
            }}
            placeholder="e.g. Intel(R) Xeon(R) Gold 6248"
          />
          <div className="space-y-2">
            <label className="flex items-center gap-2 text-sm text-foreground">
              <input
                type="checkbox"
                checked={useCoreFactorOverride}
                onChange={(e) => {
                  setUseCoreFactorOverride(e.target.checked);
                  if (!e.target.checked) {
                    setCoreFactorOverride("");
                  } else if (
                    !coreFactorOverride &&
                    effectiveFactor != null &&
                    !Number.isNaN(effectiveFactor.core_factor)
                  ) {
                    setCoreFactorOverride(String(effectiveFactor.core_factor));
                  }
                }}
              />
              Override core factor
            </label>
            {useCoreFactorOverride ? (
              <FormField
                label="Core factor override"
                type="number"
                step="0.01"
                value={coreFactorOverride}
                onChange={(e) => setCoreFactorOverride(e.target.value)}
                placeholder="e.g. 0.5"
              />
            ) : (
              <p className="text-sm text-muted">
                Applied factor:{" "}
                {effectiveFactor
                  ? `${effectiveFactor.name} (${effectiveFactor.core_factor})`
                  : trimmedCpuModel
                    ? "Resolving…"
                    : "Enter or select a CPU model"}
              </p>
            )}
          </div>
          <FormField
            label="Sockets"
            type="number"
            value={socketCount}
            onChange={(e) => setSocketCount(e.target.value)}
            placeholder="e.g. 2"
          />
          <FormField
            label="Cores per socket"
            type="number"
            value={coresPerSocket}
            onChange={(e) => setCoresPerSocket(e.target.value)}
            placeholder="e.g. 16"
          />
          <FormField
            label="Threads per core"
            type="number"
            value={threadsPerCore}
            onChange={(e) => setThreadsPerCore(e.target.value)}
            placeholder="e.g. 2"
          />
        </div>
        <div className="flex gap-3">
          <Button
            onPress={() => saveCpu.mutate()}
            isDisabled={!cpuFormComplete || saveCpu.isPending}
          >
            Save CPU profile
          </Button>
          <Button variant="tertiary" isDisabled>
            Collect via SSH (Phase 4)
          </Button>
        </div>
        {saveCpu.isError ? (
          <p className="text-sm text-danger">
            Failed to save CPU profile. Check sockets, cores, and threads are valid numbers.
          </p>
        ) : null}
        {effectiveFactor != null && (
          <div className="rounded-lg border border-border bg-default p-3 text-sm">
            <p className="font-medium">
              {licenseType === "cpu" ? "Processor license requirement" : "License requirement"}
            </p>
            <p className="text-muted">
              Matched factor: {effectiveFactor.name} ({effectiveFactor.core_factor})
            </p>
            {previewPhysicalCores != null && previewLicensesRequired != null ? (
              <>
                <p className="text-muted">
                  {formatProcessorLicenseCalc(
                    previewPhysicalCores,
                    effectiveFactor.core_factor,
                    previewLicensesRequired,
                  )}
                </p>
                {licenseType === "nup" && previewNamedUsersRequired != null ? (
                  <p className="text-muted">
                    {previewLicensesRequired} licensable cores × 25 = {previewNamedUsersRequired}{" "}
                    NUPs
                  </p>
                ) : null}
              </>
            ) : (
              <p className="text-muted">Enter sockets and cores per socket to preview licenses.</p>
            )}
            {cpuProfile &&
            cpuProfile.core_factor != null &&
            cpuProfile.processor_licenses_required != null ? (
              <p className="mt-1 text-xs text-muted">
                Saved profile: {cpuProfile.core_factor_name ?? "Manual override"} (
                {cpuProfile.core_factor}) · {cpuProfile.processor_licenses_required} processor
                licenses
              </p>
            ) : null}
          </div>
        )}
      </Card>

      {cpuHistory && cpuHistory.length > 0 && (
        <Card className="p-4">
          <h3 className="mb-3 font-medium">CPU profile history</h3>
          <ul className="space-y-2 text-sm">
            {cpuHistory.map((entry) => (
              <li key={entry.id} className="border-b border-separator pb-2">
                {entry.source}: {entry.socket_count}×{entry.cores_per_socket} cores (
                {entry.physical_cores} physical)
                {entry.processor_licenses_required != null
                  ? ` · ${entry.processor_licenses_required} processor licenses`
                  : ""}{" "}
                · {new Date(entry.collected_at).toLocaleString()}
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
}
