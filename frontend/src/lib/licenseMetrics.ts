import type { LicenseMetric } from "../api/client";

export const LICENSE_METRIC_OPTIONS: { value: LicenseMetric; label: string; group: string }[] = [
  {
    value: "processor",
    label: "Processor (core-based)",
    group: "Core-based licensing",
  },
  {
    value: "socket",
    label: "Socket",
    group: "Core-based licensing",
  },
  {
    value: "ocpu",
    label: "OCPU (cloud)",
    group: "Core-based licensing",
  },
  {
    value: "named_user_plus",
    label: "Named User Plus (NUP)",
    group: "Named-user licensing",
  },
  {
    value: "named_user",
    label: "Named User",
    group: "Named-user licensing",
  },
  {
    value: "concurrent_user",
    label: "Concurrent User",
    group: "Named-user licensing",
  },
  {
    value: "application_user",
    label: "Application User",
    group: "Named-user licensing",
  },
  {
    value: "other",
    label: "Other",
    group: "Other",
  },
];

const METRIC_LABELS = Object.fromEntries(
  LICENSE_METRIC_OPTIONS.map((option) => [option.value, option.label]),
) as Record<LicenseMetric, string>;

/** Return a human-readable label for a license metric value. */
export function formatLicenseMetric(metric: LicenseMetric): string {
  return METRIC_LABELS[metric] ?? metric;
}

/** Return whether a metric is core-based processor licensing. */
export function isProcessorBasedMetric(metric: LicenseMetric): boolean {
  return metric === "processor" || metric === "socket" || metric === "ocpu";
}

/** Return whether a metric is named-user licensing. */
export function isNamedUserMetric(metric: LicenseMetric): boolean {
  return (
    metric === "named_user_plus" ||
    metric === "named_user" ||
    metric === "concurrent_user" ||
    metric === "application_user"
  );
}

/** Summarize entitlements for a CSI list row. */
export function formatEntitlementSummary(
  products: { product_name: string; metric: LicenseMetric; quantity: number }[],
): string {
  if (products.length === 0) {
    return "No products";
  }
  return products
    .map(
      (product) =>
        `${product.product_name}: ${product.quantity} ${formatLicenseMetric(product.metric)}`,
    )
    .join(" · ");
}

/** Format processor license requirement from cores and multiplier. */
export function formatProcessorLicenseCalc(
  physicalCores: number,
  coreFactor: number,
  licensesRequired: number,
): string {
  return `${physicalCores} cores × ${coreFactor} = ${licensesRequired} processor licenses`;
}

export const NUP_USERS_PER_LICENSE = 25;

/** Format named-user license requirement from licensable cores. */
export function formatNamedUsersCalc(
  licensableCores: number,
  namedUsersRequired: number,
): string {
  return `${licensableCores} licensable cores × ${NUP_USERS_PER_LICENSE} = ${namedUsersRequired} NUPs`;
}

/** Compute named users required from licensable processor cores. */
export function calculateNamedUsersRequired(
  licensableCores: number | null | undefined,
): number | null {
  if (licensableCores == null || licensableCores < 1) {
    return null;
  }
  return licensableCores * NUP_USERS_PER_LICENSE;
}

/** Format the full path from sockets to licensable processor cores. */
export function formatLicensableCoresCalc(host: {
  cpu_model: string | null;
  socket_count: number | null;
  cores_per_socket: number | null;
  physical_cores: number | null;
  core_factor: number | null;
  core_factor_name: string | null;
  processor_licenses_required: number | null;
}): string[] {
  if (
    host.socket_count == null ||
    host.cores_per_socket == null ||
    host.physical_cores == null
  ) {
    return ["Not set"];
  }

  const lines: string[] = [];
  if (host.cpu_model) {
    lines.push(host.cpu_model);
  }
  lines.push(
    `${host.socket_count} sockets × ${host.cores_per_socket} cores/socket = ${host.physical_cores} physical cores`,
  );
  if (host.core_factor != null && host.processor_licenses_required != null) {
    const factorLabel = host.core_factor_name
      ? `${host.core_factor_name} (${host.core_factor})`
      : String(host.core_factor);
    lines.push(
      `${host.physical_cores} physical cores × ${factorLabel} = ${host.processor_licenses_required} licensable cores`,
    );
  } else {
    lines.push("Core factor not set — licensable cores unknown");
  }
  return lines;
}
