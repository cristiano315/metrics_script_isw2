import subprocess
import re


def estrai_linee_sorgente(file_aperto):
    """
    Estrae le linee di codice sorgente reale (SLOC) da un file.

    Descrizione:
    - Rimuove righe vuote
    - Rimuove commenti singola linea (//)
    - Rimuove commenti multilinea (/* ... */)

    Scopo:
    - Utilizzata per ottenere una rappresentazione "pulita" del codice
    - Fondamentale per il calcolo di Churn e LOC Added basati su codice effettivo
    - Evita rumore dovuto a commenti o spazi vuoti

    Restituisce:
    - Lista di righe di codice sorgente (conservando formattazione originale)
    """

    linee_sorgente = []
    in_multiline_comment = False

    for riga in file_aperto:
        riga_pulita = riga.strip()

        # --- 1. Ignora righe vuote ---
        if not riga_pulita:
            continue

        # --- 2. Se siamo dentro un commento multilinea ---
        if in_multiline_comment:
            if "*/" in riga_pulita:
                in_multiline_comment = False
            continue

        # --- 3. Inizio commento multilinea ---
        if riga_pulita.startswith("/*"):
            if "*/" not in riga_pulita:
                in_multiline_comment = True
            continue

        # --- 4. Commento singola linea ---
        if riga_pulita.startswith("//"):
            continue

        # --- Codice valido ---
        linee_sorgente.append(riga)

    return linee_sorgente


def get_authors(repo_path, file_path):
    """
    Calcola il numero di autori distinti (NAuth) che hanno modificato un file.

    Metodo:
    - Usa il comando Git: git log --format=%an
    - Estrae i nomi degli autori
    - Utilizza un set per eliminare duplicati

    Scopo:
    - Misura la frammentazione della responsabilità del codice
    - Più autori → maggiore complessità organizzativa → più bug

    Parametri:
    - repo_path: percorso del repository Git
    - file_path: percorso del file nel repository

    Restituisce:
    - Numero di sviluppatori distinti
    """

    cmd = ["git", "log", "--format=%an", "--", file_path]

    result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True)

    authors = set(result.stdout.splitlines())

    return len(authors)


def extract_project_dependencies(file_content):
    """
    Estrae le dipendenze (Fan-Out) di un file Java.

    Metodo:
    - Analizza le istruzioni import
    - Esclude librerie standard (java.*, javax.*, sun.*)
    - Restituisce il nome delle classi importate (senza path completo)

    Scopo:
    - Base per calcolo Fan-Out
    - Identifica accoppiamento tra classi

    Parametri:
    - file_content: lista di righe del file

    Restituisce:
    - Set di classi dipendenti (senza duplicati)
    """

    pattern = re.compile(r"^\s*import\s+(?:static\s+)?([\w\.]+)\s*;")
    dependencies = set()

    for line in file_content:
        match = pattern.match(line)
        if match:
            full_import = match.group(1)

            # Esclude librerie standard Java
            if full_import.startswith(("java.", "javax.", "sun.")):
                continue

            # Estrae nome classe
            class_name = full_import.split('.')[-1]
            dependencies.add(class_name)

    return dependencies


def get_nfix(repo_path, file_path):
    """
    Calcola il numero di bug fix (NFix) associati a un file.

    Metodo:
    - Usa git log con filtro "--grep=fix"
    - Conta i commit contenenti la parola "fix"

    Scopo:
    - Identificare classi già coinvolte in bug fix
    - Basato sul principio: "bug-prone modules tend to stay bug-prone"

    Parametri:
    - repo_path: repository Git
    - file_path: percorso file

    Restituisce:
    - Numero di commit di fix
    """

    cmd = ["git", "log", "--grep=fix", "--format=%H", "--", file_path]

    result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True)

    return len(result.stdout.splitlines())


def ottieni_timestamp_git(comando_git, cwd):
    """
    Esegue un comando Git e restituisce il timestamp (UNIX) risultante.

    Metodo:
    - Esegue un comando git tramite subprocess
    - Estrae la prima riga dell'output
    - Converte in intero

    Scopo:
    - Utilizzato per calcolare Age e Weighted Age
    - Permette di ottenere:
        • data di creazione file
        • data release

    Parametri:
    - comando_git: lista del comando Git
    - cwd: directory di esecuzione

    Restituisce:
    - Timestamp UNIX (int) oppure None in caso di errore
    """

    try:
        risultato = subprocess.run(
            comando_git,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True
        )

        righe = risultato.stdout.strip().split('\n')

        if righe and righe[0]:
            return int(righe[0])

    except (subprocess.CalledProcessError, ValueError):
        pass

    return None