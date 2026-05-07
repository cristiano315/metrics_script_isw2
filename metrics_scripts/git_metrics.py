"""
Metriche basate su Git:
- NAuth
- NFix
- NDEV
- Age
"""

import os
from metrics_scripts import helper as hp
from metrics_scripts.age import calcola_age_e_weighted_age


def compute_git_metrics(metrics, repo_path):

    if not repo_path or not os.path.exists(os.path.join(repo_path, ".git")):
        print(" non trova il path per calcolare le metriche da git")
        return

    for class_id in metrics:
        try:
            relative_path = class_id

            nauth = hp.get_authors(repo_path, relative_path)
            nfix = hp.get_nfix(repo_path, relative_path)

            metrics[class_id]["nauth"] = nauth
            metrics[class_id]["ndev"] = nauth   # approssimazione
            metrics[class_id]["nfix"] = nfix

        except Exception:
            metrics[class_id]["nauth"] = 0
            metrics[class_id]["ndev"] = 0
            metrics[class_id]["nfix"] = 0
def update_age(metrics, class_id, repo_path, release, churn):

    relative_path = class_id.replace("\\", "/")

    age_data = calcola_age_e_weighted_age(
        repo_path,
        relative_path,
        churn
    )

    metrics[class_id]["age"] = age_data["Age_Mesi"]
    metrics[class_id]["weighted_age"] = age_data["Weighted_Age"]