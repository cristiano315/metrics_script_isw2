"""
Script di validazione dataset CSV per bug prediction.

Controlla:
- duplicati (release, class)
- valori mancanti
- validità numerica
- distribuzione metriche

Uso:
python validate_dataset.py dataset.csv
"""

import pandas as pd
import sys


def validate_csv(file_path):
    print(f"\n📁 Validazione dataset: {file_path}")

    # =====================
    # LOAD DATASET
    # =====================
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(f"❌ Errore lettura CSV: {e}")
        return

    print(f"\n✅ Dataset caricato")
    print(f"Righe: {len(df)}")
    print(f"Colonne: {len(df.columns)}")

    # =====================
    # CHECK COLONNE
    # =====================
    required_cols = ["project", "release", "class", "buggy"]

    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        print(f"❌ Colonne mancanti: {missing_cols}")
    else:
        print("✅ Colonne base presenti")

    # =====================
    # DUPLICATI
    # =====================
    duplicates = df.duplicated(subset=["release", "class"])

    if duplicates.any():
        print(f"❌ Duplicati trovati: {duplicates.sum()}")
        print(df[duplicates].head())
    else:
        print("✅ Nessun duplicato (release, class)")

    # =====================
    # VALORI MANCANTI
    # =====================
    missing = df.isnull().sum()

    if missing.sum() > 0:
        print("\n⚠️ Valori mancanti:")
        print(missing[missing > 0])
    else:
        print("✅ Nessun valore mancante")

    # =====================
    # TIPO NUMERICO
    # =====================
    numeric_cols = df.select_dtypes(include=['number']).columns

    print("\n📊 Controllo metriche numeriche...")

    for col in numeric_cols:
        if df[col].isnull().all():
            print(f"⚠️ {col}: tutti valori nulli")

    print("✅ Tipi numerici OK")

    # =====================
    # VALORI NEGATIVI SOSPETTI
    # =====================
    suspicious_cols = ["loc", "churn", "loc_added", "revisions"]

    print("\n📊 Controllo valori negativi...")

    for col in suspicious_cols:
        if col in df.columns:
            negative = (df[col] < 0).sum()
            if negative > 0:
                print(f"❌ {col}: {negative} valori negativi")
            else:
                print(f"✅ {col}: OK")

    # =====================
    # DISTRIBUZIONE BASE
    # =====================
    print("\n📊 Statistiche dataset:")

    print(df.describe().T[["mean", "min", "max"]])

    # =====================
    # LABEL
    # =====================
    if "buggy" in df.columns:
        print("\n📊 Distribuzione label:")
        print(df["buggy"].value_counts())

    print("\n✅ Validazione completata")


if __name__ == "__main__":

    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = "dataset.csv"

    validate_csv(file_path)
