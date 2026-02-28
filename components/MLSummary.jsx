// components/MLSummary.jsx
import React, { useMemo } from "react";
import { Bar, Pie } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
} from "chart.js";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

const BORDER_COLOR = 'rgba(255,255,255,0.06)';
const BAR_BG = 'rgba(34,211,238,0.72)';

function computeHistogramBins(values, binCount = 12) {
  if (!values.length) return { labels: [], counts: [] };
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = (max - min) || 1;
  const binSize = span / binCount;
  const edges = Array.from({ length: binCount }, (_, i) => min + i * binSize);
  const counts = new Array(binCount).fill(0);

  values.forEach(v => {
    let idx = Math.floor((v - min) / binSize);
    if (idx < 0) idx = 0;
    if (idx >= binCount) idx = binCount - 1;
    counts[idx] += 1;
  });

  const labels = edges.map((e, i) => {
    const start = edges[i];
    const end = (i === edges.length - 1) ? (max) : (edges[i] + binSize);
    return `${start.toFixed(1)}–${end.toFixed(1)}`;
  });

  return { labels, counts };
}

function safeStringifyCell(v, maxLen = 2000) {
  if (v === null || typeof v === "undefined") return "";
  if (typeof v === "number" || typeof v === "boolean") return String(v);
  if (typeof v === "bigint") return v.toString();
  if (typeof v === "string") {
    return v.length > maxLen ? v.slice(0, maxLen) + "…" : v;
  }
  if (Array.isArray(v)) {
    try {
      const str = v.map(x => (x === null || typeof x === "undefined" ? "" : String(x))).join("|");
      return str.length > maxLen ? str.slice(0, maxLen) + "…" : str;
    } catch (e) {
      return "";
    }
  }
  try {
    const seen = new WeakSet();
    const s = JSON.stringify(v, function (k, val) {
      if (typeof val === "function") return undefined;
      if (typeof val === "object" && val !== null) {
        if (seen.has(val)) return "[Circular]";
        seen.add(val);
      }
      return val;
    });
    return s.length > maxLen ? s.slice(0, maxLen) + "…" : s;
  } catch (e) {
    try { return String(v).slice(0, maxLen); } catch (_) { return ""; }
  }
}

function csvCell(val) {
  const s = safeStringifyCell(val);
  return `"${String(s).replace(/"/g, '""')}"`;
}

function flattenResult(r, probaSlotCount = 0) {
  const flat = {};
  const cls = r?.classification;
  if (cls === null || typeof cls === "undefined") {
    flat.PlasticType = "";
  } else if (typeof cls === "string") {
    flat.PlasticType = cls;
  } else if (typeof cls === "object") {
    if ("PlasticType" in cls) flat.PlasticType = cls.PlasticType;
    else if ("plastic" in cls) flat.PlasticType = cls.plastic;
    else flat.PlasticType = cls.PlasticType ?? cls.plastic ?? "";

    const proba = cls.proba ?? cls.probabilities ?? cls.probability ?? cls.prob;
    if (Array.isArray(proba)) {
      proba.forEach((p, i) => flat[`classification_proba_${i}`] = p);
    } else if (typeof proba === "object" && proba !== null) {
      Object.entries(proba).forEach(([k, v]) => flat[`proba_${k}`] = v);
    }
  } else {
    flat.PlasticType = String(cls);
  }

  if (typeof r.size_um === "object" && r.size_um !== null) {
    flat.size_um = safeStringifyCell(r.size_um);
  } else {
    flat.size_um = (typeof r.size_um !== "undefined" && r.size_um !== null) ? r.size_um : "";
  }

  Object.keys(r || {}).forEach(k => {
    if (k === "classification" || k === "size_um") return;
    const v = r[k];
    if (Array.isArray(v)) flat[k] = v.join("|");
    else if (typeof v === "object" && v !== null) flat[k] = safeStringifyCell(v);
    else flat[k] = v;
  });

  for (let i = 0; i < probaSlotCount; ++i) {
    const key = `classification_proba_${i}`;
    if (!(key in flat)) flat[key] = "";
  }

  return flat;
}

