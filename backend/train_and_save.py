# train_and_save.py (robust version)
import os
import sys
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

def find_file(root_dir, candidates):
    for name in candidates:
        path = os.path.join(root_dir, name)
        if os.path.exists(path):
            return path
    return None

def load_csv_from_repo_root(script_file_dir, candidates):
    repo_root = os.path.abspath(os.path.join(script_file_dir, ".."))
    found = find_file(repo_root, candidates)
    if found:
        print(f"Found file: {found}")
        return found
    found2 = find_file(script_file_dir, candidates)
    if found2:
        print(f"Found file in backend/: {found2}")
        return found2
    print("Tried these locations (repo root and backend/):")
    for c in candidates:
        print(" -", os.path.join(repo_root, c))
        print(" -", os.path.join(script_file_dir, c))
    return None

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))

    angle_candidates = [
        "synthetic_microplastic_angle.csv",
        "synthetic_microplastic_4angle.csv",
        "synathetic_microplastic_angle.csv",
        "synthetic_microplastic_angle .csv"
    ]
    scatter_candidates = [
        "synthetic_scatter_data.csv",
        "synthetic_scatter.csv",
        "synthetic_scatter_data .csv"
    ]

    angle_path = load_csv_from_repo_root(script_dir, angle_candidates)
    scatter_path = load_csv_from_repo_root(script_dir, scatter_candidates)

    if angle_path is None:
        print("\nERROR: Could not find any angle CSV. Put the file in the project root or backend/ with one of these names:")
        print("\n".join(angle_candidates))
        sys.exit(1)

    if scatter_path is None:
        print("\nERROR: Could not find any scatter CSV. Put the file in the project root or backend/ with one of these names:")
        print("\n".join(scatter_candidates))
        sys.exit(1)

    models_dir = os.path.join(script_dir, "models")
    os.makedirs(models_dir, exist_ok=True)

    print("\nLoading angle CSV:", angle_path)
    df = pd.read_csv(angle_path)
    features_clf = ['Pol0', 'Pol45', 'Pol90', 'Pol135', 'Pol_Ratio_0_90', 'Pol_Diff_0_90']
    missing = [c for c in features_clf if c not in df.columns]
    if missing:
        print(f"WARNING: angle CSV missing columns: {missing}. Please check file.")
    X = df[features_clf]
    y = df['PlasticType']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)
    clf_path = os.path.join(models_dir, "classification_model.pkl")
    joblib.dump(clf, clf_path)
    print("Saved classifier to", clf_path)
    print("Classification test accuracy:", clf.score(X_test, y_test))

    print("\nLoading scatter CSV:", scatter_path)
    df2 = pd.read_csv(scatter_path)
    features_reg = ['fsc_peak', 'ssc_peak', 'bsc_peak', 'fsc_ssc_ratio', 'refractive_index', 'noise_level']
    missing2 = [c for c in features_reg if c not in df2.columns]
    if missing2:
        print(f"WARNING: scatter CSV missing columns: {missing2}. Please check file.")
    Xr = df2[features_reg]
    yr = df2['size_um']
    Xr_train, Xr_test, yr_train, yr_test = train_test_split(Xr, yr, test_size=0.2, random_state=42)
    rfr = RandomForestRegressor(n_estimators=100, random_state=42)
    rfr.fit(Xr_train, yr_train)
    rgr_path = os.path.join(models_dir, "regression_model.pkl")
    joblib.dump(rfr, rgr_path)
    print("Saved regressor to", rgr_path)

    from sklearn.metrics import mean_squared_error, r2_score
    pred = rfr.predict(Xr_test)
    print("Regressor R2:", r2_score(yr_test, pred))
    print("\nDone. Models saved in:", models_dir)

if __name__ == "__main__":
    main()
