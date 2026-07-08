import type { EChartsOption } from "echarts";

import type { ProductLicenseSummary } from "../api/client";

const COLOR_LICENSED = "#3B82F6";
const COLOR_COMPLIANT = "#10B981";
const COLOR_SHORTFALL = "#EF4444";

interface ChartThemeColors {
  text: string;
  axisText: string;
  gridLine: string;
  legendText: string;
  tooltipBackground: string;
  tooltipBorder: string;
}

function getChartThemeColors(isDark: boolean): ChartThemeColors {
  if (isDark) {
    return {
      text: "#f8fafc",
      axisText: "#e2e8f0",
      gridLine: "#3d5a80",
      legendText: "#f1f5f9",
      tooltipBackground: "#1e3860",
      tooltipBorder: "#4a6a94",
    };
  }

  return {
    text: "#13233d",
    axisText: "#334155",
    gridLine: "#e0e0e0",
    legendText: "#334155",
    tooltipBackground: "#ffffff",
    tooltipBorder: "#e2e8f0",
  };
}

function axisLineStyle(color: string) {
  return { lineStyle: { color } };
}

export function buildComplianceChartOption(
  rows: ProductLicenseSummary[],
  isDark = false,
): EChartsOption | null {
  const colors = getChartThemeColors(isDark);
  const labels: string[] = [];
  const licensed: number[] = [];
  const inUse: Array<{ value: number; itemStyle: { color: string } }> = [];

  for (const item of rows) {
    if (item.cores_licensed > 0 || item.cores_in_use > 0) {
      labels.push(`${item.product_name} (Cores)`);
      licensed.push(item.cores_licensed);
      inUse.push({
        value: item.cores_in_use,
        itemStyle: {
          color: item.cores_in_use > item.cores_licensed ? COLOR_SHORTFALL : COLOR_COMPLIANT,
        },
      });
    }

    if (item.nups_licensed > 0 || (item.nups_in_use ?? 0) > 0) {
      const nupsInUse = item.nups_in_use ?? 0;
      labels.push(`${item.product_name} (NUPs)`);
      licensed.push(item.nups_licensed);
      inUse.push({
        value: nupsInUse,
        itemStyle: {
          color: nupsInUse > item.nups_licensed ? COLOR_SHORTFALL : COLOR_COMPLIANT,
        },
      });
    }
  }

  if (labels.length === 0) {
    return null;
  }

  const reversedLabels = [...labels].reverse();
  const reversedLicensed = [...licensed].reverse();
  const reversedInUse = [...inUse].reverse();

  return {
    title: {
      text: "Product License Compliance (Licensed vs In Use)",
      left: "center",
      textStyle: { fontSize: 14, color: colors.text, fontWeight: "bold" },
    },
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
      backgroundColor: colors.tooltipBackground,
      borderColor: colors.tooltipBorder,
      textStyle: { color: colors.text },
    },
    legend: {
      top: 28,
      data: ["Licensed", "In Use (Compliant)", "In Use (Shortfall)"],
      textStyle: { color: colors.legendText, fontSize: 11 },
    },
    grid: { left: 150, right: 56, top: 72, bottom: 32 },
    xAxis: {
      type: "value",
      axisLabel: { color: colors.axisText, fontSize: 11 },
      axisLine: axisLineStyle(colors.gridLine),
      axisTick: axisLineStyle(colors.gridLine),
      splitLine: { lineStyle: { type: "dashed", color: colors.gridLine } },
    },
    yAxis: {
      type: "category",
      data: reversedLabels,
      axisLabel: {
        fontSize: 11,
        color: colors.axisText,
        width: 130,
        overflow: "truncate",
      },
      axisLine: axisLineStyle(colors.gridLine),
      axisTick: axisLineStyle(colors.gridLine),
    },
    series: [
      {
        name: "Licensed",
        type: "bar",
        data: reversedLicensed,
        itemStyle: { color: COLOR_LICENSED },
        label: {
          show: true,
          position: "right",
          fontSize: 10,
          color: colors.axisText,
        },
        barGap: "20%",
      },
      {
        name: "In Use",
        type: "bar",
        data: reversedInUse,
        label: {
          show: true,
          position: "right",
          fontSize: 10,
          color: colors.axisText,
        },
      },
      {
        name: "In Use (Compliant)",
        type: "bar",
        data: [],
        itemStyle: { color: COLOR_COMPLIANT },
      },
      {
        name: "In Use (Shortfall)",
        type: "bar",
        data: [],
        itemStyle: { color: COLOR_SHORTFALL },
      },
    ],
  };
}

export function complianceLabelCount(rows: ProductLicenseSummary[]): number {
  let count = 0;
  for (const item of rows) {
    if (item.cores_licensed > 0 || item.cores_in_use > 0) {
      count += 1;
    }
    if (item.nups_licensed > 0 || (item.nups_in_use ?? 0) > 0) {
      count += 1;
    }
  }
  return count;
}

export function complianceChartHeight(labelCount: number): number {
  return Math.max(350, labelCount * 35 + 120);
}
