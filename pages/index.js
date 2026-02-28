// pages/index.js
import React, { useState, useMemo } from 'react'
import MLSummary from "../components/MLSummary"
import FileUploader from '../components/FileUploader'
import SpectrumChart from '../components/SpectrumChart'
import LoadingBar from '../components/LoadingBar'
import ModelResults from '../components/ModelResults'

const API_BASE = "http://127.0.0.1:5000"  // backend URL (fastest & explicit)

export default function Home() {
  const [dataRows, setDataRows] = useState(null)
  const [loading, setLoading] = useState(false)

  const [selectedFile, setSelectedFile] = useState(null) // raw CSV file, if user uploaded one
  const [mlResults, setMlResults] = useState(null)
  const [mlLoading, setMlLoading] = useState(false)
  const [mlError, setMlError] = useState(null)

  const wavelengths = useMemo(() => dataRows ? dataRows.map(r => r.wavelength) : [], [dataRows])
  const absorbances = useMemo(() => dataRows ? dataRows.map(r => r.absorbance) : [], [dataRows])

  // keep spectrum preview and store the selected file for upload
  function handleData(parsedRows, originalFile) {
    setDataRows(parsedRows)
    setSelectedFile(originalFile || null)
    // removed client-side batch normalization/upload — we use server CSV upload only
  }

  // Upload the RAW CSV file to /predict/file (multipart)
  async function uploadFileToBackend() {
    if (!selectedFile) {
      setMlError("No file available to upload. Please re-upload CSV.")
      return
    }
    setMlLoading(true)
    setMlError(null)
    setMlResults(null)

    try {
      const fd = new FormData()
      fd.append("file", selectedFile) // backend expects field name 'file'

      const res = await fetch(`${API_BASE}/predict/file`, {
        method: "POST",
        body: fd
      })
      if (!res.ok) {
        const txt = await res.text()
        throw new Error(txt || `Server returned ${res.status}`)
      }
      const json = await res.json()
      setMlResults(json.results)
    } catch (err) {
      setMlError(err.message || "File upload failed")
    } finally {
      setMlLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-start justify-center p-8">
      <div className="max-w-6xl w-full grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* LEFT: controls + per-row results */}
        <div className="lg:col-span-1">
          <div className="card">
            <h1 className="text-2xl font-semibold mb-2 text-sky-100">Microplastic Visualizer</h1>
            <p className="text-sm text-sky-200 mb-4">Upload a CSV with wavelength/absorbance to see the spectrum, or upload an angle CSV (Pol0/Pol45/Pol90/Pol135) to get ML predictions.</p>

            <FileUploader onDataReady={(rows, file) => {
              setLoading(true)
              setTimeout(() => {
                setLoading(false)
                handleData(rows, file)
              }, 700)
            }} />

            <div className="mt-4 flex gap-2">
              <button
                onClick={uploadFileToBackend}
                disabled={!selectedFile || mlLoading}
                className="px-3 py-1 rounded bg-sky-600 hover:bg-sky-500 text-white disabled:opacity-50"
              >
                {mlLoading ? "Uploading..." : "Upload CSV to ML (raw file)"}
              </button>
              {/* Batch button removed to simplify UI */}
            </div>

            <div className="mt-6 text-xs text-sky-200">Key Point: Use "Upload CSV to ML" to validate server-side parsing; the server will return both classification and size</div>
          </div>

          <div className="mt-6">
            {mlLoading ? (
              <div className="card"><LoadingBar /></div>
            ) : (
              <div className="card p-4">
                <ModelResults results={mlResults} />
              </div>
            )}
            {mlError && <div className="text-red-400 mt-2">{mlError}</div>}
          </div>
        </div>

        {/* RIGHT: spectrum + ML summary (wide area) */}
        <div className="lg:col-span-2 space-y-6">
          <div className="card">
            <h2 className="text-xl font-semibold mb-3 text-sky-100">Spectrum</h2>
            {loading ? (
              <div className="flex items-center justify-center h-40"><LoadingBar /></div>
            ) : dataRows ? (
              <div style={{ height: 360 }}>
                <SpectrumChart labels={wavelengths} values={absorbances} />
              </div>
            ) : (
              <div className="h-56 flex items-center justify-center text-sky-300">Upload a CSV to view the spectrum.</div>
            )}
          </div>

          <div className="card p-4">
            {mlLoading ? <LoadingBar /> : <MLSummary results={mlResults} />}
          </div>

          <div className="card">
            <h2 className="text-xl font-semibold mb-3 text-sky-100">About</h2>
            <p className="text-sm text-sky-200">Team Cytomers @SIH2025</p>
          </div>
        </div>
      </div>
    </div>
  )
}
