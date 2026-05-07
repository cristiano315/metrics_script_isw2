"""
    La metrica Age è stata calcolata utilizzando la cronologia Git del progetto, 
    ottenendo il timestamp della release corrente e del primo commit del file. 
    La Weighted Age è stata poi derivata moltiplicando l’età del file per il numero di linee di codice modificate (LOC touched), 
    al fine di combinare informazione temporale ed evolutiva.
    """

import difflib
from metrics_scripts import helper as hp


def calcola_churn_sloc(file_vecchio, file_nuovo):
    
    # Filtriamo i file prima di confrontarli
    righe_vecchio_pulite = hp.estrai_linee_sorgente(file_vecchio)
    righe_nuovo_pulite = hp.estrai_linee_sorgente(file_nuovo)

    if not file_vecchio:
        return len(hp.estrai_linee_sorgente(file_nuovo))

    righe_aggiunte = 0
    righe_rimosse = 0

    # Calcoliamo la differenza solo sul codice effettivo
    differenza = difflib.ndiff(righe_vecchio_pulite, righe_nuovo_pulite)

    for riga in differenza:
        if riga.startswith('+ '):
            righe_aggiunte += 1
        elif riga.startswith('- '):
            righe_rimosse += 1

    churn_totale = righe_aggiunte + righe_rimosse

    return churn_totale


