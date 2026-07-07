export type LicenseStatus = "active" | "expired" | "pending";

export const LICENSE_STATUS_OPTIONS: { value: LicenseStatus; label: string }[] = [
  { value: "active", label: "Active" },
  { value: "expired", label: "Expired" },
  { value: "pending", label: "Pending" },
];
export type HostEnvironment = "production" | "non_production";
export type HostLicenseType = "cpu" | "nup";

export const HOST_ENVIRONMENT_OPTIONS: { value: HostEnvironment; label: string }[] = [
  { value: "production", label: "Production" },
  { value: "non_production", label: "Non-production" },
];

export const HOST_LICENSE_TYPE_OPTIONS: { value: HostLicenseType; label: string }[] = [
  { value: "cpu", label: "CPU (processor)" },
  { value: "nup", label: "NUP (Named User Plus)" },
];

export function formatHostEnvironment(environment: HostEnvironment | null | undefined): string {
  if (environment === "production") {
    return "Production";
  }
  if (environment === "non_production") {
    return "Non-production";
  }
  return "—";
}

export function formatHostLicenseType(licenseType: HostLicenseType): string {
  return licenseType === "cpu" ? "CPU" : "NUP";
}
export type LicenseMetric =
  | "processor"
  | "named_user_plus"
  | "named_user"
  | "socket"
  | "concurrent_user"
  | "application_user"
  | "ocpu"
  | "other";

export const PROCESSOR_METRICS: LicenseMetric[] = ["processor", "socket", "ocpu"];
export const NAMED_USER_METRICS: LicenseMetric[] = [
  "named_user_plus",
  "named_user",
  "concurrent_user",
  "application_user",
];
export type CpuProfileSource = "manual" | "ssh_probe";

