import os
import subprocess
import time
import requests
import csv
import pandas as pd

# ==========================================
# CONFIGURAZIONI
# ==========================================
SONAR_URL = "http://localhost:9000"
SONAR_TOKEN = "squ_97ae2ccbd620d0fb04bbb2a3cecee27d39e345d0"
PROJECT_KEY = "apache-syncope-history"
RELEASES_DIR = "./syncope_java_releases" # Usa il tuo percorso reale
CSV_FILENAME = "storico_smells_classi.csv"
CSV_ESISTENTE = "dataset.csv"

def run_sonar_scanner(source_dir, version):
    """Compila il codice con Maven ed esegue SonarScanner."""
    # --- FASE 1: COMPILAZIONE MAVEN ---
    print(f"\n[{version}] 1a. Compilazione codice con Maven...")
    
    # Aggiungi questa riga per gestire l'estensione su Windows
    mvn_executable = "mvn.cmd" if os.name == 'nt' else "mvn"
    
    # Usa la variabile mvn_executable al posto della stringa "mvn"
    mvn_cmd = [mvn_executable, "clean", "compile", "-DskipTests"] 
    
    try:
        subprocess.run(mvn_cmd, cwd=source_dir, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        print(f"[{version}] Compilazione completata.")
    except subprocess.CalledProcessError:
        print(f"[{version}] ATTENZIONE: Compilazione Maven fallita parzialmente.")

    print(f"[{version}] 1b. Avvio analisi SonarScanner...")
    sonar_cmd = "sonar-scanner.bat" if os.name == 'nt' else "sonar-scanner"
    
    cmd = [
        sonar_cmd,
        f"-Dsonar.projectKey={PROJECT_KEY}",
        f"-Dsonar.host.url={SONAR_URL}",
        f"-Dsonar.login={SONAR_TOKEN}",
        f"-Dsonar.projectVersion={version}",
        f"-Dsonar.sources=.",
        "-Dsonar.java.binaries=**/target/classes,.",
        
        # --- NUOVE RIGHE "NUCLEARI" ---
        "-Dsonar.inclusions=**/*.java",           # FORZA la lettura di tutti i file .java
        "-Dsonar.scm.exclusions.disabled=true"    # DISABILITA i file .gitignore che potrebbero bloccare la lettura
    ]
    
    try:
        subprocess.run(cmd, cwd=source_dir, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        
        report_path = os.path.join(source_dir, ".scannerwork", "report-task.txt")
        with open(report_path, "r") as f:
            for line in f:
                if line.startswith("ceTaskId="):
                    task_id = line.strip().split("=")[1]
                    print(f"[{version}] Analisi inviata. Task ID: {task_id}")
                    return task_id
        return None
    except Exception as e:
        print(f"[{version}] Errore durante l'esecuzione di SonarScanner: {e}")
        return None

def wait_for_task_completion(task_id, version):
    """Attende che SonarQube finisca di elaborare il report."""
    print(f"[{version}] 2. Attesa elaborazione server (polling API)...", end="", flush=True)
    url = f"{SONAR_URL}/api/ce/task"
    params = {"id": task_id}
    
    while True:
        try:
            response = requests.get(url, params=params, auth=(SONAR_TOKEN, ""))
            if response.status_code == 200:
                status = response.json().get('task', {}).get('status')
                if status == 'SUCCESS':
                    print(" Completato!")
                    return True
                elif status in ['FAILED', 'CANCELED']:
                    print(f" Fallito con stato: {status}")
                    return False
                else:
                    print(".", end="", flush=True)
                    time.sleep(2)
            else:
                print(f" Errore API: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f" Errore connessione: {e}")
            return False

def get_all_classes_smells(version):
    """Estrae i code smells per ogni singolo file Java usando la paginazione."""
    print(f"[{version}] 3. Estrazione smells per singola classe...")
    files_data = []
    page = 1
    page_size = 500 # SonarQube permette massimo 500 risultati per pagina
    
    while True:
        url = f"{SONAR_URL}/api/measures/component_tree"
        params = {
            "component": PROJECT_KEY,
            "metricKeys": "code_smells",
            "qualifiers": "FIL", # FIL = Files (ignora cartelle e moduli)
            "p": page,
            "ps": page_size
        }
        
        response = requests.get(url, params=params, auth=(SONAR_TOKEN, ""))
        if response.status_code == 200:
            data = response.json()
            components = data.get('components', [])
            
            if not components:
                break # Nessun componente trovato in questa pagina, esci dal ciclo
                
            for comp in components:
                file_path = comp.get('path', 'Sconosciuto')
                
                # Vogliamo solo i file Java (SonarQube analizza anche XML, POM, ecc.)
                if not file_path.endswith('.java'):
                    continue
                    
                smell_value = 0
                for measure in comp.get('measures', []):
                    if measure['metric'] == 'code_smells':
                        smell_value = int(measure['value'])
                
                files_data.append([version, file_path, smell_value])
            
            # Gestione della paginazione
            paging = data.get('paging', {})
            total = paging.get('total', 0)
            
            if page * page_size >= total:
                break # Abbiamo letto tutte le pagine
            page += 1
        else:
            print(f"[{version}] Errore API: {response.status_code}")
            break
            
    print(f"[{version}] Trovate {len(files_data)} classi Java.")
    return files_data

def process_all_releases():
    releases = sorted([d for d in os.listdir(RELEASES_DIR) if os.path.isdir(os.path.join(RELEASES_DIR, d))])
    print(f"Trovate {len(releases)} release. Inizio elaborazione...")
    
    # Lista per accumulare tutti i dati estratti in questa sessione
    tutti_i_nuovi_dati = []
    
    for release_name in releases:
        release_path = os.path.join(RELEASES_DIR, release_name)
        
        # Blocco anti-matrioska
        elementi = os.listdir(release_path)
        if len(elementi) == 1 and os.path.isdir(os.path.join(release_path, elementi[0])):
            actual_source_dir = os.path.join(release_path, elementi[0])
        else:
            actual_source_dir = release_path
            
        task_id = run_sonar_scanner(actual_source_dir, release_name)
        
        if task_id:
            success = wait_for_task_completion(task_id, release_name)
            
            if success:
                # Estraiamo i dati: restituisce una lista di liste [Release, Classe_Java, Code_Smells]
                classes_data = get_all_classes_smells(release_name)
                tutti_i_nuovi_dati.extend(classes_data)
                print(f"[{release_name}] Dati estratti e salvati in memoria.\n")
            else:
                print(f"[{release_name}] Saltato a causa di un errore del server.\n")
        break

    # ==========================================
    # FASE FINALE: MERGE CON IL CSV ESISTENTE
    # ==========================================
    print("\nInizio la fusione dei dati con il CSV esistente...")
    
    # 1. Creiamo un DataFrame (tabella) con i dati appena estratti da SonarQube
    df_sonar = pd.DataFrame(tutti_i_nuovi_dati, columns=['release', 'class', 'Code_Smells'])
    # --- NUOVO: NORMALIZZAZIONE DEI PERCORSI ---
    # Sostituiamo tutti gli slash (/) con i backslash (\) nella colonna di SonarQube.
    # Nota: in Python il backslash è un carattere speciale, quindi dobbiamo scriverlo doppio ('\\')
    df_sonar['class'] = df_sonar['class'].str.replace('/', '\\')
    
    # 2. Leggiamo il tuo CSV esistente
    try:
        df_esistente = pd.read_csv(CSV_ESISTENTE)
        
        # 3. Facciamo il "MERGE" (come un JOIN in SQL) basandoci su Release e Nome Classe
        # Usiamo how='left' per mantenere TUTTE le righe del tuo CSV originale
        df_finale = pd.merge(df_esistente, df_sonar, on=['release', 'class'], how='left')
        
        # 4. Salviamo il risultato sovrascrivendo il file (o creandone uno nuovo)
        df_finale.to_csv(CSV_ESISTENTE, index=False)
        print(f"✅ Finito! La colonna 'Code_Smells' è stata aggiunta a '{CSV_ESISTENTE}'")
        
    except FileNotFoundError:
        print(f"❌ Errore: Non trovo il file '{CSV_ESISTENTE}'.")
        print("Salvo i risultati in un nuovo file per non perdere i dati...")
        df_sonar.to_csv("salvataggio_emergenza_smells.csv", index=False)

if __name__ == "__main__":
    process_all_releases()
    print(f"ELABORAZIONE COMPLETATA! Apri '{CSV_FILENAME}' per vedere i risultati.")