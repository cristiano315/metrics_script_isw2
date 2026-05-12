"""
Gestisce metriche evolutive cumulative.
Le metriche di churn / loc_added vengono aggiornate solo
se esiste una versione precedente della classe.
"""


def update_churn(metrics, class_id, current_churn, is_first_observation):
    if is_first_observation:
        return

    metrics[class_id]["churn_total"] += current_churn

    if current_churn > metrics[class_id]["max_churn"]:
        metrics[class_id]["max_churn"] = current_churn


def update_loc_added(metrics, class_id, loc_added, is_first_observation):
    if is_first_observation:
        return

    metrics[class_id]["loc_added_total"] += loc_added

    if loc_added > metrics[class_id]["max_loc_added"]:
        metrics[class_id]["max_loc_added"] = loc_added


def update_revisions(metrics, class_id, old_lines, new_lines, is_first_observation):
    """
    Number of Revisions = numero di vere modifiche osservate tra release.
    La prima osservazione non conta come revisione.
    """
    if is_first_observation:
        return

    if old_lines != new_lines:
        metrics[class_id]["revisions"] += 1