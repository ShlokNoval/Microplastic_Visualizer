// components/SpectrumChart.js
import React, { useRef } from 'react'
import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend)

export default function SpectrumChart({ labels = [], values = [] }) {
  const chartRef = useRef(null)

  const data = {
    labels: labels,
    datasets: [
      {
        label: 'Absorbance',
        data: values,
        fill: true,
        tension: 0.2,
        borderWidth: 2,
        backgroundColor: 'rgba(34,211,238,0.08)',
        borderColor: '#06b6d4',
        pointRadius: 2
      }
    ]
  }

  const AXIS_COLOR = '#e2e8f0'  // light gray-blue
  const LABEL_COLOR = '#f8fafc'

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: { color: LABEL_COLOR, font: { size: 14 } }
      },
      tooltip: {
        titleFont: { size: 14 },
        bodyFont: { size: 13 },
        backgroundColor: 'rgba(2,6,23,0.75)'
      }
    },
    scales: {
      x: {
        title: { display: true, text: 'Wavelength', color: AXIS_COLOR, font: { size: 15 } },
        ticks: { color: AXIS_COLOR, font: { size: 13 } },
        grid: { color: 'rgba(255,255,255,0.03)' }
      },
      y: {
        title: { display: true, text: 'Absorbance', color: AXIS_COLOR, font: { size: 15 } },
        ticks: { color: AXIS_COLOR, font: { size: 13 } },
        grid: { color: 'rgba(255,255,255,0.03)' }
      }
    }
  }

  function downloadChart() {
    const chart = chartRef.current
    if (!chart) {
      alert("Chart not ready yet")
      return
    }
    let dataUrl = null
    try {
      dataUrl = chart.toBase64Image ? chart.toBase64Image() : (chart.chartInstance && chart.chartInstance.toBase64Image ? chart.chartInstance.toBase64Image() : null)
    } catch (err) {
      console.error(err)
    }
    if (!dataUrl) {
      alert("Unable to get chart image")
      return
    }
    const a = document.createElement('a')
    a.href = dataUrl
    a.download = 'spectrum.png'
    document.body.appendChild(a)
    a.click()
    a.remove()
  }

  function exportCSV() {
    if (!labels.length || !values.length) {
      alert("No spectrum data to export")
      return
    }

    // Build CSV rows: header + wavelength/value pairs
    const csvRows = [
      "Wavelength,Absorbance",
      ...labels.map((w, i) => `${w},${values[i]}`)
    ]

    const csvContent = csvRows.join("\r\n")
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = "spectrum.csv"
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  }

  return (
    <div>
      <div className="flex justify-end gap-2 mb-2">
        <button
          onClick={downloadChart}
          className="px-2 py-1 rounded bg-sky-600 hover:bg-sky-500 text-white text-sm"
        >
          Export PNG
        </button>
        <button
          onClick={exportCSV}
          className="px-2 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-white text-sm"
        >
          Export CSV
        </button>
      </div>

      <div style={{ height: 360 }}>
        <Line ref={chartRef} data={data} options={options} />
      </div>
    </div>
  )
}
