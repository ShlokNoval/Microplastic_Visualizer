// components/ModelResults.jsx
import React from "react";



export default function ModelResults({ results }) {
  if (!results) {
    return <div className="text-sky-300 text-sm">No ML results yet.</div>;
  }
  if (!Array.isArray(results) || results.length === 0) {
    return <div className="text-sky-300 text-sm">No predictions returned.</div>;
  }
      
  return (
    <div>
      <h3 className="text-lg font-semibold text-sky-100 mb-2">ML Predictions</h3>
      <div className="space-y-3">
        {results.map((r, idx) => (
          <div key={idx} className="p-2 rounded border bg-slate-900 text-sky-200">
            <div><strong>Sample #{idx + 1}</strong></div>

            {r.classification && (
              <div className="text-sm mt-1">
                <strong>Plastic:</strong> {r.classification.PlasticType ?? r.classification.Plastic ?? "—"}
                {r.classification.proba && <div className="text-xs mt-1">Probs: {JSON.stringify(r.classification.proba)}</div>}
              </div>
            )}

            {typeof r.size_um !== "undefined" && (
              <div className="text-sm mt-1"><strong>Predicted size (µm):</strong> {Number(r.size_um).toFixed(3)}</div>
            )}

            {r.error && <div className="text-red-400 mt-1">Error: {r.error}</div>}
          </div>
        ))}
      </div>
    </div>
  );
}
