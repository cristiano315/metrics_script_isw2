"""
Data: 28/04/2026
Autore: enrico_barbatano

Main per la costruzione del dataset di metriche software a livello di classe.

Ogni riga del CSV rappresenta una coppia:
(project, release, class)

La pipeline:
1. ordina le release in base al timestamp reale del tag Git
2. legge i file Java di ogni release
3. calcola metriche locali della release
4. aggiorna metriche cumulative fino a quella release
5. calcola metriche Git coerenti con la release corrente
6. genera il dataset finale senza leakage temporale
"""

import os
import csv
import re

from metrics_scripts import size as sm
from metrics_scripts import churn
from metrics_scripts import LOC_Added as L_A
from metrics_scripts.fan_in_out import FanInOut

from metrics_scripts import evolution_metrics as evo
from metrics_scripts import aggregate_metrics as agg
from metrics_scripts import git_metrics as gitm
from metrics_scripts import helper as hp


def version_key(release_name):
    """
    Chiave numerica di fallback per ordinare release del tipo:
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
    Ordina le release usando il timestamp reale del tag Git corrispondente.
    Se il tag non è risolvibile, usa come fallback version_key().
    """
    if not repo_path:
        return version_key(release_name)

    git_ref = hp.resolve_git_ref(repo_path, release_name)
    if not git_ref:
        return version_key(release_name)

    ts = hp.get_ref_timestamp(repo_path, git_ref)
    if ts is None:
        return version_key(release_name)

    return ts


def export_csv_rows(rows, output_path="dataset.csv"):
    """
    Esporta il dataset in CSV.
    """
    print("\n📁 Creazione CSV...")

    if not rows:
        print("❌ Nessun dato da esportare")
        return

    headers = list(rows[0].keys())

    with open(output_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ CSV creato: {output_path}")


def create_dataset(directory_path, repo_path=None):
    """
    Costruisce il dataset finale.

    Parametri:
    - directory_path: cartella con le release estratte
    - repo_path: repository Git reale (serve per metriche storiche)

    Restituisce:
    - lista di righe del dataset finale
    """

    # Stato cumulativo per classe
    metrics = {}

    # Mantiene l'ultima versione nota della classe per calcolare i delta
    file_history = {}

    # Gestore dipendenze
    fan_io = FanInOut()

    # Prendo solo cartelle release_*
    all_entries = os.listdir(directory_path)
    releases = [
        d for d in all_entries
        if os.path.isdir(os.path.join(directory_path, d)) and d.startswith("release_")
    ]

    # ✅ Ordinamento corretto: data reale del tag Git, non solo numero versione
    releases = sorted(releases, key=lambda r: release_time_key(r, repo_path))

    print("\n✅ Release ordinate correttamente:")
    for r in releases:
        print(r)

    project_name = os.path.basename(repo_path) if repo_path else "unknown"

    # Evita duplicati su (release, class)
    seen_pairs = set()

    # Output finale
    dataset_rows = []

    # ======================================================
    # 1. PROCESSAMENTO RELEASE
    # ======================================================
    for release in releases:
        current_folder = os.path.join(directory_path, release)
        print(f"\n📂 Processing release: {release}")

        for root, _, files in os.walk(current_folder):
            for file_name in files:

                if not file_name.endswith(".java"):
                    continue

                full_path = os.path.join(root, file_name)

                # ID classe indipendente dalla release
                class_id = os.path.relpath(full_path, current_folder)

                pair_key = (release, class_id)
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)

                # Inizializzazione metriche cumulative
                if class_id not in metrics:
                    metrics[class_id] = {
                        "churn_total": 0,
                        "max_churn": 0,
                        "loc_added_total": 0,
                        "revisions": 0,
                        "max_loc_added": 0,
                        "ns": set()
                    }

                # Lettura file corrente
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    new_lines = f.readlines()

                # Prima osservazione della classe?
                is_first_observation = class_id not in file_history
                old_lines = file_history.get(class_id, [])

                # -------------------------
                # METRICHE LOCALI ALLA RELEASE
                # -------------------------
                loc = sm.calcola_loc_java(new_lines)

                # Prima osservazione = baseline, non modifica
                if is_first_observation:
                    current_churn = 0
                    loc_added = 0
                else:
                    current_churn = churn.calcola_churn_sloc(old_lines, new_lines)
                    loc_added = L_A.calculate_loc_added(old_lines, new_lines)

                # -------------------------
                # AGGIORNAMENTO METRICHE EVOLUTIVE CUMULATIVE
                # -------------------------
                evo.update_churn(metrics, class_id, current_churn, is_first_observation)
                evo.update_loc_added(metrics, class_id, loc_added, is_first_observation)
                evo.update_revisions(metrics, class_id, old_lines, new_lines, is_first_observation)

                # -------------------------
                # FAN OUT / FAN IN TOTAL
                # -------------------------
                fan_out, deps = fan_io.compute_fan_out(new_lines)
                fan_io.update_fan_in(class_id, deps)

                # -------------------------
                # NS (Number of Subsystems)
                # -------------------------
                subsystem = class_id.split(os.sep)[0]
                metrics[class_id]["ns"].add(subsystem)

                # -------------------------
                # SNAPSHOT AGGREGATE FINO A QUESTA RELEASE
                # -------------------------
                agg_snapshot = agg.snapshot_aggregate_metrics(
                    metrics,
                    class_id,
                    fan_io,
                    new_lines
                )

                # -------------------------
                # SNAPSHOT GIT FINO A QUESTA RELEASE
                # -------------------------
                git_snapshot = gitm.compute_git_metrics_for_release(
                    repo_path,
                    class_id,
                    release,
                    loc,
                    agg_snapshot["loc_touched_total"]
                )

                # -------------------------
                # COSTRUZIONE RIGA FINALE
                # -------------------------
                row = {
                    "project": project_name,
                    "release": release,
                    "class": class_id,

                    # metriche locali alla release
                    "loc": loc,
                    "churn": current_churn,
                    "loc_added": loc_added,
                    "fan_out": fan_out,

                    # metriche cumulative fino a questa release
                    "revisions": agg_snapshot["revisions"],
                    "max_churn": agg_snapshot["max_churn"],
                    "max_loc_added": agg_snapshot["max_loc_added"],
                    "avg_churn": agg_snapshot["avg_churn"],
                    "avg_loc_added": agg_snapshot["avg_loc_added"],
                    "fan_in_total": agg_snapshot["fan_in_total"],
                    "loc_touched_total": agg_snapshot["loc_touched_total"],
                    "revisions_density": agg_snapshot["revisions_density"],
                    "ns": agg_snapshot["ns"],

                    # metriche Git / temporali fino a questa release
                    "age": git_snapshot["age"],
                    "weighted_age": git_snapshot["weighted_age"],
                    "nauth": git_snapshot["nauth"],
                    "nfix": git_snapshot["nfix"],
                    "ndev": git_snapshot["ndev"],

                    # metriche derivate
                    "bug_density": git_snapshot["bug_density"],
                    "fix": git_snapshot["fix"],

                    # label finale
                    "buggy": "NO"
                }

                dataset_rows.append(row)

                # ✅ aggiorno la history solo dopo aver calcolato i delta
                file_history[class_id] = new_lines

    print("\n✅ Dataset completo generato")
    return dataset_rows


if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    target = os.path.abspath(os.path.join(BASE_DIR, "..", "releases"))
    repo = os.path.abspath(os.path.join(BASE_DIR, "..", "storm"))

    rows = create_dataset(target, repo)
    export_csv_rows(rows)
