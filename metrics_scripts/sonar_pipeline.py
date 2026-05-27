import subprocess
import requests
import json
import os
import time
import pandas as pd


# =====================================================================
# CONFIGURAZIONE
# =====================================================================

SONAR_PROJECT_KEY = "enricobarbatano_storm"
SONAR_ORG = "enricobarbatano"
SONAR_TOKEN = "9f26bdfd1bededb4de0dbb2e28e4fda0f5b971ba"

SONAR_URL = "https://sonarcloud.io/api/issues/search"

DATASET_PATH = "../dataset.csv"
OUTPUT_DATASET = "../dataset_with_smells.csv"
CACHE_FILE = "smells_cache.json"

REPO_PATH = "../storm"


# mapping release → tag
release_to_tag = {
    "release_0.9.0.1": "0.9.0.1",
    "release_0.9.1": "v0.9.1-incubating",
    "release_0.9.2": "v0.9.2-incubating",
    "release_0.9.3": "v0.9.3",
    "release_0.9.4": "v0.9.4",
    "release_0.9.5": "v0.9.5",
    "release_0.9.6": "v0.9.6",
    "release_0.9.7": "v0.9.7",
    "release_0.10.1": "v0.10.1",
    "release_1.0.0": "v1.0.0",
    "release_1.0.1": "v1.0.1",
    "release_1.0.2": "v1.0.2"
}


# =====================================================================
# UTILS
# =====================================================================

def run_cmd(cmd):
    print(f"\n> {cmd}")
    subprocess.run(cmd, shell=True)


def normalize_path(path):
    return path.replace("\\", os.sep).replace("/", os.sep)


# =====================================================================
# STEP 1: SONAR SCAN
# =====================================================================

def run_sonar_scans():
    print("\n=== SONAR SCANS ===")

    os.chdir(REPO_PATH)

    for release, tag in release_to_tag.items():

        print(f"\n🚀 Scan {release} ({tag})")

        run_cmd(f"git checkout {tag}")

        run_cmd(
            f"sonar-scanner "
            f"-Dsonar.projectKey={SONAR_PROJECT_KEY} "
            f"-Dsonar.organization={SONAR_ORG} "
            f"-Dsonar.host.url=https://sonarcloud.io "
            f"-Dsonar.token={SONAR_TOKEN} "
            f"-Dsonar.branch.name={release}"
        )

        time.sleep(5)

    print("\n✅ Sonar scan completate")


# =====================================================================
# STEP 2: FETCH SMELLS (NO BRANCH!)
# =====================================================================

def fetch_all_smells():
    print("\n=== FETCH SMELLS ===")

    params = {
        "projectKeys": SONAR_PROJECT_KEY,
        "types": "CODE_SMELL",
        "ps": 500
    }

    response = requests.get(
        SONAR_URL,
        params=params,
        auth=(SONAR_TOKEN, "")
    )

    if response.status_code != 200:
        print("❌ Errore API Sonar")
        return {}

    data = response.json()
    smells_map = {}

    for issue in data.get("issues", []):
        component = issue.get("component")

        if ":" not in component:
            continue

        file_path = component.split(":")[1]
        file_path = normalize_path(file_path)

        smells_map[file_path] = smells_map.get(file_path, 0) + 1

    print(f"✅ Trovati {len(smells_map)} file con smell")

    # stesso mapping per tutte le release (semplificazione)
    all_data = {release: smells_map for release in release_to_tag}

    with open(CACHE_FILE, "w") as f:
        json.dump(all_data, f, indent=2)

    print(f"✅ Cache salvata: {CACHE_FILE}")

    return all_data


# =====================================================================
# STEP 3: MERGE DATASET + SMELLS
# =====================================================================

def merge_dataset(smells_data):
    print("\n=== MERGE DATASET ===")

    df = pd.read_csv(DATASET_PATH)
    df["code_smells"] = 0

    matched = 0

    for i, row in df.iterrows():

        class_path = normalize_path(row["class"])
        release = row["release"]

        smells_in_release = smells_data.get(release, {})

        count = 0

        for file_path, smell_count in smells_in_release.items():
            file_path = normalize_path(file_path)

            # match principale
            if file_path.endswith(class_path):
                count = smell_count
                matched += 1
                break

            # fallback senza estensione
            if file_path.replace(".java", "").endswith(
                class_path.replace(".java", "")
            ):
                count = smell_count
                matched += 1
                break

        df.at[i, "code_smells"] = count

    print(f"✅ Match trovati: {matched}")

    print("\n📊 Statistiche code_smells:")
    print(df["code_smells"].describe())

    df.to_csv(OUTPUT_DATASET, index=False)

    print(f"\n✅ Dataset finale salvato: {OUTPUT_DATASET}")


# =====================================================================
# PIPELINE COMPLETA
# =====================================================================

def run_pipeline(run_scan=True):

    print("\n🔥 AVVIO PIPELINE COMPLETA")

    # STEP 1 (opzionale)
    if run_scan:
        run_sonar_scans()
    else:
        print("⏭️ Scan saltate")

    # STEP 2
    smells_data = fetch_all_smells()

    # STEP 3
    merge_dataset(smells_data)

    print("\n✅ PIPELINE COMPLETATA")


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    run_pipeline(run_scan=True)  # metti True SOLO la prima volta
