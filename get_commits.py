import subprocess
import os
import shutil

def keep_only_java_files(directory):
    """
    Scorre l'intera directory partendo dal basso verso l'alto (topdown=False),
    elimina tutti i file che non terminano con .java e rimuove le cartelle vuote.
    """
    for root, dirs, files in os.walk(directory, topdown=False):
        # 1. Elimina i file non-.java
        for file in files:
            if not file.endswith('.java'):
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                except OSError:
                    pass # Ignora eventuali errori di permessi su file specifici

        # 2. Elimina la cartella se è rimasta vuota dopo la pulizia
        try:
            if not os.listdir(root): # Se la lista dei file/cartelle è vuota
                os.rmdir(root)
        except OSError:
            pass

def clone_github_releases(repo_url, releases, base_dest_folder):
    """
    Clona specifiche release e conserva solo i file .java.
    """
    if not os.path.exists(base_dest_folder):
        os.makedirs(base_dest_folder)
        print(f"📂 Creata cartella base: {base_dest_folder}\n")

    for release in releases:
        dest_folder = os.path.join(base_dest_folder, f"release_{release}")
        
        if os.path.exists(dest_folder):
            print(f"⚠️ La cartella {dest_folder} esiste già. Salto la release '{release}'.\n")
            continue

        print(f"⬇️  Clonazione della release '{release}' in corso...")

        command = [
            "git", "clone",
            "--depth", "1",
            "--branch", release,
            repo_url,
            dest_folder
        ]

        try:
            # Esegue il clone
            subprocess.run(command, check=True, capture_output=True, text=True)
            
            # --- FASE DI PULIZIA ---
            print(f"🧹 Pulizia: rimozione cartella .git e file non-Java...")
            
            # Rimuoviamo prima la cartella .git nascosta (è pesante e non serve all'analisi)
            git_dir = os.path.join(dest_folder, ".git")
            if os.path.exists(git_dir):
                shutil.rmtree(git_dir, ignore_errors=True)
            
            # Eseguiamo la funzione di filtraggio per i file .java
            #keep_only_java_files(dest_folder)
            
            print(f"✅ Release '{release}' pronta! Contiene solo file .java in: {dest_folder}\n")
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Errore durante la clonazione della release '{release}'.")
            print(f"Dettagli errore Git:\n{e.stderr}\n")

if __name__ == "__main__":
    # --- CONFIGURAZIONE ---
    REPO_URL = "https://github.com/apache/syncope.git" 
    RELEASES_TO_DOWNLOAD = ["syncope-1.0.4", "syncope-1.0.5", "syncope-1.0.6", "syncope-1.0.7", "syncope-1.1.0", "syncope-1.0.8", "syncope-1.1.1", "syncope-1.1.2", "syncope-1.1.3", "syncope-1.1.4", "syncope-1.1.5", "syncope-1.1.6", "syncope-1.1.7", "syncope-1.1.8", "syncope-1.2.0-M1", "syncope-1.2.0", "syncope-1.2.1", "syncope-1.2.2", "syncope-1.2.3", "syncope-1.2.4", "syncope-1.2.5", "syncope-1.2.6", "syncope-2.0.0-M1", "syncope-1.2.7", "syncope-2.0.0-M2", "syncope-2.0.0-M3"] # Ricordati la 'v' se richiesta dal repository!
    DESTINATION_FOLDER = "./syncope_java_releases"

    clone_github_releases(REPO_URL, RELEASES_TO_DOWNLOAD, DESTINATION_FOLDER)