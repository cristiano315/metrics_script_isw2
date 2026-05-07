"""
Data: 28/04/2026
Autore: enrico_barbatano

Refactoring della gestione delle metriche di dipendenza (Fan-Out e Fan-In).

In questa versione:
- è stata separata la logica di estrazione delle dipendenze (delegata al modulo helper)
- è stato eliminato l'accesso diretto alla struttura globale 'metrics' per migliorare la modularità
- il Fan-Out viene calcolato per singola release come numero di dipendenze distinte
- il Fan-In è stato ridefinito come metrica cumulativa globale (Fan-In total),
  costruita aggregando le dipendenze tra classi lungo tutte le release
- ! sono stati eliminati i duplicati tramite uso di strutture dati di tipo set
- è stata introdotta una struttura dati interna per mantenere lo storico delle dipendenze,
  permettendo di calcolare la centralità architetturale delle classi

Questo refactoring migliora:
- riusabilità del codice
- coerenza tra metriche
- manutenibilità dell'architettura
- correttezza metodologica rispetto alla letteratura sulla defect prediction
"""

from metrics_scripts import helper as hp

class FanInOut:
    """
    Classe per calcolare Fan-Out (per release)
    e Fan-In Total (globale).
    """

    def __init__(self):
        # Dizionario globale: classe -> set di classi che la usano
        self.fan_in_map = {}

    def compute_fan_out(self, file_content):
        """
        Calcola Fan-Out per una classe (per release).
        Usa helper per estrarre dipendenze.

        Ritorna:
        - numero di dipendenze
        - set delle dipendenze (serve per Fan-In)
        """

        dependencies = hp.extract_project_dependencies(file_content)

        fan_out_value = len(dependencies)

        return fan_out_value, dependencies

    def update_fan_in(self, class_id, dependencies):
        """
        Aggiorna Fan-In total.

        class_id = classe corrente
        dependencies = classi che questa classe usa
        """

        for dep in dependencies:

            if dep not in self.fan_in_map:
                self.fan_in_map[dep] = set()

            self.fan_in_map[dep].add(class_id)

    def get_fan_in_total(self, class_id):
        """
        Restituisce il Fan-In total della classe.
        """

        return len(self.fan_in_map.get(class_id, set()))
