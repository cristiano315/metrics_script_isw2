import pandas as pd
import sys
import re
import os

from metrics_scripts import helper as hp


def version_key(release_name):
    """
    Fallback numerico per ordinare release del tipo:
    release_0.10.1 -> [0, 10, 1]
    """
    try:
        v = release_name.replace("release_", "")
        v = re.split(r"[-_]", v)[0]
        return [int(x) for x in v.split(".")]
    except Exception:
        return [0]


def release_time_key(release_name, repo_path):
    """
    Ordina le release in base al timestamp reale del tag Git associato.
    Se il tag non è risolvibile, usa version_key come fallback.
    """
    if not repo_path:
        return version_key(release_name)

    git_ref = hp.resolve_git_ref(repo_path, release_name)
    if not git_ref:
        return version_key(release_name)

    ts = hp.get_ref_timestamp(repo_path, git_ref)
    return ts if ts is not None else version_key(release_name)


def monotonic_non_decreasing(series):
    """
    Verifica che una sequenza sia monotona non decrescente.
    """
    return all(x <= y for x, y in zip(series, series[1:]))


def validate_dataset(file_path, repo_path=None):
    print(f"\n📁 Validazione dataset: {file_path}")

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(f"❌ Errore lettura CSV: {e}")
        return

    print("\n✅ Dataset caricato")
    print(f"Righe: {len(df)}")
    print(f"Colonne: {len(df.columns)}")

    # =========================
    # 1. CHECK COLONNE
    # =========================
    required_cols = [
        "project", "release", "class",
        "loc", "churn", "loc_added", "fan_out",
        "revisions", "max_churn", "max_loc_added",
        "avg_churn", "avg_loc_added",
        "fan_in_total", "loc_touched_total",
        "age", "weighted_age",
        "nauth", "nfix", "ndev",
        "bug_density", "fix",
        "ns", "revisions_density",
        "buggy"
    ]

    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        print(f"❌ Colonne mancanti: {missing_cols}")
        return
    else:
        print("✅ Colonne base presenti")

    # =========================
    # 2. DUPLICATI
    # =========================
    duplicates = df.duplicated(subset=["release", "class"]).sum()
    if duplicates > 0:
        print(f"❌ Duplicati trovati su (release, class): {duplicates}")
    else:
        print("✅ Nessun duplicato (release, class)")

    # =========================
    # 3. VALORI MANCANTI
    # =========================
    total_nulls = df.isnull().sum().sum()
    if total_nulls > 0:
        print(f"❌ Valori mancanti trovati: {total_nulls}")
        print(df.isnull().sum()[df.isnull().sum() > 0])
        return
    else:
        print("✅ Nessun valore mancante")

    # =========================
    # 4. TIPI NUMERICI
    # =========================
    numeric_cols = [
        "loc", "churn", "loc_added", "fan_out",
        "revisions", "max_churn", "max_loc_added",
        "avg_churn", "avg_loc_added",
        "fan_in_total", "loc_touched_total",
        "age", "weighted_age",
        "nauth", "nfix", "ndev",
        "bug_density", "fix",
        "ns", "revisions_density"
    ]

    print("\n📊 Controllo metriche numeriche...")
    for col in numeric_cols:
        if not pd.api.types.is_numeric_dtype(df[col]):
            print(f"❌ {col} non numerica")
            return
    print("✅ Tipi numerici OK")

    # =========================
    # 5. VALORI NEGATIVI
    # =========================
    print("\n📊 Controllo valori negativi...")
    has_negative = False

    for col in numeric_cols:
        negatives = (df[col] < 0).sum()
        if negatives > 0:
            print(f"❌ {col}: {negatives} valori negativi")
            has_negative = True
        else:
            print(f"✅ {col}: OK")

    if has_negative:
        return

    # =========================
    # 6. FORMULE DERIVATE
    # =========================
    print("\n📊 Controllo formule derivate...")

    bug_density_expected = (df["nfix"] / df["loc"]).fillna(0)
    bug_density_ok = ((df["bug_density"] - bug_density_expected).abs() < 1e-9).all()
    print("✅ bug_density corretta" if bug_density_ok else "❌ bug_density NON corretta")

    fix_expected = (df["nfix"] > 0).astype(int)
    fix_ok = (df["fix"] == fix_expected).all()
    print("✅ fix corretto" if fix_ok else "❌ fix NON corretto")

    revisions_density_expected = (df["revisions"] / df["loc"]).fillna(0)
    rev_density_ok = ((df["revisions_density"] - revisions_density_expected).abs() < 1e-9).all()
    print("✅ revisions_density corretta" if rev_density_ok else "❌ revisions_density NON corretta")

    # =========================
    # 7. ORDINAMENTO RELEASE
    # =========================
    if repo_path:
        release_order_map = {
            r: release_time_key(r, repo_path)
            for r in df["release"].unique()
        }
    else:
        release_order_map = {
            r: version_key(r)
            for r in df["release"].unique()
        }

    df["release_order"] = df["release"].map(release_order_map)

    # release globale più antica
    releases_sorted = sorted(df["release"].unique(), key=lambda r: release_order_map[r])
    first_release = releases_sorted[0]

    print("\n📊 Controllo prima release globale...")
    print(f"Prima release reale: {first_release}")

    # =========================
    # 8. PRIMA OSSERVAZIONE PER CLASSE
    # =========================
    print("\n📊 Controllo prima osservazione per classe...")

    first_observation_errors = {
        "churn_zero": 0,
        "loc_added_zero": 0,
        "revisions_zero": 0,
        "max_churn_zero": 0,
        "max_loc_added_zero": 0,
        "loc_touched_total_zero": 0
    }

    for class_name, group in df.groupby("class"):
        group_sorted = group.sort_values("release_order")
        first_row = group_sorted.iloc[0]

        if first_row["churn"] != 0:
            first_observation_errors["churn_zero"] += 1
        if first_row["loc_added"] != 0:
            first_observation_errors["loc_added_zero"] += 1
        if first_row["revisions"] != 0:
            first_observation_errors["revisions_zero"] += 1
        if first_row["max_churn"] != 0:
            first_observation_errors["max_churn_zero"] += 1
        if first_row["max_loc_added"] != 0:
            first_observation_errors["max_loc_added_zero"] += 1
        if first_row["loc_touched_total"] != 0:
            first_observation_errors["loc_touched_total_zero"] += 1

    for check, count in first_observation_errors.items():
        if count == 0:
            print(f"✅ {check}")
        else:
            print(f"❌ {check}: {count} classi")

    # =========================
    # 9. MONOTONICITÀ
    # =========================
    print("\n📊 Controllo monotonicità metriche cumulative...")

    # queste DEVONO essere monotone
    strict_monotonic_cols = [
        "revisions",
        "max_churn",
        "max_loc_added",
        "fan_in_total",
        "loc_touched_total"
    ]

    # queste possono NON esserlo per branch/tag Git differenti
    git_sensitive_cols = [
        "age",
        "nauth",
        "nfix"
    ]

    strict_errors = {}
    warning_errors = {}

    for class_name, group in df.groupby("class"):
        group_sorted = group.sort_values("release_order")

        for col in strict_monotonic_cols:
            vals = group_sorted[col].tolist()
            if not monotonic_non_decreasing(vals):
                strict_errors.setdefault(col, 0)
                strict_errors[col] += 1

        for col in git_sensitive_cols:
            vals = group_sorted[col].tolist()
            if not monotonic_non_decreasing(vals):
                warning_errors.setdefault(col, 0)
                warning_errors[col] += 1

    if strict_errors:
        print("❌ Problemi di monotonicità trovati (metriche che dovrebbero essere monotone):")
        for col, count in strict_errors.items():
            print(f"   - {col}: {count} classi")
    else:
        print("✅ Metriche cumulative monotone")

    if warning_errors:
        print("\n⚠️ Warning metriche Git-based non monotone:")
        print("   (fenomeno possibile se i tag provengono da branch diversi)")
        for col, count in warning_errors.items():
            print(f"   - {col}: {count} classi")
    else:
        print("✅ Metriche Git-based monotone")

    # =========================
    # 10. STATISTICHE DESCRITTIVE
    # =========================
    print("\n📊 Statistiche dataset:")
    print(df[numeric_cols].describe().T[["mean", "min", "max"]])

    # =========================
    # 11. LABEL
    # =========================
    print("\n📊 Distribuzione label:")
    print(df["buggy"].value_counts(dropna=False))

    print("\n✅ Validazione completata")


if __name__ == "__main__":
    dataset_path = "dataset.csv"
    repo_path = None

    if len(sys.argv) >= 2:
        dataset_path = sys.argv[1]

    if len(sys.argv) >= 3:
        repo_path = sys.argv[2]

    validate_dataset(dataset_path, repo_path)