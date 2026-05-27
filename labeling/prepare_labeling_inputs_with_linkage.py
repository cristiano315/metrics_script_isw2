import os
import re
import csv
import json
import time
import subprocess
from pathlib import Path

import requests


# =====================================================================
# CONFIG
# =====================================================================

PROJECT_KEY = "SYNCOPE"

TICKETS_FILE = r"C:\Uni\ISW2\Progetto\metrics_script\metrics_script_isw2\SYNCOPE_Tickets.txt"

# Repository Git pulito completo di Apache Storm.
# Deve essere una repo git valida.
GIT_REPO_PATH = r"C:\Uni\ISW2\Progetto\metrics_script\metrics_script_isw2\syncope"

OUTPUT_DIR = r"C:\Uni\ISW2\Progetto\metrics_script\metrics_script_isw2\syncope_labeling"

TICKETS_METADATA_CSV = os.path.join(OUTPUT_DIR, "tickets_metadata.csv")
TICKET_COMMITS_CSV = os.path.join(OUTPUT_DIR, "ticket_commits.csv")
TICKET_JAVA_FILES_CSV = os.path.join(OUTPUT_DIR, "ticket_commit_java_files.csv")
JIRA_GITHUB_LINKAGE_CSV = os.path.join(OUTPUT_DIR, "jira_github_linkage.csv")
SUMMARY_JSON = os.path.join(OUTPUT_DIR, "labeling_input_summary.json")
LINKAGE_SUMMARY_JSON = os.path.join(OUTPUT_DIR, "linkage_summary.json")

JIRA_ISSUE_URL = "https://issues.apache.org/jira/rest/api/2/issue/{key}"

JIRA_FIELDS = [
    "key",
    "summary",
    "issuetype",
    "status",
    "resolution",
    "created",
    "resolutiondate",
    "versions",
    "fixVersions"
]

JIRA_SLEEP_SECONDS = 0.10
MAX_RETRIES = 5


# =====================================================================
# UTILS
# =====================================================================

def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def check_git_repo():
    if not os.path.isdir(GIT_REPO_PATH):
        raise FileNotFoundError(f"Repository Git non trovato: {GIT_REPO_PATH}")

    result = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=GIT_REPO_PATH,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    if result.returncode != 0 or result.stdout.strip() != "true":
        raise RuntimeError(
            f"La cartella non sembra una repo Git valida: {GIT_REPO_PATH}"
        )


def read_tickets(path):
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    tickets = re.findall(rf"{PROJECT_KEY}-\d+", text)

    seen = set()
    unique_tickets = []

    for ticket in tickets:
        if ticket not in seen:
            unique_tickets.append(ticket)
            seen.add(ticket)

    return unique_tickets


def jira_get_issue(ticket_key):
    url = JIRA_ISSUE_URL.format(key=ticket_key)
    params = {
        "fields": ",".join(JIRA_FIELDS)
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, params=params, timeout=30)

            if response.status_code == 200:
                return response.json()

            if response.status_code in [429, 500, 502, 503, 504]:
                wait = 10 * attempt
                print(
                    f"⚠️ Jira status {response.status_code} per {ticket_key}. "
                    f"Retry tra {wait}s..."
                )
                time.sleep(wait)
                continue

            print(f"❌ Errore Jira {response.status_code} per {ticket_key}")
            print(response.text[:300])
            return None

        except requests.RequestException as e:
            wait = 10 * attempt
            print(f"⚠️ Eccezione Jira per {ticket_key}: {e}. Retry tra {wait}s...")
            time.sleep(wait)

    print(f"❌ Troppi retry falliti per {ticket_key}")
    return None


def version_names(version_array):
    if not version_array:
        return ""

    names = []

    for version in version_array:
        name = version.get("name")
        if name:
            names.append(name)

    return ";".join(names)


def normalize_date(date_str):
    return date_str or ""


