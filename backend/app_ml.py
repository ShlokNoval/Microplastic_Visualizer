# app_ml.py
"""
FastAPI app that loads saved sklearn models and serves batch predictions.
Very defensive about removing any legacy 'classification_proba' column/header
so exported CSVs are clean. JSON responses keep nested classification.PlasticType
but do NOT include a combined 'proba' list.
"""

import os
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any
import joblib
import pandas as pd
import numpy as np
from io import StringIO, BytesIO

app = FastAPI(title="Microplastic ML API")

# CORS (dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load models
MODEL_DIR = "models"
clf_path = os.path.join(MODEL_DIR, "classification_model.pkl")
rgr_path = os.path.join(MODEL_DIR, "regression_model.pkl")
if not os.path.exists(clf_path) or not os.path.exists(rgr_path):
    raise Exception("Model files not found. Run train_and_save.py and ensure models/ exists.")

clf_model = joblib.load(clf_path)
rgr_model = joblib.load(rgr_path)

# Prepare class names and sanitized keys
RAW_CLASS_NAMES = [str(c) for c in getattr(clf_model, "classes_", [])]
def _sanitize(s: str) -> str:
    s = str(s)
    return "".join(ch if (ch.isalnum() or ch in ("_", "-")) else "_" for ch in s)
SANITIZED_CLASS_NAMES = [_sanitize(c) for c in RAW_CLASS_NAMES]
PROBA_KEYS = [f"proba_{s}" for s in SANITIZED_CLASS_NAMES]  # e.g. proba_PE, proba_PP

# Request schemas
class AngleSample(BaseModel):
    Pol0: float; Pol45: float; Pol90: float; Pol135: float
    Pol_Ratio_0_90: float; Pol_Diff_0_90: float

class ScatterSample(BaseModel):
    fsc_peak: float; ssc_peak: float; bsc_peak: float
    fsc_ssc_ratio: float; refractive_index: float; noise_level: float

# Helpers
def _get_proba_matrix(df_clf):
    if not hasattr(clf_model, "predict_proba"):
        return None
    try:
        return clf_model.predict_proba(df_clf).tolist()
    except Exception:
        return None

def _clean_row_remove_legacy(row: Dict[str, Any]):
    """Remove legacy combined fields from a row dict if present (defensive)."""
    # remove top-level legacy variants
    for legacy in ("classification_proba", "classification.proba", "classification_proba_list"):
        if legacy in row:
            row.pop(legacy, None)
    # nested classification.proba removal
    if "classification" in row and isinstance(row["classification"], dict):
        row["classification"].pop("proba", None)
        # also remove any nested keys that contain classification_proba text
        for k in list(row["classification"].keys()):
            if "classification_proba" in k or "proba" in k and k.startswith("classification"):
                row["classification"].pop(k, None)
    return row

def _drop_legacy_columns_from_df(df: pd.DataFrame) -> pd.DataFrame:
    """Defensively drop any dataframe columns related to legacy 'classification_proba' or empty headers."""
    # Normalize column names (strip whitespace)
    new_cols = []
    for c in df.columns:
        if isinstance(c, str):
            new_cols.append(c.strip())
        else:
            new_cols.append(c)
    df.columns = new_cols

    # Build drop list: any column whose name contains 'classification_proba' (case-insensitive),
    # equals '' (empty header), or starts with 'unnamed' (pandas default)
    drop_cols = []
    for c in df.columns:
        if not isinstance(c, str):
            continue
        lc = c.lower().strip()
        if "classification_proba" in lc or lc == "" or lc.startswith("unnamed") or lc == "classification.proba":
            drop_cols.append(c)

    if drop_cols:
        df = df.drop(columns=drop_cols, errors="ignore")

    return df

# Endpoints
@app.post("/predict/batch")
def predict_batch(samples: List[Dict[str, Any]]):
    results = []
    angle_keys = {"Pol0","Pol45","Pol90","Pol135","Pol_Ratio_0_90","Pol_Diff_0_90"}
    scatter_keys = {"fsc_peak","ssc_peak","bsc_peak","fsc_ssc_ratio","refractive_index","noise_level"}

    for s in samples:
        res = {}
        s_keys = set(s.keys())

        # classification
        if angle_keys.issubset(s_keys):
            df_clf = pd.DataFrame([{
                "Pol0": float(s["Pol0"]),
                "Pol45": float(s["Pol45"]),
                "Pol90": float(s["Pol90"]),
                "Pol135": float(s["Pol135"]),
                "Pol_Ratio_0_90": float(s["Pol_Ratio_0_90"]),
                "Pol_Diff_0_90": float(s["Pol_Diff_0_90"]),
            }])
            pred = clf_model.predict(df_clf)[0]
            proba_matrix = _get_proba_matrix(df_clf)
            proba_vec = proba_matrix[0] if proba_matrix is not None else None

            # nested classification object for UI compatibility
            res["classification"] = {"PlasticType": str(pred)}

            # flattened proba_<CLASS> keys
            for j, key in enumerate(PROBA_KEYS):
                try:
                    res[key] = float(proba_vec[j]) if proba_vec is not None else None
                except Exception:
                    res[key] = None

        # regression
        if scatter_keys.issubset(s_keys):
            df_r = pd.DataFrame([{
                "fsc_peak": float(s["fsc_peak"]),
                "ssc_peak": float(s["ssc_peak"]),
                "bsc_peak": float(s["bsc_peak"]),
                "fsc_ssc_ratio": float(s["fsc_ssc_ratio"]),
                "refractive_index": float(s["refractive_index"]),
                "noise_level": float(s["noise_level"]),
            }])
            res["size_um"] = float(rgr_model.predict(df_r)[0])

        if not res:
            raise HTTPException(status_code=400, detail=f"Sample missing required features: {s}")

        # defensive cleanup per-row
        res = _clean_row_remove_legacy(res)
        results.append(res)

    # Also ensure no top-level 'classification_proba' sneaks in
    for r in results:
        if "classification_proba" in r:
            r.pop("classification_proba", None)
        if "classification" in r and isinstance(r["classification"], dict):
            r["classification"].pop("proba", None)

    return {"results": results}

