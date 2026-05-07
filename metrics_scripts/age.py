import subprocess
import os
from metrics_scripts import helper as hp
from datetime import datetime


def calcola_age_e_weighted_age(percorso_repo, percorso_file_relativo, tag_release, loc_touched):
    """
    Calcola l'Age (in mesi) e la Weighted Age di un file.
    """
    # 1. Trova la data della release attuale (in UNIX timestamp)
    # Comando: git log -1 --format=%at <tag_release>
    cmd_release_date = ["git", "log", "-1", "--format=%at", tag_release]
    timestamp_release = hp.ottieni_timestamp_git(cmd_release_date, percorso_repo)

    # 2. Trova la data di creazione del file (il commit più vecchio per quel file)
    # Comando: git log --reverse --format=%at -- <file>
    cmd_creation_date = ["git", "log", "--reverse", "--format=%at", "--", percorso_file_relativo]
    timestamp_creazione = hp.ottieni_timestamp_git(cmd_creation_date, percorso_repo)

    # Gestione errori se il file non è tracciato o appena creato
    if not timestamp_release or not timestamp_creazione:
        return {"Age_Mesi": 0, "Weighted_Age": 0}

    # Se il file è stato creato in questa esatta release, l'età è 0
    if timestamp_creazione >= timestamp_release:
        return {"Age_Mesi": 0, "Weighted_Age": 0}

    # 3. Calcolo dell'Age in Mesi
    # Differenza in secondi, convertita in mesi (approssimando 1 mese = 30 giorni = 2592000 secondi)
    differenza_secondi = timestamp_release - timestamp_creazione
    age_mesi = differenza_secondi / 2592000.0 

    # 4. Calcolo della Weighted Age
    weighted_age = age_mesi * loc_touched

    return {
        "Age_Mesi": round(age_mesi, 2), # Arrotondiamo a 2 decimali
        "Weighted_Age": round(weighted_age, 2)
    }

# --- ESEMPIO DI UTILIZZO ---
if __name__ == "__main__":
    
    # ATTENZIONE: Questo script deve essere eseguito dentro o puntando a un VERO repository Git locale
    # (Non una cartella da cui hai cancellato .git!)
    CARTELLA_REPO = "./storm" # La cartella principale clonata col .git intatto
    FILE_DA_ANALIZZARE = "storm-client/src/jvm/org/apache/storm/Config.java" # Percorso relativo
    RELEASE_ATTUALE = "v2.6.0"
    
    # Immagina di aver calcolato questo valore con lo script del Churn precedente
    LOC_TOUCHED_CALCOLATE = 150 
    
    if os.path.exists(os.path.join(CARTELLA_REPO, ".git")):
        risultato = calcola_age_e_weighted_age(
            CARTELLA_REPO, 
            FILE_DA_ANALIZZARE, 
            RELEASE_ATTUALE, 
            LOC_TOUCHED_CALCOLATE
        )
        
        print("📊 Statistiche Temporali:")
        print(f"- Età del file (Age):    {risultato['Age_Mesi']} mesi")
        print(f"- LOC Touched (Churn):   {LOC_TOUCHED_CALCOLATE} righe")
        print(f"🔥 Età Pesata (Weighted): {risultato['Weighted_Age']}")
    else:
        print("❌ Per calcolare l'età serve la cronologia Git! Usa un repository intero, non uno shallow clone.")