import os
from metrics_scripts import size as sm
from metrics_scripts import churn 


metrics = {
    "FormAttributeField.java": {
        "Churn_Totale": 0,
        "max_churn": 0,
        "average_churn": 0,
        "loc_added_total": 0,
        "fan_in": 0,
        "age": 0,
    }
}


if __name__ == "__main__":
    
    # Immagina di aver trovato un file tramite la funzione os.walk di prima
    percorso_file_test = "C:\\Uni\\ISW2\\Progetto\\dateaset_script\\syncope_java_releases\\\\release_syncope-1.0.4\\client\\src\\main\\java\\org\\apache\\syncope\\annotation\\FormAttributeField.java"

    
    # --- QUI INIZIA LA PARTE CHE TI INTERESSA ---
    # Apri il file (gestendo l'encoding corretto, spesso utf-8 nei repository GitHub)
    with open(percorso_file_test, "r", encoding="utf-8") as file_gia_aperto:
        
        # Passi alla funzione l'oggetto file aperto, non il percorso testuale!
        #LOC
        loc = sm.calcola_loc_java(file_gia_aperto)
        #CHURN
        current_churn = churn.calcola_churn_sloc(file_gia_aperto, file_gia_aperto)
        #CHURN TOTAL
        metrics["FormAttributeField.java"]["Churn_Totale"] += current_churn
        #MAX CHURN
        if current_churn > metrics["FormAttributeField.java"]["max_churn"]:
            metrics["FormAttributeField.java"]["max_churn"] = current_churn
        #AVERAGE CHURN TOTAL
        #avg=avg+(nuovo/numRelease)
        #LOC ADDED
        loc_added = sm.calculate_loc_added(file_gia_aperto, loc)
        #LOC ADDED TOTAL
        metrics["FormAttributeField.java"]["loc_added_total"] += loc_added
        #FAN OUT
        #importare
        #FAN IN
        #insieme a fan out
        #AGE
        #importare
        #WEIGHTED AGE
        #importare
        
        
        
        print("loc (Size) del file è:", loc)


