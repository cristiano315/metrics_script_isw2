"""
Metriche derivate:
- Bug density
- Fix flag
"""

def compute_derived(metrics, class_id, loc):

    nfix = metrics[class_id]["nfix"]

    # FIX → classe difettosa
    metrics[class_id]["fix"] = 1 if nfix > 0 else 0

    # Bug density
    metrics[class_id]["bug_density"] = (
        nfix / loc if loc > 0 else 0
    )