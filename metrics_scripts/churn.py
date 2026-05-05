import difflib

def estrai_linee_sorgente(file_aperto):
    """
    Legge un file riga per riga e restituisce una lista contenente 
    solo il codice sorgente reale (ignorando righe vuote e commenti).
    """
    linee_sorgente = []
    in_multiline_comment = False

    for riga in file_aperto:
        riga_pulita = riga.strip()

        # 1. Ignora le righe vuote
        if not riga_pulita:
            continue

        # 2. Gestione commento multilinea aperto in precedenza
        if in_multiline_comment:
            if "*/" in riga_pulita:
                in_multiline_comment = False # Il commento si chiude qui
            continue

        # 3. Inizio di un nuovo commento multilinea
        if riga_pulita.startswith("/*"):
            if "*/" not in riga_pulita:
                in_multiline_comment = True
            continue

        # 4. Ignora i commenti a riga singola
        if riga_pulita.startswith("//"):
            continue

        # Se arriva qui, è codice vero. Lo aggiungiamo alla lista.
        # Manteniamo la 'riga' originale (con spazi e \n) per passarla a difflib
        linee_sorgente.append(riga)
        
    return linee_sorgente


def calcola_churn_sloc(file_vecchio, file_nuovo):
    """
    Calcola il Churn (Righe Aggiunte + Righe Rimosse) ignorando i commenti.
    """
    # Filtriamo i file prima di confrontarli
    righe_vecchio_pulite = estrai_linee_sorgente(file_vecchio)
    righe_nuovo_pulite = estrai_linee_sorgente(file_nuovo)

    if not file_vecchio:
        return len(estrai_linee_sorgente(file_nuovo))

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