export interface License {
  id: string;
  csi: string;
  customer_name: string;
  support_level: string | null;
  start_date: string | null;
  renewal_date: string | null;
  status: LicenseStatus;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface Product {
  id: string;
  agreement_id: string;
  product_name: string;
  option_name: string | null;
  metric: LicenseMetric;
  quantity: number;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface LicenseDetail extends License {
  products: Product[];
}

export interface LicenseListItem extends License {
  product_count: number;
  products: Product[];
}

export interface Host {
  id: string;
  hostname: string;
  fqdn: string | null;
  ip_address: string | null;
  environment: HostEnvironment | null;
  license_type: HostLicenseType;
  named_users_required: number | null;
  os_name: string | null;
  notes: string | null;
  ssh_enabled: boolean;
  ssh_port: number;
  ssh_user: string | null;
  created_at: string;
  updated_at: string;
}

export interface HostListItem extends Host {
  assigned_products: string[];
  cpu_model: string | null;
  socket_count: number | null;
  cores_per_socket: number | null;
  physical_cores: number | null;
  core_factor: number | null;
  core_factor_name: string | null;
  processor_licenses_required: number | null;
  licenses_required_label: string | null;
  licenses_required_detail: string[];
}

export interface HostProduct {
  id: string;
  host_id: string;
  product_name: string;
  option_name: string | null;
  license_type: HostLicenseType;
  metric: LicenseMetric;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface PooledProduct {
  product_name: string;
  option_name: string | null;
  license_type: HostLicenseType;
  total_quantity: number;
}

export interface CoreFactor {
  id: string;
  name: string;
  match_pattern: string;
  core_factor: number;
  priority: number;
  is_default: boolean;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface CpuProfile {
  id: string;
  host_id: string;
  cpu_model: string | null;
  core_factor: number | null;
  core_factor_name: string | null;
  socket_count: number;
  cores_per_socket: number;
  threads_per_core: number;
  logical_processor_count: number;
  physical_cores: number;
  processor_licenses_required: number | null;
  source: CpuProfileSource;
  collected_at: string;
  created_at: string;
}

export interface CatalogProduct {
  id: string;
  price_list_id: string;
  category: string;
  product_name: string;
  option_name: string | null;
  list_price_nup_usd: number | null;
  list_price_nup_support_usd: number | null;
  list_price_processor_usd: number | null;
  list_price_processor_support_usd: number | null;
  supports_nup: boolean;
  supports_processor: boolean;
}

export interface CatalogProductInput {
  price_list_id: string;
  category: string;
  product_name: string;
  option_name?: string | null;
  list_price_nup_usd?: number | null;
  list_price_nup_support_usd?: number | null;
  list_price_processor_usd?: number | null;
  list_price_processor_support_usd?: number | null;
  supports_nup?: boolean;
  supports_processor?: boolean;
}

export interface ProcessorComplianceLine {
  product_id: string;
  product_name: string;
  licensed_quantity: number;
}

export interface AgreementCompliance {
  agreement_id: string;
  csi: string;
  processor_licenses_purchased: number;
  processor_lines: ProcessorComplianceLine[];
  named_user_plus_purchased: number;
}

export interface ProductLicenseSummary {
  product_name: string;
  cores_licensed: number;
  nups_licensed: number;
  cores_in_use: number;
  nups_in_use: number | null;
  balance: number;
}

export interface DashboardSummary {
  agreement_count: number;
  product_count: number;
  host_count: number;
  total_physical_cores: number;
  renewals_30_days: number;
  renewals_60_days: number;
  renewals_90_days: number;
  license_inventory: ProductLicenseSummary[];
}

export interface LicenseTrackerReport {
  generated_at: string;
  summary: DashboardSummary;
  agreements: LicenseDetail[];
  hosts: HostListItem[];
  product_compliance: ProductLicenseSummary[];
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || response.statusText);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export const api = {
  getDashboard: () => request<DashboardSummary>("/api/v1/dashboard/summary"),
  getFullReport: (params?: { shortfallsOnly?: boolean }) => {
    const query = new URLSearchParams();
    if (params?.shortfallsOnly) {
      query.set("shortfalls_only", "true");
    }
    const suffix = query.toString() ? `?${query.toString()}` : "";
    return request<LicenseTrackerReport>(`/api/v1/reports/full${suffix}`);
  },
  downloadFullReport: async (params?: {
    format?: "csv" | "pdf";
    shortfallsOnly?: boolean;
  }) => {
    const format = params?.format ?? "csv";
    const query = new URLSearchParams({ format });
    if (params?.shortfallsOnly) {
      query.set("shortfalls_only", "true");
    }
    const response = await fetch(`${API_BASE}/api/v1/reports/full?${query.toString()}`);
    if (!response.ok) {
      const detail = await response.text();
      throw new Error(detail || response.statusText);
    }
    const blob = await response.blob();
    const disposition = response.headers.get("Content-Disposition") ?? "";
    const match = disposition.match(/filename="([^"]+)"/);
    const defaultFilename =
      format === "pdf" ? "license-tracker-report.pdf" : "license-tracker-report.csv";
    const filename = match?.[1] ?? defaultFilename;
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    anchor.click();
    URL.revokeObjectURL(url);
  },
  downloadFullReportCsv: async (params?: { shortfallsOnly?: boolean }) =>
    api.downloadFullReport({ format: "csv", ...params }),
  downloadFullReportPdf: async (params?: { shortfallsOnly?: boolean }) =>
    api.downloadFullReport({ format: "pdf", ...params }),
  listAgreements: () => request<LicenseListItem[]>("/api/v1/agreements"),
  listCatalogCategories: () => request<string[]>("/api/v1/catalog/categories"),
  listCatalogProducts: (params?: { search?: string; category?: string; limit?: number }) => {
    const query = new URLSearchParams();
    if (params?.search) {
      query.set("search", params.search);
    }
    if (params?.category) {
      query.set("category", params.category);
    }
    if (params?.limit) {
      query.set("limit", String(params.limit));
    }
    const suffix = query.toString() ? `?${query.toString()}` : "";
    return request<CatalogProduct[]>(`/api/v1/catalog/products${suffix}`);
  },
  getCatalogProduct: (id: string) => request<CatalogProduct>(`/api/v1/catalog/products/${id}`),
  createCatalogProduct: (body: CatalogProductInput) =>
    request<CatalogProduct>("/api/v1/catalog/products", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  updateCatalogProduct: (id: string, body: Partial<CatalogProductInput>) =>
    request<CatalogProduct>(`/api/v1/catalog/products/${id}`, {
      method: "PUT",
      body: JSON.stringify(body),
    }),
  deleteCatalogProduct: (id: string) =>
    request<void>(`/api/v1/catalog/products/${id}`, { method: "DELETE" }),
  getAgreement: (id: string) => request<LicenseDetail>(`/api/v1/agreements/${id}`),
  getAgreementCompliance: (id: string) =>
    request<AgreementCompliance>(`/api/v1/agreements/${id}/compliance`),
  createAgreement: (body: Partial<License>) =>
    request<License>("/api/v1/agreements", { method: "POST", body: JSON.stringify(body) }),
  updateAgreement: (id: string, body: Partial<License>) =>
    request<License>(`/api/v1/agreements/${id}`, { method: "PUT", body: JSON.stringify(body) }),
  deleteAgreement: (id: string) =>
    request<void>(`/api/v1/agreements/${id}`, { method: "DELETE" }),
  createProduct: (agreementId: string, body: Partial<Product>) =>
    request<Product>(`/api/v1/agreements/${agreementId}/entitlements`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  updateProduct: (agreementId: string, productId: string, body: Partial<Product>) =>
    request<Product>(`/api/v1/agreements/${agreementId}/entitlements/${productId}`, {
      method: "PUT",
      body: JSON.stringify(body),
    }),
  deleteProduct: (agreementId: string, productId: string) =>
    request<void>(`/api/v1/agreements/${agreementId}/entitlements/${productId}`, {
      method: "DELETE",
    }),
  listHosts: () => request<HostListItem[]>("/api/v1/hosts"),
  listPooledProducts: () => request<PooledProduct[]>("/api/v1/hosts/pooled-products"),
  getHost: (id: string) => request<Host>(`/api/v1/hosts/${id}`),
  createHost: (body: Partial<Host>) =>
    request<Host>("/api/v1/hosts", { method: "POST", body: JSON.stringify(body) }),
  updateHost: (id: string, body: Partial<Host>) =>
    request<Host>(`/api/v1/hosts/${id}`, { method: "PUT", body: JSON.stringify(body) }),
  listCoreFactors: () => request<CoreFactor[]>("/api/v1/core-factors"),
  resolveCoreFactor: (cpuModel: string) =>
    request<CoreFactor>(
      `/api/v1/core-factors/resolve?cpu_model=${encodeURIComponent(cpuModel)}`,
    ),
  getCpuProfile: (hostId: string) => request<CpuProfile>(`/api/v1/hosts/${hostId}/cpu-profile`),
  upsertCpuProfile: (
    hostId: string,
    body: {
      cpu_model?: string | null;
      core_factor?: number | null;
      socket_count: number;
      cores_per_socket: number;
      threads_per_core: number;
      logical_processor_count?: number;
    },
  ) =>
    request<CpuProfile>(`/api/v1/hosts/${hostId}/cpu-profile`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  getCpuHistory: (hostId: string) =>
    request<CpuProfile[]>(`/api/v1/hosts/${hostId}/cpu-profile/history`),
  listHostProducts: (hostId: string) =>
    request<HostProduct[]>(`/api/v1/hosts/${hostId}/entitlements`),
  assignHostProduct: (
    hostId: string,
    body: {
      product_name: string;
      option_name?: string | null;
    },
  ) =>
    request<HostProduct>(`/api/v1/hosts/${hostId}/entitlements`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  unassignHostProduct: (hostId: string, assignmentId: string) =>
    request<void>(`/api/v1/hosts/${hostId}/entitlements/${assignmentId}`, {
      method: "DELETE",
    }),
  seedDatabase: () =>
    request<{ status: string; message: string }>("/api/v1/system/seed", {
      method: "POST",
    }),
};

