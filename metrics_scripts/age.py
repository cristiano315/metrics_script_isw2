from metrics_scripts import helper as hp


def calcola_age_e_weighted_age(percorso_repo, percorso_file_relativo, release_name, loc_touched):
    """
    Calcola:
    - Age: età del file (in mesi) fino alla release corrente
    - Weighted Age: age * loc_touched

    Parametri:
    - percorso_repo: path del repository Git
    - percorso_file_relativo: path del file relativo al repo
    - release_name: nome della release del dataset (es. release_0.9.1)
    - loc_touched: churn totale fino a quella release
    """

    # Risolve il nome release nel tag Git reale
    git_ref = hp.resolve_git_ref(percorso_repo, release_name)
    if not git_ref:
        return {"Age_Mesi": 0, "Weighted_Age": 0}

    # Timestamp della release corrente
    cmd_release_date = ["git", "log", "-1", "--format=%at", git_ref]
    timestamp_release = hp.ottieni_timestamp_git(cmd_release_date, percorso_repo)

    # Timestamp di creazione del file fino a quella release
    cmd_creation_date = [
        "git", "log", "--reverse", "--format=%at", git_ref,
        "--", percorso_file_relativo
    ]
    timestamp_creazione = hp.ottieni_timestamp_git(cmd_creation_date, percorso_repo)

    if timestamp_release is None or timestamp_creazione is None:
        return {"Age_Mesi": 0, "Weighted_Age": 0}

    if timestamp_creazione >= timestamp_release:
        return {"Age_Mesi": 0, "Weighted_Age": 0}

    differenza_secondi = timestamp_release - timestamp_creazione
    age_mesi = differenza_secondi / 2592000.0

    weighted_age = age_mesi * loc_touched

    return {
        "Age_Mesi": round(age_mesi, 2),
        "Weighted_Age": round(weighted_age, 2)
    }
