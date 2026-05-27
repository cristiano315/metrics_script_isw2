import pandas as pd
import json
import os


class SmellIntegrator:

    def __init__(self, dataset_path, cache_path):
        self.dataset_path = dataset_path
        self.cache_path = cache_path
        self.dataset = None
        self.smells_data = None

    # -----------------------------
    # LOAD DATA
    # -----------------------------
    def load_data(self):
        print("📥 Caricamento dataset...")
        self.dataset = pd.read_csv(self.dataset_path)

        print("📥 Caricamento cache smells...")
        with open(self.cache_path, "r") as f:
            self.smells_data = json.load(f)

        print("✅ Dati caricati")

    # -----------------------------
    # NORMALIZZAZIONE PATH
    # -----------------------------
    @staticmethod
    def normalize_path(path):
        return path.replace("\\", os.sep).replace("/", os.sep)

    # opzionale: togli estensione
    @staticmethod
    def remove_extension(path):
        return path.replace(".java", "")

    # -----------------------------
    # MATCH SMELLS
    # -----------------------------
    def compute_smells(self):
        print("🔍 Matching smells...")

        smell_counts = []
        matched = 0

        for _, row in self.dataset.iterrows():

            release = row["release"]
            class_path = self.normalize_path(row["class"])

            smells_in_release = self.smells_data.get(release, {})

            count = 0

            for file_path, smell_count in smells_in_release.items():
                file_path = self.normalize_path(file_path)

                # match robusto (IMPORTANTISSIMO)
                if file_path.endswith(class_path):
                    count = smell_count
                    matched += 1
                    break

                # fallback senza estensione (extra robustezza)
                if self.remove_extension(file_path).endswith(
                    self.remove_extension(class_path)
                ):
                    count = smell_count
                    matched += 1
                    break

            smell_counts.append(count)

        self.dataset["code_smells"] = smell_counts

        print(f"✅ Match completati: {matched}")

    # -----------------------------
    # VALIDAZIONE RAPIDA
    # -----------------------------
    def validate(self):
        print("\n📊 Statistiche smells")

        desc = self.dataset["code_smells"].describe()
        print(desc)

        if desc["max"] == 0:
            print("⚠️ ATTENZIONE: nessuno smell trovato (controlla mapping!)")
        else:
            print("✅ Smells integrati correttamente")

    # -----------------------------
    # SAVE
    # -----------------------------
    def save(self, output_path):
        print(f"\n💾 Salvataggio in: {output_path}")
        self.dataset.to_csv(output_path, index=False)
        print("✅ Dataset salvato")

    # -----------------------------
    # PIPELINE COMPLETA
    # -----------------------------
    def run(self, output_path):
        self.load_data()
        self.compute_smells()
        self.validate()
        self.save(output_path)


# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":

    integrator = SmellIntegrator(
        dataset_path="./dataset.csv",
        cache_path="smells_cache.json"
    )

    integrator.run("./dataset_with_smells.csv")