@app.post("/predict/file")
async def predict_file(
    file: UploadFile = File(...),
    response_format: str = Query("json", description="Response format: 'json' or 'csv'")
):
    contents = await file.read()
    try:
        text = contents.decode("utf-8")
    except Exception:
        raise HTTPException(status_code=400, detail="Could not read file as UTF-8 CSV")

    try:
        df = pd.read_csv(StringIO(text))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {e}")

    angle_cols_ordered = ["Pol0","Pol45","Pol90","Pol135","Pol_Ratio_0_90","Pol_Diff_0_90"]
    scatter_cols_ordered = ["fsc_peak","ssc_peak","bsc_peak","fsc_ssc_ratio","refractive_index","noise_level"]

    cols_present = set(df.columns)
    has_angles = all(c in cols_present for c in angle_cols_ordered)
    has_scatter = all(c in cols_present for c in scatter_cols_ordered)

    if not has_angles and not has_scatter:
        missing_angle = [c for c in angle_cols_ordered if c not in cols_present]
        missing_scatter = [c for c in scatter_cols_ordered if c not in cols_present]
        raise HTTPException(status_code=400, detail={
            "error": "CSV missing required columns",
            "missing_angle_columns": missing_angle,
            "missing_scatter_columns": missing_scatter
        })

    n_rows = len(df)
    # classification preds + proba matrix
    if has_angles:
        X_clf = df[angle_cols_ordered].astype(float)
        preds_clf = clf_model.predict(X_clf)
        proba_matrix = _get_proba_matrix(X_clf)
    else:
        preds_clf = [None] * n_rows
        proba_matrix = None

    # regression preds
    if has_scatter:
        X_rgr = df[scatter_cols_ordered].astype(float)
        preds_size = rgr_model.predict(X_rgr).tolist()
    else:
        preds_size = [None] * n_rows

    # build flat rows
    flat_rows = []
    for i in range(n_rows):
        row = {}
        if preds_clf[i] is not None:
            row["classification"] = {"PlasticType": str(preds_clf[i])}
            vec = proba_matrix[i] if proba_matrix is not None else None
            for j, pk in enumerate(PROBA_KEYS):
                try:
                    row[pk] = float(vec[j]) if vec is not None else None
                except Exception:
                    row[pk] = None
        else:
            for pk in PROBA_KEYS:
                row[pk] = None

        if preds_size[i] is not None:
            row["size_um"] = float(preds_size[i])

        # defensive removal of legacy fields inside each row
        row = _clean_row_remove_legacy(row)
        flat_rows.append(row)

    # JSON response (default)
    if response_format.lower() == "json":
        # remove any leftover legacy keys defensively
        for r in flat_rows:
            r.pop("classification_proba", None)
            if "classification" in r and isinstance(r["classification"], dict):
                r["classification"].pop("proba", None)
        return {"results": flat_rows}

    # CSV response
    elif response_format.lower() == "csv":
        df_out = pd.DataFrame(flat_rows)

        # If a 'classification' column exists, extract PlasticType and drop nested
        if "classification" in df_out.columns:
            df_out["PlasticType"] = df_out["classification"].apply(
                lambda x: x.get("PlasticType") if isinstance(x, dict) else None
            )
            df_out = df_out.drop(columns=["classification"])

        # Normalize and drop legacy/empty/unnamed columns
        df_out = _drop_legacy_columns_from_df(df_out)

        # Ensure proba keys exist
        for pk in PROBA_KEYS:
            if pk not in df_out.columns:
                df_out[pk] = None

        # Reorder columns: PlasticType, proba keys, size_um, then others
        cols = []
        if "PlasticType" in df_out.columns:
            cols.append("PlasticType")
        cols.extend(PROBA_KEYS)
        if "size_um" in df_out.columns:
            cols.append("size_um")
        existing = [c for c in cols if c in df_out.columns]
        others = [c for c in df_out.columns if c not in existing]
        df_out = df_out[existing + others]

        # Final defensive drop of any column that (case-insensitively) contains 'classification_proba'
        drop_cols_final = [c for c in df_out.columns if isinstance(c, str) and "classification_proba" in c.lower().replace(".", "_")]
        if drop_cols_final:
            df_out = df_out.drop(columns=drop_cols_final, errors="ignore")

        # Stream CSV
        buffer = BytesIO()
        df_out.to_csv(buffer, index=False)
        buffer.seek(0)
        filename_root = os.path.splitext(file.filename)[0] if file.filename else "predictions"
        headers = {"Content-Disposition": f"attachment; filename={filename_root}_predictions.csv"}
        return StreamingResponse(buffer, media_type="text/csv", headers=headers)

    else:
        raise HTTPException(status_code=400, detail="response_format must be 'json' or 'csv'")

@app.get("/")
def read_root():
    return {"info": "Microplastic ML API — POST /predict/batch or /predict/file"}
