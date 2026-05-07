def calcola_loc_java(file_aperto):
    """
    Calcola le metriche LOC (Lines of Code) da un file Java già aperto.
    Restituisce un dizionario con il dettaglio delle righe.
    """
    total_lines = 0
    blank_lines = 0
    comment_lines = 0
    source_lines = 0 # Questa è la vera metrica "Size (LOC)" utile per i modelli

    in_multiline_comment = False

    # Il file è già aperto, possiamo iterarlo riga per riga
    for riga in file_aperto:
        total_lines += 1
        # Rimuove spazi bianchi e tabulazioni a inizio e fine riga
        riga_pulita = riga.strip()

        # 1. Riga vuota
        if not riga_pulita:
            blank_lines += 1
            continue

        # 2. Gestione se siamo già dentro un commento multilinea (/* ... */)
        if in_multiline_comment:
            comment_lines += 1
            if "*/" in riga_pulita:
                in_multiline_comment = False  # Il commento si chiude su questa riga
            continue

        # 3. Inizio di un nuovo commento multilinea
        if riga_pulita.startswith("/*"):
            comment_lines += 1
            # Se non si chiude sulla stessa riga, attiviamo il flag
            if "*/" not in riga_pulita:
                in_multiline_comment = True
            continue

        # 4. Commento a riga singola (//)
        if riga_pulita.startswith("//"):
            comment_lines += 1
            continue

        # 5. Se non è vuota e non è un commento, è codice sorgente reale
        source_lines += 1

    return source_lines


#vecchai funzione che calcola loc added
#def calculate_loc_added(old_file, loc_new_file):
    result = loc_new_file - calcola_loc_java(old_file)
    return result if result > 0 else 0