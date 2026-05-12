import subprocess
import re


def run_git_command(cmd, cwd):
    """
    Esegue un comando Git e restituisce stdout come stringa.

    Viene forzato l'encoding UTF-8 e ignorati eventuali caratteri non decodificabili
    per evitare errori Unicode su Windows.
    """
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore"
        )
        return result.stdout.strip()
    except Exception:
        return ""


def estrai_linee_sorgente(file_aperto):
    """
    Estrae solo le linee di codice sorgente reale (SLOC) da un file.

    - ignora righe vuote
    - ignora commenti singola linea
    - ignora commenti multilinea
    """

    linee_sorgente = []
    in_multiline_comment = False

    for riga in file_aperto:
        riga_pulita = riga.strip()

        if not riga_pulita:
            continue

        if in_multiline_comment:
            if "*/" in riga_pulita:
                in_multiline_comment = False
            continue

        if riga_pulita.startswith("/*"):
            if "*/" not in riga_pulita:
                in_multiline_comment = True
            continue

        if riga_pulita.startswith("//"):
            continue

        linee_sorgente.append(riga)

    return linee_sorgente


def extract_project_dependencies(file_content):
    """
    Estrae le dipendenze di progetto da un file Java leggendo le direttive import.

    Esclude le librerie standard:
    - java.*
    - javax.*
    - sun.*

    Restituisce:
    - set di nomi classe dipendenti (senza duplicati)
    """
    pattern = re.compile(r"^\s*import\s+(?:static\s+)?([\w\.]+)\s*;")
    dependencies = set()

    for line in file_content:
        match = pattern.match(line)
        if match:
            full_import = match.group(1)

            if full_import.startswith(("java.", "javax.", "sun.")):
                continue

            class_name = full_import.split(".")[-1].strip()
            if class_name:
                dependencies.add(class_name)

    return dependencies


def resolve_git_ref(repo_path, release_name):
    """
    Mappa il nome della release locale (es. release_0.9.1)
    al tag Git reale.

    Tenta, in ordine:
    - 0.9.1
    - v0.9.1
    - 0.9.1-incubating
    - v0.9.1-incubating
    """

    v = release_name.replace("release_", "")

    candidates = [
        v,
        f"v{v}",
        f"{v}-incubating",
        f"v{v}-incubating"
    ]

    for ref in candidates:
        out = run_git_command(["git", "rev-parse", "--verify", ref], repo_path)
        if out:
            return ref

    return None


def get_authors(repo_path, file_path, git_ref=None):
    """
    Calcola NAuth:
    numero di autori distinti che hanno modificato il file
    fino al ref Git specificato.
    """

    cmd = ["git", "log", "--format=%an"]
    if git_ref:
        cmd.append(git_ref)
    cmd.extend(["--", file_path])

    out = run_git_command(cmd, repo_path)
    if not out:
        return 0

    authors = set(out.splitlines())
    return len(authors)


def get_nfix(repo_path, file_path, git_ref=None):
    """
    Calcola NFix:
    numero di commit di fix che coinvolgono il file
    fino al ref Git specificato.
    """

    cmd = ["git", "log", "--regexp-ignore-case", "--grep=fix", "--format=%H"]
    if git_ref:
        cmd.append(git_ref)
    cmd.extend(["--", file_path])

    out = run_git_command(cmd, repo_path)
    if not out:
        return 0

    return len(out.splitlines())

def get_ref_timestamp(repo_path, git_ref):
    """
    Restituisce il timestamp del commit puntato dal tag/ref Git.
    """
    cmd = ["git", "log", "-1", "--format=%at", git_ref]
    return ottieni_timestamp_git(cmd, repo_path)

def ottieni_timestamp_git(comando_git, cwd):
    """
    Esegue un comando Git che restituisce un timestamp UNIX
    e ne estrae il primo valore.
    """
    try:
        out = run_git_command(comando_git, cwd)
        if not out:
            return None

        righe = out.splitlines()
        if righe and righe[0]:
            return int(righe[0])

    except Exception:
        pass

    return None