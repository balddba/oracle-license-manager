import ReactECharts from "echarts-for-react";

import type { ProductLicenseSummary } from "../api/client";
import {
  buildComplianceChartOption,
  complianceChartHeight,
  complianceLabelCount,
} from "../lib/reportCharts";
import { useAppTheme } from "./ThemeProvider";

export function ReportCharts({
  productCompliance,
}: {
  productCompliance: ProductLicenseSummary[];
}) {
  const { resolvedTheme } = useAppTheme();
  const isDark = resolvedTheme === "dark";
  const complianceOption = buildComplianceChartOption(productCompliance, isDark);
  const complianceHeight = complianceChartHeight(complianceLabelCount(productCompliance));

  if (!complianceOption) {
    return null;
  }

  return (
    <section className="space-y-3">
      <h3 className="text-lg font-medium">Visual insights</h3>
      <div className="overflow-hidden rounded-lg border border-border bg-surface p-2">
        <ReactECharts
          key={`compliance-${resolvedTheme}`}
          option={complianceOption}
          style={{ height: complianceHeight }}
          opts={{ renderer: "canvas" }}
        />
      </div>
    </section>
  );
}
