"""
Calcolo metriche aggregate globali
"""

from metrics_scripts import size as sm

def compute_aggregates(metrics, file_history, fan_io):

    for class_id in metrics:
        revs = metrics[class_id]["revisions"]
        loc = sm.calcola_loc_java(file_history.get(class_id, []))

        # Average churn
        metrics[class_id]["avg_churn"] = (
            metrics[class_id]["Churn_Totale"] / revs if revs > 0 else 0
        )

        # Average LOC Added
        metrics[class_id]["avg_loc_added"] = (
            metrics[class_id]["loc_added_total"] / revs if revs > 0 else 0
        )

        # Fan-In total
        metrics[class_id]["fan_in"] = fan_io.get_fan_in_total(class_id)

        # LOC Touched
        metrics[class_id]["loc_touched"] = metrics[class_id]["Churn_Totale"]

        # Revisions Density
        metrics[class_id]["revisions_density"] = (
            revs / loc if loc > 0 else 0
        )

        # NS → cardinalità
        metrics[class_id]["ns"] = len(metrics[class_id]["ns"])