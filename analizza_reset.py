import pandas as pd
import re

from metrics_scripts import helper as hp


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


def analyze_resets(dataset_path, repo_path):
    df = pd.read_csv(dataset_path)

    df["order"] = df["release"].apply(lambda r: release_time_key(r, repo_path))

    total_classes = 0
    classes_with_reset = 0

    total_transitions = 0
    reset_transitions = 0

    for cls, group in df.groupby("class"):
        group = group.sort_values("order")
        rows = group.to_dict("records")

        total_classes += 1
        class_has_reset = False

        for i in range(1, len(rows)):
            prev = rows[i - 1]
            curr = rows[i]

            total_transitions += 1

            # condizioni di reset reale
            reset = (
                curr["revisions"] < prev["revisions"]
                or curr["max_churn"] < prev["max_churn"]
                or curr["loc_touched_total"] < prev["loc_touched_total"]
            )

            if reset:
                reset_transitions += 1
                class_has_reset = True

        if class_has_reset:
            classes_with_reset += 1

    print("\n=== RISULTATI ===")

    print(f"\nClassi totali: {total_classes}")
    print(f"Classi con almeno un reset: {classes_with_reset}")
    print(f"% classi affette: {classes_with_reset / total_classes * 100:.2f}%")

    print("\n---")

    print(f"Transizioni totali: {total_transitions}")
    print(f"Transizioni con reset: {reset_transitions}")
    print(f"% transizioni affette: {reset_transitions / total_transitions * 100:.2f}%")
if __name__ == "__main__":
    analyze_resets("dataset.csv", "../storm")