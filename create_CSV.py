"""
Modulo per l'esportazione del dataset in formato CSV.
Ogni riga rappresenta una coppia (project, release, class).
"""

import csv


def export_csv_rows(dataset_rows, output_path="dataset.csv"):
    """
    Esporta il dataset nel file CSV.

    Parametri:
    - dataset_rows: lista di dizionari (una riga = una coppia release-classe)
    - output_path: nome file CSV
    """

    print("\n📁 Creazione CSV...")

    if not dataset_rows:
        print("❌ Nessun dato da esportare")
        return

    # Header generato automaticamente
    headers = list(dataset_rows[0].keys())

    with open(output_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=headers)

        writer.writeheader()
        writer.writerows(dataset_rows)

    print(f"✅ CSV creato: {output_path}")