"""
Calcolo snapshot delle metriche aggregate fino alla release corrente.
"""

from metrics_scripts import size as sm


def snapshot_aggregate_metrics(metrics, class_id, fan_io, current_lines):
    """
    Restituisce le metriche aggregate della classe
    nello stato corrente della pipeline.
    """

    revs = metrics[class_id]["revisions"]
    loc = sm.calcola_loc_java(current_lines)

    churn_total = metrics[class_id]["churn_total"]
    loc_added_total = metrics[class_id]["loc_added_total"]

    avg_churn = churn_total / revs if revs > 0 else 0
    avg_loc_added = loc_added_total / revs if revs > 0 else 0

    return {
        "revisions": revs,
        "max_churn": metrics[class_id]["max_churn"],
        "max_loc_added": metrics[class_id]["max_loc_added"],
        "avg_churn": avg_churn,
        "avg_loc_added": avg_loc_added,
        "fan_in_total": fan_io.get_fan_in_total(class_id),
        "loc_touched_total": churn_total,
        "revisions_density": (revs / loc if loc > 0 else 0),
        "ns": len(metrics[class_id]["ns"])
    }
