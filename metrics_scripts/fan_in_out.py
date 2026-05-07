import os
from metrics_scripts import helper as hp

class FanInOut:
    """
    Calcola:
    - Fan-Out (per release)
    - Fan-In total (globale su tutte le release)
    """

    def __init__(self):
        # mappa: nome_classe -> set(classi che la usano)
        self.fan_in_map = {}

    def _normalize_class_name(self, class_path):
        """
        Estrae solo il nome della classe:
        storm-core/src/.../Config.java -> Config
        """
        return class_path.split(os.sep)[-1].replace(".java", "")

    def compute_fan_out(self, file_content):
        """
        Calcola Fan-Out e restituisce anche le dipendenze
        """
        dependencies = hp.extract_project_dependencies(file_content)

        # ✅ pulizia finale (evita None o vuoti)
        dependencies = {d.strip() for d in dependencies if d}

        return len(dependencies), dependencies

    def update_fan_in(self, class_id, dependencies):
        """
        Aggiorna Fan-In: chi usa chi
        """
        current_class = self._normalize_class_name(class_id)

        for dep in dependencies:

            # ✅ normalizzi anche la dipendenza
            dep_clean = dep.strip()

            if not dep_clean:
                continue

            if dep_clean not in self.fan_in_map:
                self.fan_in_map[dep_clean] = set()

            # ✅ aggiungiamo chi usa questa classe
            self.fan_in_map[dep_clean].add(current_class)

    def get_fan_in_total(self, class_id):
        """
        Restituisce fan-in totale
        """
        class_name = self._normalize_class_name(class_id)

        return len(self.fan_in_map.get(class_name, set()))