# Microplastic Visualizer (Next.js)

This project is a single-page client-side Next.js app to:

- Upload and parse a CSV with `wavelength` and `absorbance` columns
- Show a dynamic molecule-like loading animation while processing
- Plot wavelength vs absorbance (interactive line chart)
- Display microplastic count (threshold adjustable)
- Show a chemistry-inspired polymer visualization

## Prerequisites

- Node.js v18+ (recommended)
- npm (included with Node) or yarn

## Install & Run

1. Create a new folder and put the files from this repo inside.
2. Run:

```bash
npm install
npm run dev
```

3. Open `http://localhost:3000` in your browser.

## File overview

- `pages/index.js` — main app UI
- `components/FileUploader.js` — handles CSV upload and parsing
- `components/LoadingMolecule.js` — chemistry-inspired loading animation
- `components/SpectrumChart.js` — Chart.js wrapper for the spectrum
- `components/PolymerViz.js` — polymer visualizer (radial molecule nodes)
- `styles/globals.css` — Tailwind + custom styles
- `tailwind.config.js` & `postcss.config.js` — Tailwind setup

## How it works (short)

- Select a CSV file (single file). Expected columns are `wavelength` and `absorbance` (case-insensitive). If different column names are used, the uploader tries to map the first two numeric columns.
- On upload, the app parses the CSV with PapaParse, shows the molecule loading animation for a short time (simulated processing), then renders the chart and polymer view.
- Microplastic count is derived as the number of rows whose absorbance is above a chosen threshold (default = mean + 0.5 * stddev). You can adjust the threshold using a slider.
