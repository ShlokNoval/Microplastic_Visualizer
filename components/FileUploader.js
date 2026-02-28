// components/FileUploader.js
import React from 'react'
import Papa from 'papaparse'

export default function FileUploader({ onDataReady }) {
  function handleFile(e) {
    const file = e.target.files?.[0]
    if (!file) return

    Papa.parse(file, {
      header: true,
      dynamicTyping: true,
      skipEmptyLines: true,
      complete: (results) => {
        const rows = results.data
        if (!rows || !rows.length) {
          // fallback for header-less CSVs
          Papa.parse(file, {
            header: false,
            dynamicTyping: true,
            skipEmptyLines: true,
            complete: (res2) => {
              const raw = res2.data
              const mapped = raw.map(r => ({ wavelength: Number(r[0]), absorbance: Number(r[1]) }))
              // pass both parsed rows and original file
              onDataReady(mapped, file)
            }
          })
          return
        }

        const first = rows[0]
        const keys = Object.keys(first)
        const lowerKeys = keys.map(k => k.toLowerCase())
        const waveIdx = lowerKeys.findIndex(k => k.includes('wavelength') || k.includes('wave') || k.includes('nm') )
        const absIdx = lowerKeys.findIndex(k => k.includes('absorb') || k.includes('abs') || k.includes('intensity'))

        const mapped = rows.map(r => {
          if (waveIdx !== -1 && absIdx !== -1) {
            const wk = keys[waveIdx]
            const ak = keys[absIdx]
            return { wavelength: Number(r[wk]), absorbance: Number(r[ak]) }
          }
          const numericCols = keys.filter(k => typeof r[k] === 'number' && !isNaN(r[k]))
          if (numericCols.length >= 2) {
            return { wavelength: Number(r[numericCols[0]]), absorbance: Number(r[numericCols[1]]) }
          }
          return { wavelength: Number(r[keys[0]]), absorbance: Number(r[keys[1]]) }
        })

        const cleaned = mapped.filter(r => typeof r.wavelength === 'number' && !isNaN(r.wavelength) && typeof r.absorbance === 'number' && !isNaN(r.absorbance))

        // Pass the cleaned rows AND the original file so parent can upload raw CSV if required
        onDataReady(cleaned, file)
      }
    })
  }

  return (
    <div>
      <label className="block">
        <span className="sr-only">Upload CSV</span>
        <input type="file" accept=".csv" onChange={handleFile} className="block w-full text-sm text-sky-200" />
      </label>
    </div>
  )
}
