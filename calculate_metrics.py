import os
import csv
import re

from metrics_scripts import size as sm
from metrics_scripts import churn
from metrics_scripts import LOC_Added as L_A
from metrics_scripts.fan_in_out import FanInOut

from metrics_scripts import evolution_metrics as evo
from metrics_scripts import aggregate_metrics as agg
from metrics_scripts import derived_metrics as der
from metrics_scripts import git_metrics as gitm


metrics = {}
tries = 1 


# ✅ NORMALIZZAZIONE VERSIONI (LA PARTE IMPORTANTE)
def version_key(release_name):
    """
    Ordina correttamente le release tipo:
    release_0.9.1-incubating -> [0,9,1]
    """

    # rimuove prefisso
    v = release_name.replace("release_", "")

    # rimuove suffissi tipo -incubating
    v = re.split(r"[-_]", v)[0]

    try:
        return [int(x) for x in v.split(".")]
    except:
        return [0]


# ✅ CSV EXPORT
def export_csv_rows(rows, output_path="../dataset.csv"):

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

    file_history = {}
    fan_io = FanInOut()

    # ✅ ORDINAMENTO CORRETTO
    releases = sorted(os.listdir(directory_path), key=version_key)

    print("\n✅ Release ordinate correttamente:")
    for r in releases:
        print(r)

    project_name = os.path.basename(repo_path) if repo_path else "unknown"

    seen_pairs = set()
    per_release_data = []

    # =========================
    # SCAN RELEASE
    # =========================
    attempt = 0
    for release in releases:

        current_folder = os.path.join(directory_path, release)
        if not os.path.isdir(current_folder):
            continue

        print(f"\n📂 Processing release: {release}")

        for root, _, files in os.walk(current_folder):
            for file_name in files:

                if not file_name.endswith(".java"):
                    continue

                full_path = os.path.join(root, file_name)
                class_id = os.path.relpath(full_path, directory_path)

                # ✅ evita duplicati
                pair_key = (release, class_id)
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)

                if class_id not in metrics:
                    metrics[class_id] = {
                        "Churn_Totale": 0,
                        "max_churn": 0,
                        "loc_added_total": 0,
                        "fan_in": 0,
                        "age": 0,
                        "weighted_age": 0,
                        "nauth": 0,
                        "nfix": 0,
                        "nfix_total": 0,
                        "revisions": 0,
                        "max_loc_added": 0,
                        "avg_churn": 0,
                        "avg_loc_added": 0,
                        "bug_density": 0,
                        "ns": set(),
                        "ndev": 0,
                        "fix": 0,
                        "loc_touched": 0,
                        "revisions_density": 0,
                        "nauth_total": 0,
                    }

                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    new_lines = f.readlines()

                old_lines = file_history.get(class_id, [])

                relative_path = os.path.relpath(full_path, current_folder)

                # --- BASE ---
                loc = sm.calcola_loc_java(new_lines)
                current_churn = churn.calcola_churn_sloc(old_lines, new_lines)
                loc_added = L_A.calculate_loc_added(old_lines, new_lines)

                # --- EVOLUZIONE ---
                evo.update_churn(metrics, class_id, current_churn)
                evo.update_loc_added(metrics, class_id, loc_added)
                evo.update_revisions(metrics, class_id, old_lines, new_lines)

                # --- FAN ---
                fan_out, deps = fan_io.compute_fan_out(new_lines)
                fan_io.update_fan_in(class_id, deps)

                # --- NS ---
                subsystem = class_id.split(os.sep)[0]
                metrics[class_id]["ns"].add(subsystem)

                # --- AGE ---
                if repo_path:
                    gitm.update_age(metrics, class_id, repo_path, relative_path, release, current_churn)

                file_history[class_id] = new_lines

                # ✅ SALVO DATI BASE PER CSV
                per_release_data.append({
                    "project": project_name,
                    "release": release,
                    "class": class_id,
                    "loc": loc,
                    "churn": current_churn,
                    "loc_added": loc_added,
                    "fan_out": fan_out
                })
        attempt += 1
        if attempt == 1:
            break

    # =========================
    # POST PROCESS
    # =========================

    print("\n📊 Calcolo metriche aggregate...")
    agg.compute_aggregates(metrics, file_history, fan_io)

    print("\n📊 Calcolo metriche Git...")
    gitm.compute_git_metrics(metrics, file_history, repo_path)

    for class_id in metrics:
        loc = sm.calcola_loc_java(file_history.get(class_id, []))
        der.compute_derived(metrics, class_id, loc)

    # =========================
    # COSTRUZIONE CSV FINALE
    # =========================

    dataset_rows = []

    for entry in per_release_data:
        class_id = entry["class"]
        m = metrics[class_id]   

        row = {
            **entry,

            "revisions": m["revisions"],
            "max_churn": m["max_churn"],
            # --- AVERAGE ---
            "avg_churn": m["avg_churn"],

            # --- TOTAL (🔥 naming corretto) ---
            "fan_in_total": m["fan_in"],
            "churn_total": m["Churn_Totale"],
            "loc_added_total": m["loc_added_total"],

            # --- TEMPORAL ---
            "age": m["age"],
            "weighted_age": m["weighted_age"],
            "nauth": m["nauth"],
            "nauth_total": m["nauth_total"],
            "nfix": m["nfix"],

            # --- DERIVED ---
            "bug_density": m["bug_density"],
            "fix": m["fix"],
            "nfix_total": m["nfix_total"],

            # --- STRUCTURE ---
            "ns": m["ns"],
            "revisions_density": m["revisions_density"],
            "fix": m["fix"],

            "buggy": "NO"
        }

        dataset_rows.append(row)

    print("\n✅ Dataset completo generato")

    return dataset_rows


if __name__ == "__main__":

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    target = os.path.abspath(os.path.join(BASE_DIR, "syncope_java_releases"))
    repo = os.path.abspath(os.path.join(BASE_DIR, "syncope"))

    rows = create_dataset(target, repo)

    export_csv_rows(rows)

    print("\n🔍 Sample:")
    for r in rows[:5]:
        print(r)
