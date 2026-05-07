import subprocess
import requests
import json
import os
import time

# ✅ CONFIGURA QUI
SONAR_PROJECT_KEY = "TUO_PROJECT_KEY"
SONAR_TOKEN = "TUO_TOKEN"
SONAR_URL = "https://sonarcloud.io/api/issues/search"

# ✅ mapping precise release → tag
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


# ✅ esegue comando shell
def run_cmd(cmd):
    subprocess.run(cmd, shell=True)


# ✅ esegue sonar per tutte le release
def run_sonar_scans(repo_path):

    os.chdir(repo_path)

    for release, tag in release_to_tag.items():

        print(f"\n🚀 Scan {release} ({tag})")

        run_cmd(f"git checkout {tag}")

        run_cmd(
            f"sonar-scanner "
            f"-Dsonar.projectKey={SONAR_PROJECT_KEY} "
            f"-Dsonar.projectVersion={release}"
        )

        time.sleep(5)  # evita rate limit


# ✅ recupera smells per release
def fetch_smells_for_release(release):

    params = {
        "projectKeys": SONAR_PROJECT_KEY,
        "types": "CODE_SMELL",
        "branch": release,
        "ps": 500
    }

    response = requests.get(
        SONAR_URL,
        params=params,
        auth=(SONAR_TOKEN, "")
    )

    if response.status_code != 200:
        print(f"❌ errore per {release}")
        return {}

    data = response.json()

    smells_map = {}

    for issue in data.get("issues", []):

        component = issue.get("component")

        if ":" not in component:
            continue

        file_path = component.split(":")[1]

        # ✅ normalizza path
        file_path = file_path.replace("/", os.sep)

        if file_path not in smells_map:
            smells_map[file_path] = 0

        smells_map[file_path] += 1

    return smells_map


# ✅ genera cache JSON (IMPORTANTISSIMO)
def build_smells_cache(output_file="smells_cache.json"):

    all_data = {}

    for release in release_to_tag:

        print(f"\n📊 Download smells {release}")

        smells = fetch_smells_for_release(release)

        all_data[release] = smells

        time.sleep(2)

    with open(output_file, "w") as f:
        json.dump(all_data, f, indent=2)

    print(f"\n✅ Cache salvata: {output_file}")


# ✅ load cache
def load_cache(file="smells_cache.json"):
    if not os.path.exists(file):
        return {}

    with open(file, "r") as f:
        return json.load(f)