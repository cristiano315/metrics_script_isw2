"""
Data: 28/04/2026
Autore: enrico_barbatano

Refactoring della metrica LOC Added.

In una prima versione, LOC Added veniva calcolata come differenza tra
il numero totale di linee di codice della nuova versione e della versione precedente del file.
Tale approccio risultava metodologicamente scorretto, in quanto misura solo la variazione netta
delle linee (LOC_new - LOC_old), senza distinguere tra linee aggiunte e linee rimosse.

Questo comportava perdite di informazione rilevanti:
- non venivano contabilizzate le modifiche reali al codice (es. +10 linee e -10 linee → risultato 0)
- veniva sottostimato l'effettivo lavoro di sviluppo e manutenzione
- la metrica risultava poco informativa per modelli di bug prediction

Nel refactoring corrente, LOC Added è calcolata mediante confronto differenziale
tra due versioni successive del file (utilizzando difflib), conteggiando esclusivamente
le linee di codice effettivamente aggiunte, dopo aver rimosso commenti e linee vuote.

Questo approccio:
- consente di ottenere una misura accurata del codice introdotto
- preserva l'informazione sulle modifiche reali
- risulta coerente con la definizione presente in letteratura
- migliora la capacità predittiva della metrica nei modelli di defect prediction
"""

import difflib
from metrics_scripts import helper as hp
def calculate_loc_added(old_file, new_file):
    

    old_lines = hp.estrai_linee_sorgente(old_file)
    new_lines = hp.estrai_linee_sorgente(new_file)

    added = 0

    diff = difflib.ndiff(old_lines, new_lines)

    for line in diff:
        if line.startswith('+ '):
            added += 1

    return added