function exportResultsToCSV(results, filename = "results.csv") {
  try {
    if (!results || !results.length) {
      alert("No results to export");
      return;
    }

    let maxProbaLen = 0;
    results.forEach(r => {
      const cls = r?.classification;
      if (cls && typeof cls === "object") {
        const proba = cls.proba ?? cls.probabilities ?? cls.prob;
        if (Array.isArray(proba)) maxProbaLen = Math.max(maxProbaLen, proba.length);
      }
    });

    const flattened = results.map((r, idx) => {
      const f = flattenResult(r, maxProbaLen);
      f.sample_index = idx + 1;
      return f;
    });

    const probaCols = Array.from({ length: maxProbaLen }).map((_, i) => `classification_proba_${i}`);
    const allKeys = new Set();
    flattened.forEach(f => Object.keys(f).forEach(k => allKeys.add(k)));

    const restKeys = Array.from(allKeys).filter(k => !["sample_index", "PlasticType", "size_um", ...probaCols].includes(k)).sort();
    const headers = ["sample_index", "PlasticType", "size_um", ...probaCols, ...restKeys];

    const csvRows = [
      headers.join(","),
      ...flattened.map(row => headers.map(h => csvCell(row[h])).join(","))
    ];

    const csvContent = csvRows.join("\r\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  } catch (err) {
    console.error("Export error:", err, results && results[0]);
    alert("Failed to export CSV — see console for details.");
    try {
      console.log("First result sample (debug):", results && results[0]);
    } catch (_) { }
  }
}

export default function MLSummary({ results, title = "ML Summary", bins = 12 }) {
  const sizes = useMemo(() => {
    if (!results || !Array.isArray(results)) return [];
    return results
      .map(r => (typeof r.size_um !== "undefined" ? Number(r.size_um) : null))
      .filter(v => v !== null && !isNaN(v));
  }, [results]);

  const classCounts = useMemo(() => {
    const map = {};
    if (!results || !Array.isArray(results)) return map;
    results.forEach(r => {
      const cls = r?.classification?.PlasticType ?? r?.classification ?? "unknown";
      map[cls] = (map[cls] || 0) + 1;
    });
    return map;
  }, [results]);

  const { labels: histLabels, counts: histCounts } = useMemo(
    () => computeHistogramBins(sizes, bins),
    [sizes, bins]
  );

  const barData = {
    labels: histLabels,
    datasets: [
      {
        label: "Count",
        data: histCounts,
        backgroundColor: BAR_BG,
        borderColor: BORDER_COLOR,
        borderRadius: 6,
        barThickness: 'flex',
      }
    ]
  };

  const pieLabels = Object.keys(classCounts);
  const pieDataCounts = pieLabels.map(k => classCounts[k]);
  const pieData = {
    labels: pieLabels,
    datasets: [
      {
        data: pieDataCounts,
        backgroundColor: pieLabels.map((_, i) => `hsl(${(i * 55) % 360} 72% 52%)`),
        borderWidth: 0
      }
    ]
  };

  return (
    <div className="w-full">
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-lg font-semibold text-sky-100">{title}</h3>
        <div className="flex gap-2">
          <button
            onClick={() => exportResultsToCSV(results, "results.csv")}
            className="px-2 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-white text-sm"
          >
            Export CSV
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Histogram */}
        <div className="relative card p-4" style={{ minHeight: 320, overflow: "hidden" }}>
          <div className="text-sm text-sky-200 mb-2">Predicted size distribution (µm)</div>
          {sizes.length ? (
            <div style={{ height: 240 }}>
              <Bar
                data={barData}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: {
                      labels: {
                        color: "#f8fafc",
                        font: { size: 13 }
                      }
                    }
                  },
                  scales: {
                    x: {
                      ticks: { color: "#e2e8f0" },
                      grid: { color: "rgba(255,255,255,0.08)" }
                    },
                    y: {
                      ticks: { color: "#e2e8f0" },
                      grid: { color: "rgba(255,255,255,0.08)" }
                    }
                  }
                }}
              />
            </div>
          ) : (
            <div className="text-sky-300 text-sm">No size predictions available.</div>
          )}
        </div>

        {/* Pie */}
        <div className="relative card p-4" style={{ minHeight: 320, overflow: "hidden" }}>
          <div className="text-sm text-sky-200 mb-2">Classification breakdown</div>
          {pieLabels.length ? (
            <div style={{ height: 240 }}>
              <Pie
                data={pieData}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: {
                      labels: {
                        color: "#f8fafc",
                        font: { size: 13 }
                      }
                    }
                  }
                }}
              />
            </div>
          ) : (
            <div className="text-sky-300 text-sm">No classification predictions available.</div>
          )}
        </div>
      </div>
    </div>
  );
}
