# backend/combine_csvs.py
import pandas as pd
import numpy as np
import os

# Paths (adjust if your files are elsewhere)
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
angle_path = os.path.join(os.path.dirname(__file__), "synthetic_microplastic_angle.csv")
scatter_path = os.path.join(os.path.dirname(__file__), "synthetic_scatter_data.csv")

# Read
df_angle = pd.read_csv(angle_path)
df_scatter = pd.read_csv(scatter_path)

# Choose N = minimum length, or set a custom N
N = min(len(df_angle), len(df_scatter))
# If you want a smaller test-size, set N = 200, for example:
# N = 200

# Shuffle both (so pairing isn't deterministic)
df_angle = df_angle.sample(frac=1, random_state=42).reset_index(drop=True).iloc[:N]
df_scatter = df_scatter.sample(frac=1, random_state=11).reset_index(drop=True).iloc[:N]

# Reset indices and concat columns side-by-side
df_combined = pd.concat([df_angle.reset_index(drop=True), df_scatter.reset_index(drop=True)], axis=1)

# Optionally: drop duplicate columns if any column names collide (none should)
# If both had a column with same name (e.g., "size_um"), rename or drop
if 'size_um' in df_combined.columns:
    # keep scatter's size_um (it should be there) but you can drop it if you want only predicted
    pass

# Output path (backend folder)
out_path = os.path.join(os.path.dirname(__file__), "combined_for_inference.csv")
df_combined.to_csv(out_path, index=False)
print(f"Saved combined CSV with {N} rows to: {out_path}")
