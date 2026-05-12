"""
Metriche basate su Git calcolate fino alla release corrente.
"""

import os
from metrics_scripts import helper as hp
from metrics_scripts.age import calcola_age_e_weighted_age


def compute_fix_flag(nfix):
    """
    FIX:
    - 1 se il file ha almeno un bug fix
    - 0 altrimenti
    """
    return 1 if nfix > 0 else 0


def compute_bug_density(nfix, loc):
    """
    Bug density = nfix / loc
    """
    return nfix / loc if loc > 0 else 0


def compute_git_metrics_for_release(repo_path, class_id, release_name, loc, loc_touched):
    """
    Calcola le metriche Git fino alla release corrente.

    Parametri:
    - repo_path: path del repository Git
    - class_id: path della classe relativo alla release / repository
    - release_name: nome release del dataset (es. release_0.9.1)
    - loc: LOC della classe nella release corrente
    - loc_touched: churn totale fino alla release corrente

    Restituisce un dizionario con:
    - nauth
    - nfix
    - ndev
    - age
    - weighted_age
    - bug_density
    - fix
    """

    if not repo_path or not os.path.exists(os.path.join(repo_path, ".git")):
        return {
            "nauth": 0,
            "nfix": 0,
            "ndev": 0,
            "age": 0,
            "weighted_age": 0,
            "bug_density": 0,
            "fix": 0
        }

    git_ref = hp.resolve_git_ref(repo_path, release_name)
    if not git_ref:
        return {
            "nauth": 0,
            "nfix": 0,
            "ndev": 0,
            "age": 0,
            "weighted_age": 0,
            "bug_density": 0,
            "fix": 0
        }

    relative_path = class_id.replace("\\", "/")

    nauth = hp.get_authors(repo_path, relative_path, git_ref)
    nfix = hp.get_nfix(repo_path, relative_path, git_ref)

    # Nel tuo progetto NDEV è approssimato a NAuth
    ndev = nauth

    age_data = calcola_age_e_weighted_age(
        repo_path,
        relative_path,
        release_name,
        loc_touched
    )

    return {
        "nauth": nauth,
        "nfix": nfix,
        "ndev": ndev,
        "age": age_data["Age_Mesi"],
        "weighted_age": age_data["Weighted_Age"],
        "bug_density": compute_bug_density(nfix, loc),
        "fix": compute_fix_flag(nfix)
    }