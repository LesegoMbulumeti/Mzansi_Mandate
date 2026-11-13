"use client";

import dynamic from "next/dynamic";
import type { ApexOptions } from "apexcharts";

const Chart = dynamic(() => import("react-apexcharts"), { ssr: false });

type Point = { label: string; allowed: number; blocked: number; volume: string };

export function DashboardCharts({ data, currency }: { data: Point[]; currency: string }) {
  const labels = data.map((point) => point.label);
  const outcomesOptions: ApexOptions = {
    chart: { type: "bar", toolbar: { show: false }, fontFamily: "inherit", background: "transparent" },
    colors: ["#316cf4", "#f59e61"],
    plotOptions: { bar: { borderRadius: 5, columnWidth: "42%" } },
    dataLabels: { enabled: false },
    grid: { borderColor: "#edf0f5", strokeDashArray: 4 },
    legend: { position: "top", horizontalAlign: "right", fontSize: "12px", markers: { size: 4 }, itemMargin: { horizontal: 10 } },
    xaxis: { categories: labels, axisBorder: { show: false }, axisTicks: { show: false }, labels: { style: { colors: "#8892a3", fontSize: "11px" } } },
    yaxis: { min: 0, forceNiceScale: true, labels: { style: { colors: "#8892a3", fontSize: "11px" } } },
    tooltip: { theme: "light" },
  };
  const volumeOptions: ApexOptions = {
    chart: { type: "area", toolbar: { show: false }, sparkline: { enabled: false }, fontFamily: "inherit", background: "transparent" },
    colors: ["#27b7a0"],
    stroke: { curve: "smooth", width: 2.5 },
    fill: { type: "gradient", gradient: { opacityFrom: 0.2, opacityTo: 0.015, stops: [0, 90, 100] } },
    dataLabels: { enabled: false },
    grid: { borderColor: "#edf0f5", strokeDashArray: 4 },
    xaxis: { categories: labels, axisBorder: { show: false }, axisTicks: { show: false }, labels: { style: { colors: "#8892a3", fontSize: "11px" } } },
    yaxis: { min: 0, forceNiceScale: true, labels: { style: { colors: "#8892a3", fontSize: "11px" }, formatter: (value) => `${currency} ${Math.round(value).toLocaleString("en-ZA")}` } },
    tooltip: { y: { formatter: (value) => `${currency} ${(value ?? 0).toLocaleString("en-ZA", { maximumFractionDigits: 2 })}` } },
  };

  return <div className="chart-grid">
    <article className="panel chart-panel"><div className="panel-heading"><div><h3>Policy activity</h3><p>Allowed and blocked intents · 7 days</p></div><span className="chart-period">7 days</span></div><Chart type="bar" height={260} options={outcomesOptions} series={[{ name: "Allowed", data: data.map((point) => point.allowed) }, { name: "Blocked", data: data.map((point) => point.blocked) }]} /></article>
    <article className="panel chart-panel"><div className="panel-heading"><div><h3>Authorized volume</h3><p>Submitted or settled · {currency}</p></div><span className="chart-legend"><i /> Volume</span></div><Chart type="area" height={260} options={volumeOptions} series={[{ name: "Volume", data: data.map((point) => Number(point.volume)) }]} /></article>
  </div>;
}
