import subprocess
import re


# ✅ FUNZIONE CENTRALIZZATA PER GIT (fix encoding definitivo)
def run_git_command(cmd, cwd):
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore"
    )
    return result.stdout


def estrai_linee_sorgente(file_aperto):

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


def get_authors(repo_path, file_path):

    cmd = ["git", "log", "--format=%an", "--", file_path]

    output = run_git_command(cmd, repo_path)

    authors = set(output.splitlines())

    return len(authors)


def extract_project_dependencies(file_content):

    pattern = re.compile(r"^\s*import\s+(?:static\s+)?([\w\.]+)\s*;")
    dependencies = set()

    for line in file_content:
        match = pattern.match(line)
        if match:
            full_import = match.group(1)

            if full_import.startswith(("java.", "javax.", "sun.")):
                continue

            class_name = full_import.split('.')[-1]
            dependencies.add(class_name.strip())

    return dependencies


def get_nfix(repo_path, file_path):

    cmd = ["git", "log", "--grep=fix", "--format=%H", "--", file_path]

    output = run_git_command(cmd, repo_path)

    return len(output.splitlines())


def ottieni_timestamp_git(comando_git, cwd):

    try:
        output = run_git_command(comando_git, cwd)

        righe = output.strip().split('\n')

        if righe and righe[0]:
            return int(righe[0])

    except Exception:
        pass

    return None