def run_git_command(args):
    try:
        result = subprocess.run(
            args,
            cwd=GIT_REPO_PATH,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

        if result.returncode != 0:
            return ""

        return result.stdout

    except Exception as e:
        print(f"⚠️ Errore eseguendo git: {e}")
        return ""


def is_fix_like_subject(subject):
    """
    Euristica solo descrittiva.
    Non scarta i commit: serve solo per sapere quanti commit sembrano fix.
    """
    s = subject.lower()

    fix_words = [
        "fix",
        "fixed",
        "bug",
        "resolve",
        "resolved",
        "repair",
        "correct",
        "problem",
        "issue",
        "defect"
    ]

    return any(word in s for word in fix_words)


def is_merge_commit(commit_hash):
    """
    Un commit è merge se ha più di un parent.
    git rev-list --parents -n 1 commit restituisce:
      commit parent1              -> non merge
      commit parent1 parent2 ...   -> merge
    """
    output = run_git_command([
        "git",
        "rev-list",
        "--parents",
        "-n",
        "1",
        commit_hash
    ])

    parts = output.strip().split()

    return len(parts) > 2


def find_commits_for_ticket(ticket_key):
    """
    Linkage Jira-Git/GitHub:
    cerca commit che citano STORM-XXXX nel messaggio.
    """
    cmd = [
        "git",
        "log",
        "--all",
        "--regexp-ignore-case",
        f"--grep={ticket_key}",
        "--pretty=format:%H%x1f%ad%x1f%s",
        "--date=iso-strict"
    ]

    output = run_git_command(cmd)

    commits = []

    for line in output.splitlines():
        parts = line.split("\x1f")

        if len(parts) != 3:
            continue

        commit_hash, commit_date, subject = parts
        commit_hash = commit_hash.strip()
        commit_date = commit_date.strip()
        subject = subject.strip()

        merge = is_merge_commit(commit_hash)

        commits.append({
            "ticket": ticket_key,
            "commit_hash": commit_hash,
            "commit_date": commit_date,
            "subject": subject,
            "is_fix_like": is_fix_like_subject(subject),
            "is_merge_commit": merge
        })

    return commits


def get_java_files_modified_by_commit(commit_hash):
    """
    Estrae file .java modificati dal commit.

    Per SZZ il commit è il punto di partenza.
    Il blame verrà fatto nello step successivo.
    """
    cmd = [
        "git",
        "show",
        "--name-only",
        "--pretty=format:",
        "--diff-filter=ACMR",
        commit_hash,
        "--",
        "*.java"
    ]

    output = run_git_command(cmd)

    files = []

    for line in output.splitlines():
        line = line.strip()

        if line.endswith(".java"):
            files.append(line.replace("/", os.sep))

    return sorted(set(files))


def is_valid_bug_fixed(issue_type, status, resolution):
    """
    Coerente con il filtro del professore:
    - issueType == Bug
    - status == Closed oppure Resolved
    - resolution == Fixed
    """
    return (
        issue_type.lower() == "bug"
        and status.lower() in ["closed", "resolved"]
        and resolution.lower() == "fixed"
    )


# =====================================================================
# WRITE CSV / JSON
# =====================================================================

def write_csv(path, fieldnames, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_tickets_metadata(rows):
    fieldnames = [
        "ticket",
        "issue_type",
        "status",
        "resolution",
        "created",
        "resolutiondate",
        "affected_versions",
        "fix_versions",
        "summary"
    ]

    write_csv(TICKETS_METADATA_CSV, fieldnames, rows)


def write_ticket_commits(rows):
    fieldnames = [
        "ticket",
        "commit_hash",
        "commit_date",
        "subject",
        "is_fix_like",
        "is_merge_commit"
    ]

    write_csv(TICKET_COMMITS_CSV, fieldnames, rows)


def write_ticket_java_files(rows):
    fieldnames = [
        "ticket",
        "commit_hash",
        "java_file"
    ]

    write_csv(TICKET_JAVA_FILES_CSV, fieldnames, rows)


def write_linkage(rows):
    fieldnames = [
        "ticket",
        "jira_found",
        "is_valid_bug_fixed",
        "has_affected_versions",
        "has_fix_versions",
        "commits_found",
        "non_merge_commits_found",
        "fix_like_commits_found",
        "java_files_touched",
        "linked_to_git",
        "linked_to_java",
        "usable_for_szz"
    ]

    write_csv(JIRA_GITHUB_LINKAGE_CSV, fieldnames, rows)


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# =====================================================================
# SUMMARY
# =====================================================================

def compute_linkage_summary(linkage_rows):
    tickets_total = len(linkage_rows)

    jira_found = sum(1 for r in linkage_rows if r["jira_found"] == "YES")
    valid_bug_fixed = sum(
        1 for r in linkage_rows if r["is_valid_bug_fixed"] == "YES"
    )
    has_av = sum(1 for r in linkage_rows if r["has_affected_versions"] == "YES")
    has_fv = sum(1 for r in linkage_rows if r["has_fix_versions"] == "YES")
    linked_to_git = sum(1 for r in linkage_rows if r["linked_to_git"] == "YES")
    linked_to_java = sum(1 for r in linkage_rows if r["linked_to_java"] == "YES")
    usable_for_szz = sum(1 for r in linkage_rows if r["usable_for_szz"] == "YES")

    total_commits = sum(int(r["commits_found"]) for r in linkage_rows)
    total_non_merge_commits = sum(
        int(r["non_merge_commits_found"]) for r in linkage_rows
    )
    total_fix_like_commits = sum(
        int(r["fix_like_commits_found"]) for r in linkage_rows
    )
    total_java_files = sum(int(r["java_files_touched"]) for r in linkage_rows)

    def pct(num, den):
        if den == 0:
            return 0.0
        return round((num / den) * 100, 2)

    return {
        "tickets_total": tickets_total,

        "jira_found": jira_found,
        "jira_found_rate_pct": pct(jira_found, tickets_total),

        "valid_bug_fixed": valid_bug_fixed,
        "valid_bug_fixed_rate_pct": pct(valid_bug_fixed, tickets_total),

        "tickets_with_affected_versions": has_av,
        "affected_versions_rate_pct": pct(has_av, tickets_total),

        "tickets_with_fix_versions": has_fv,
        "fix_versions_rate_pct": pct(has_fv, tickets_total),

        "tickets_linked_to_git": linked_to_git,
        "jira_git_linkage_rate_all_tickets_pct": pct(
            linked_to_git,
            tickets_total
        ),
        "jira_git_linkage_rate_valid_bug_fixed_pct": pct(
            linked_to_git,
            valid_bug_fixed
        ),

        "tickets_linked_to_java": linked_to_java,
        "jira_java_linkage_rate_all_tickets_pct": pct(
            linked_to_java,
            tickets_total
        ),
        "jira_java_linkage_rate_valid_bug_fixed_pct": pct(
            linked_to_java,
            valid_bug_fixed
        ),

        "tickets_usable_for_szz": usable_for_szz,
        "usable_for_szz_rate_all_tickets_pct": pct(
            usable_for_szz,
            tickets_total
        ),
        "usable_for_szz_rate_valid_bug_fixed_pct": pct(
            usable_for_szz,
            valid_bug_fixed
        ),

        "total_commits_found": total_commits,
        "total_non_merge_commits_found": total_non_merge_commits,
        "total_fix_like_commits_found": total_fix_like_commits,
        "total_java_file_references": total_java_files
    }


# =====================================================================
# MAIN
# =====================================================================

def main():
    ensure_output_dir()
    check_git_repo()

    if not os.path.exists(TICKETS_FILE):
        raise FileNotFoundError(f"File tickets non trovato: {TICKETS_FILE}")

    print("📂 Leggo tickets...")
    tickets = read_tickets(TICKETS_FILE)
    print(f"✅ Ticket letti: {len(tickets)}")

    metadata_rows = []
    commit_rows = []
    java_file_rows = []
    linkage_rows = []

    for idx, ticket in enumerate(tickets, start=1):
        print("\n" + "=" * 80)
        print(f"[{idx}/{len(tickets)}] Processing {ticket}")

        # -------------------------------------------------------------
        # Jira metadata
        # -------------------------------------------------------------
        issue_json = jira_get_issue(ticket)

        jira_found = False
        issue_type = ""
        status = ""
        resolution = ""
        created = ""
        resolutiondate = ""
        affected_versions = ""
        fix_versions = ""
        summary = ""

        if issue_json is None:
            print("   Jira: NON trovato o errore")

        else:
            jira_found = True
            fields = issue_json.get("fields", {})

            issue_type = fields.get("issuetype", {}).get("name", "")
            status = fields.get("status", {}).get("name", "")
            resolution = (
                fields.get("resolution", {}).get("name", "")
                if fields.get("resolution")
                else ""
            )

            created = normalize_date(fields.get("created"))
            resolutiondate = normalize_date(fields.get("resolutiondate"))
            affected_versions = version_names(fields.get("versions", []))
            fix_versions = version_names(fields.get("fixVersions", []))
            summary = fields.get("summary", "").replace("\n", " ").strip()

            print(f"   Jira: {issue_type} | {status} | {resolution}")
            print(f"   Created: {created}")
            print(f"   Resolution date: {resolutiondate}")
            print(f"   Affected versions: {affected_versions}")
            print(f"   Fix versions: {fix_versions}")

        metadata_rows.append({
            "ticket": ticket,
            "issue_type": issue_type,
            "status": status,
            "resolution": resolution,
            "created": created,
            "resolutiondate": resolutiondate,
            "affected_versions": affected_versions,
            "fix_versions": fix_versions,
            "summary": summary
        })

        time.sleep(JIRA_SLEEP_SECONDS)

        # -------------------------------------------------------------
        # Git / GitHub linkage
        # -------------------------------------------------------------
        commits = find_commits_for_ticket(ticket)

        commits_found = len(commits)
        non_merge_commits_found = sum(
            1 for commit in commits if not commit["is_merge_commit"]
        )
        fix_like_commits_found = sum(
            1 for commit in commits if commit["is_fix_like"]
        )

        java_files_total_for_ticket = 0

        if commits_found > 0:
            print(f"   Git commits trovati: {commits_found}")

            for commit in commits:
                commit_rows.append(commit)

                java_files = get_java_files_modified_by_commit(
                    commit["commit_hash"]
                )
                java_files_total_for_ticket += len(java_files)

                for java_file in java_files:
                    java_file_rows.append({
                        "ticket": ticket,
                        "commit_hash": commit["commit_hash"],
                        "java_file": java_file
                    })

                merge_label = "MERGE" if commit["is_merge_commit"] else "NON-MERGE"

                print(
                    f"      {commit['commit_hash'][:10]} | "
                    f"{merge_label} | "
                    f"java_files={len(java_files)} | "
                    f"{commit['subject'][:80]}"
                )

        else:
            print("   Git commits trovati: 0")

        valid_bug_fixed = is_valid_bug_fixed(issue_type, status, resolution)

        linked_to_git = commits_found > 0
        linked_to_java = java_files_total_for_ticket > 0

        # Ticket usabile per SZZ:
        # - è un bug fixed valido su Jira
        # - ha almeno un commit collegato
        # - almeno un commit tocca file Java
        usable_for_szz = valid_bug_fixed and linked_to_git and linked_to_java

        linkage_rows.append({
            "ticket": ticket,
            "jira_found": "YES" if jira_found else "NO",
            "is_valid_bug_fixed": "YES" if valid_bug_fixed else "NO",
            "has_affected_versions": "YES" if affected_versions else "NO",
            "has_fix_versions": "YES" if fix_versions else "NO",
            "commits_found": commits_found,
            "non_merge_commits_found": non_merge_commits_found,
            "fix_like_commits_found": fix_like_commits_found,
            "java_files_touched": java_files_total_for_ticket,
            "linked_to_git": "YES" if linked_to_git else "NO",
            "linked_to_java": "YES" if linked_to_java else "NO",
            "usable_for_szz": "YES" if usable_for_szz else "NO"
        })

        # -------------------------------------------------------------
        # Salvataggio incrementale
        # -------------------------------------------------------------
        if idx % 25 == 0:
            write_tickets_metadata(metadata_rows)
            write_ticket_commits(commit_rows)
            write_ticket_java_files(java_file_rows)
            write_linkage(linkage_rows)

            partial_summary = compute_linkage_summary(linkage_rows)
            write_json(LINKAGE_SUMMARY_JSON, partial_summary)

            print("💾 Salvataggio incrementale completato")
            print("📊 Linkage parziale:")
            print(json.dumps(partial_summary, indent=2, ensure_ascii=False))

    # =================================================================
    # Salvataggio finale
    # =================================================================

    write_tickets_metadata(metadata_rows)
    write_ticket_commits(commit_rows)
    write_ticket_java_files(java_file_rows)
    write_linkage(linkage_rows)

    linkage_summary = compute_linkage_summary(linkage_rows)
    write_json(LINKAGE_SUMMARY_JSON, linkage_summary)

    summary = {
        "tickets_input": len(tickets),
        "outputs": {
            "tickets_metadata_csv": TICKETS_METADATA_CSV,
            "ticket_commits_csv": TICKET_COMMITS_CSV,
            "ticket_java_files_csv": TICKET_JAVA_FILES_CSV,
            "jira_github_linkage_csv": JIRA_GITHUB_LINKAGE_CSV,
            "linkage_summary_json": LINKAGE_SUMMARY_JSON
        },
        "linkage_summary": linkage_summary
    }

    write_json(SUMMARY_JSON, summary)

    print("\n" + "=" * 80)
    print("✅ COMPLETATO")
    print(f"📄 Metadata ticket: {TICKETS_METADATA_CSV}")
    print(f"📄 Commit ticket: {TICKET_COMMITS_CSV}")
    print(f"📄 File Java per commit: {TICKET_JAVA_FILES_CSV}")
    print(f"📄 Linkage Jira-GitHub: {JIRA_GITHUB_LINKAGE_CSV}")
    print(f"📄 Linkage summary: {LINKAGE_SUMMARY_JSON}")
    print(f"📄 Summary generale: {SUMMARY_JSON}")

    print("\n📊 LINKAGE SUMMARY:")
    print(json.dumps(linkage_summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()