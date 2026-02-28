# evaluate_saved_models.py  (outputs CSVs with named proba columns)
import os
import joblib
import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, r2_score, mean_squared_error, mean_absolute_error, classification_report, confusion_matrix

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(SCRIPT_DIR, "models")

clf_path = os.path.join(MODEL_DIR, "classification_model.pkl")
rgr_path = os.path.join(MODEL_DIR, "regression_model.pkl")

angle_csv = os.path.join(SCRIPT_DIR, "synthetic_microplastic_angle.csv")
scatter_csv = os.path.join(SCRIPT_DIR, "synthetic_scatter_data.csv")

# Output files (will be placed in models/)
out_class_csv = os.path.join(MODEL_DIR, "classification_results_flat_named.csv")
out_rgr_csv = os.path.join(MODEL_DIR, "regression_results_flat.csv")

# Basic checks
for p in (clf_path, rgr_path, angle_csv, scatter_csv):
    if not os.path.exists(p):
        raise SystemExit(f"Required file not found: {p}")

# Load models
clf = joblib.load(clf_path)
rgr = joblib.load(rgr_path)

# Load data
df_clf = pd.read_csv(angle_csv)
df_rgr = pd.read_csv(scatter_csv)

# Required feature lists
features_clf = ['Pol0','Pol45','Pol90','Pol135','Pol_Ratio_0_90','Pol_Diff_0_90']
features_rgr = ['fsc_peak','ssc_peak','bsc_peak','fsc_ssc_ratio','refractive_index','noise_level']
target_clf = 'PlasticType'
target_rgr = 'size_um'

# Validate presence
missing_clf = [c for c in features_clf + [target_clf] if c not in df_clf.columns]
missing_rgr = [c for c in features_rgr + [target_rgr] if c not in df_rgr.columns]
if missing_clf:
    raise SystemExit(f"Angle CSV missing columns: {missing_clf}")
if missing_rgr:
    raise SystemExit(f"Scatter CSV missing columns: {missing_rgr}")

# Prepare arrays
Xc = df_clf[features_clf].astype(float)
yc = df_clf[target_clf].astype(str)

Xr = df_rgr[features_rgr].astype(float)
yr = df_rgr[target_rgr].astype(float)

# Predictions
y_pred_c = clf.predict(Xc)
# predict_proba -> shape (n_samples, n_classes)
try:
    y_proba = clf.predict_proba(Xc)
except Exception as e:
    # If classifier doesn't support predict_proba
    print("Warning: classifier has no predict_proba:", e)
    y_proba = np.full((len(Xc), len(clf.classes_)), np.nan)

y_pred_r = rgr.predict(Xr)

# Build columns named with actual class labels
class_names = [str(c) for c in clf.classes_]  # class order used by predict_proba
# sanitize names for column safety (replace spaces/slashes with underscore)
def sanitize(name):
    return "".join(ch if (ch.isalnum() or ch in ('_', '-')) else '_' for ch in name)

sanitized = [sanitize(c) for c in class_names]
proba_cols = [f"proba_{s}" for s in sanitized]
proba_df = pd.DataFrame(y_proba, columns=proba_cols)

# Build classification output: original df + y_true + y_pred + proba columns
out_clf_df = df_clf.reset_index(drop=True).copy()
out_clf_df["y_true"] = yc.reset_index(drop=True)
out_clf_df["y_pred"] = pd.Series(y_pred_c).astype(str).reset_index(drop=True)

# Drop any old single-column 'classification_proba' if present (legacy)
if "classification_proba" in out_clf_df.columns:
    out_clf_df = out_clf_df.drop(columns=["classification_proba"])

# Add named proba columns (numeric)
out_clf_df = pd.concat([out_clf_df, proba_df.reset_index(drop=True)], axis=1)

# Save classification CSV
out_clf_df.to_csv(out_class_csv, index=False)
print(f"Saved classification CSV: {out_class_csv}")

# Debug preview and dtypes
print("\n=== Classification CSV preview (first 6 rows) ===")
print(out_clf_df.head(6).to_string(index=False))
print("\nProba column dtypes:")
print(out_clf_df[proba_cols].dtypes)

# Print classification metrics (optional)
try:
    acc = accuracy_score(yc, y_pred_c)
    print(f"\nClassification accuracy on full CSV: {acc:.6f}")
    print("\nClassification report (sample):")
    print(classification_report(yc, y_pred_c))
except Exception as e:
    print("Could not compute classification metrics:", e)

# ---------------- Regression results
out_rgr_df = df_rgr.reset_index(drop=True).copy()
out_rgr_df["y_true"] = yr.reset_index(drop=True)
out_rgr_df["y_pred"] = pd.Series(y_pred_r).astype(float).reset_index(drop=True)

# Save regression CSV
out_rgr_df.to_csv(out_rgr_csv, index=False)
print(f"\nSaved regression CSV: {out_rgr_csv}")

print("\n=== Regression CSV preview (first 6 rows) ===")
print(out_rgr_df.head(6).to_string(index=False))

# Regression metrics
try:
    r2 = r2_score(yr, y_pred_r)
    mse = mean_squared_error(yr, y_pred_r)
    mae = mean_absolute_error(yr, y_pred_r)
    print(f"\nRegression R2: {r2:.6f}, MSE: {mse:.6f}, MAE: {mae:.6f}")
except Exception as e:
    print("Could not compute regression metrics:", e)

print("\nDONE. Inspect the CSV files in the models/ folder.")
