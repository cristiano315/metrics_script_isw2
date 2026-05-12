import pandas as pd
import random
import re

from metrics_scripts import helper as hp


# -----------------------------
# ORDINAMENTO RELEASE
# -----------------------------
def version_key(release_name):
    try:
        v = release_name.replace("release_", "")
        v = re.split(r"[-_]", v)[0]
        return [int(x) for x in v.split(".")]
    except:
        return [0]


def release_time_key(release_name, repo_path):
    git_ref = hp.resolve_git_ref(repo_path, release_name)
    if not git_ref:
        return version_key(release_name)

    ts = hp.get_ref_timestamp(repo_path, git_ref)
    return ts if ts is not None else version_key(release_name)


# -----------------------------
# ANALISI DATASET (STATISTICA)
# -----------------------------
def analyze_dataset(df, repo_path, n_samples=100, print_examples=True):
    classes = df["class"].unique()
    sampled_classes = random.sample(list(classes), min(n_samples, len(classes)))

    print(f"\nClassi analizzate: {len(sampled_classes)}")

    # contatori globali
    total_transitions = 0

    errors = {
        "rev_decrease": 0,
        "max_churn_decrease": 0,
        "loc_total_decrease": 0,
        "fan_in_decrease": 0,
        "loc_added_gt_churn": 0,
        "churn_inconsistency": 0,
    }

    examples_printed = 0

    for cls in sampled_classes:
        group = df[df["class"] == cls].copy()

        group["order"] = group["release"].apply(lambda r: release_time_key(r, repo_path))
        group = group.sort_values("order")

        rows = group.to_dict("records")

        for i in range(1, len(rows)):
            prev = rows[i - 1]
            curr = rows[i]

            total_transitions += 1

            has_error = False

            # controlli veri
            if curr["revisions"] < prev["revisions"]:
                errors["rev_decrease"] += 1
                has_error = True

            if curr["max_churn"] < prev["max_churn"]:
                errors["max_churn_decrease"] += 1
                has_error = True

            if curr["loc_touched_total"] < prev["loc_touched_total"]:
                errors["loc_total_decrease"] += 1
                has_error = True

            if curr["fan_in_total"] < prev["fan_in_total"]:
                errors["fan_in_decrease"] += 1
                has_error = True

            if curr["loc_added"] > curr["churn"]:
                errors["loc_added_gt_churn"] += 1
                has_error = True

            if curr["churn"] == 0 and curr["loc"] != prev["loc"]:
                errors["churn_inconsistency"] += 1
                has_error = True

            # stampa pochi esempi utili
            if has_error and print_examples and examples_printed < 5:
                print("\n⚠️ ESEMPIO PROBLEMA:")
                print(f"Classe: {cls}")
                print(f"{prev['release']} -> {curr['release']}")
                print(f"rev: {prev['revisions']} → {curr['revisions']}")
                print(f"max_churn: {prev['max_churn']} → {curr['max_churn']}")
                print(f"loc_total: {prev['loc_touched_total']} → {curr['loc_touched_total']}")
                examples_printed += 1

    # -----------------------------
    # PRINT RISULTATI
    # -----------------------------
    print("\n=== RISULTATI ANALISI ===")
    print(f"Transizioni analizzate: {total_transitions}")

    if total_transitions == 0:
        print("⚠️ Nessuna transizione trovata")
        return

    for key, value in errors.items():
        perc = (value / total_transitions) * 100
        print(f"{key}: {value} ({perc:.2f}%)")

    total_errors = sum(errors.values())
    perc_total = (total_errors / total_transitions) * 100

    print("\n---")
    print(f"Errori totali: {total_errors} ({perc_total:.2f}%)")

    print("\nNOTE:")
    print("- Una parte degli errori è dovuta ai branch Git (attesi)")
    print("- Percentuali sotto ~5% sono perfettamente accettabili")


# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    dataset = "dataset.csv"
    repo = "../storm"

    df = pd.read_csv(dataset)

    # 👉 CAMBIA QUI se vuoi più sicurezza
    analyze_dataset(df, repo, n_samples=300)