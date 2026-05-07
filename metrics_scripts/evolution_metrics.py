"""
Gestisce metriche evolutive:
- Churn
- LOC Added
- Revisions
- Max values
"""

def update_churn(metrics, class_id, current_churn):
    metrics[class_id]["Churn_Totale"] += current_churn

    if current_churn > metrics[class_id]["max_churn"]:
        metrics[class_id]["max_churn"] = current_churn


def update_loc_added(metrics, class_id, loc_added):
    metrics[class_id]["loc_added_total"] += loc_added

    if loc_added > metrics[class_id]["max_loc_added"]:
        metrics[class_id]["max_loc_added"] = loc_added


def update_revisions(metrics, class_id, old_lines, new_lines):
    # Conta solo cambiamenti reali
    if old_lines != new_lines:
        metrics[class_id]["revisions"] += 1
