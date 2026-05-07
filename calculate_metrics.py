"""
Data: 28/04/2026
Autore: enrico_barbatano

Main per la costruzione del dataset di metriche software.

Descrizione generale:
Questo script rappresenta l'orchestratore principale del processo di estrazione
delle metriche dal codice sorgente organizzato in release.

Il main NON implementa direttamente le metriche, ma delega il calcolo
ai moduli specializzati (evolution_metrics, aggregate_metrics, ecc.),
garantendo:
- modularità
- riusabilità
- separazione delle responsabilità

Workflow:
1. Scansione delle release in ordine temporale
2. Lettura dei file Java
3. Calcolo metriche base (LOC, churn, loc_added)
4. Aggiornamento metriche evolutive
5. Estrazione dipendenze (fan-in / fan-out)
6. Calcolo metriche temporali (Age)
7. Calcolo metriche aggregate e derivate
8. Costruzione dataset finale

Obiettivo:
Costruire un dataset completo per modelli di defect prediction.
"""

import os

# --- IMPORT METRICHE BASE ---
from metrics_scripts import size as sm
from metrics_scripts import churn
from metrics_scripts import LOC_Added as L_A
from metrics_scripts.fan_in_out import FanInOut

# --- IMPORT MODULI METRICHE ---
from metrics_scripts import evolution_metrics as evo
from metrics_scripts import aggregate_metrics as agg
from metrics_scripts import derived_metrics as der
from metrics_scripts import git_metrics as gitm


# Dizionario globale che conterrà tutte le metriche per ogni classe
metrics = {}


def create_dataset(directory_path, repo_path=None):
    """
    Funzione principale per la costruzione del dataset.

    Parametri:
    - directory_path: cartella contenente le release del progetto
    - repo_path: (opzionale) path del repository Git per metriche storiche

    Restituisce:
    - dizionario contenente tutte le metriche per classe
    """

    # Mantiene lo storico dei file per confronti tra release
    file_history = {}

    # Gestore Fan-In / Fan-Out (dipendenze tra classi)
    fan_io = FanInOut()

    # Ordina le release (importante per evoluzione temporale)
    releases = sorted(os.listdir(directory_path))

    # --- ITERAZIONE SULLE RELEASE ---
    for release in releases:

        current_folder = os.path.join(directory_path, release)

        if not os.path.isdir(current_folder):
            continue

        print(f"\n📂 Processing release: {release}")

        # --- ITERAZIONE SUI FILE ---
        for root, _, files in os.walk(current_folder):
            for file_name in files:

                # Considera solo file Java
                if not file_name.endswith(".java"):
                    continue

                # Percorso completo file
                full_path = os.path.join(root, file_name)

                # Identificatore univoco della classe
                class_id = os.path.relpath(full_path, directory_path)

                # --- INIZIALIZZAZIONE METRICHE ---
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
                        "revisions": 0,
                        "max_loc_added": 0,
                        "avg_churn": 0,
                        "avg_loc_added": 0,
                        "bug_density": 0,
                        "ns": set(),   # temporaneo (insieme subsystem)
                        "ndev": 0,
                        "fix": 0,
                        "loc_touched": 0,
                        "revisions_density": 0
                    }

                # --- LETTURA FILE ---
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    new_lines = f.readlines()

                # Recupera versione precedente (se esiste)
                old_lines = file_history.get(class_id, [])

                # Path relativo (per Git)
                relative_path = os.path.relpath(full_path, current_folder)

                # =========================
                # ✅ CALCOLO METRICHE BASE
                # =========================

                # LOC (SLOC)
                # misura la dimensione e complessità strutturale
                loc = sm.calcola_loc_java(new_lines)

                # CHURN
                # misura linee modificate (instabilità evolutiva)
                current_churn = churn.calcola_churn_sloc(old_lines, new_lines)

                # LOC ADDED
                # misura codice effettivamente aggiunto
                loc_added = L_A.calculate_loc_added(old_lines, new_lines)

                # =========================
                # ✅ METRICHE EVOLUTIVE
                # =========================

                evo.update_churn(metrics, class_id, current_churn)
                evo.update_loc_added(metrics, class_id, loc_added)
                evo.update_revisions(metrics, class_id, old_lines, new_lines)

                # =========================
                # ✅ DIPENDENZE
                # =========================

                # FAN-OUT → dipendenze uscenti
                fan_out, deps = fan_io.compute_fan_out(new_lines)

                # FAN-IN → centralità globale
                fan_io.update_fan_in(class_id, deps)

                # =========================
                # ✅ NS (Subsystem)
                # =========================

                # identifica il modulo del progetto
                subsystem = class_id.split(os.sep)[0]
                metrics[class_id]["ns"].add(subsystem)

                # =========================
                # ✅ AGE (temporale)
                # =========================

                # calcolata solo se disponibile Git
                if repo_path:
                    gitm.update_age(
                        metrics,
                        class_id,
                        repo_path,
                        relative_path,
                        release,
                        current_churn
                    )

                # aggiornamento storico
                file_history[class_id] = new_lines

    # =========================
    # ✅ METRICHE AGGREGATE
    # =========================

    print("\n📊 Calcolo metriche aggregate...")

    # calcolo medie, fan-in, normalizzazioni
    agg.compute_aggregates(metrics, file_history, fan_io)

    # =========================
    # ✅ METRICHE GIT GLOBALI
    # =========================

    print("\n📊 Calcolo metriche Git...")

    gitm.compute_git_metrics(metrics, file_history, repo_path)

    # =========================
    # ✅ METRICHE DERIVATE
    # =========================

    for class_id in metrics:
        loc = sm.calcola_loc_java(file_history.get(class_id, []))

        # bug density, fix flag, ecc.
        der.compute_derived(metrics, class_id, loc)

    print("\n✅ Dataset completato")

    return metrics


if __name__ == "__main__":

    # directory delle release
    target = os.path.abspath("./releases")

    # repository Git (opzionale)
    repo = os.path.abspath("./storm")

    dataset = create_dataset(target, repo)

    # stampa esempio
    for k, v in list(dataset.items())[:5]:
        print(k, v)