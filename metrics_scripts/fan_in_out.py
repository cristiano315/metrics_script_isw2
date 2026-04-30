import re

def calcola_fan_out_progetto(file_aperto, metrics):
    """
    Calcola il Fan-out ignorando le librerie standard (java, javax).
    Restituisce solo un numero intero.
    """
    fan_out = 0
    pattern_import = re.compile(r"^\s*import\s+(?:static\s+)?([\w\.]+)\s*;")

    for riga in file_aperto:
        match = pattern_import.match(riga)
        if match:
            nome_libreria = match.group(1)
            
            # Se NON inizia con java. e NON inizia con javax., lo contiamo
            if nome_libreria.startswith("org.apache.syncope."):
                fan_out += 1
                nome_classe = nome_libreria.split('.')[-1]
                metrics[nome_classe]["fan_out"] += 1 #CONTA ANCHE I DUPLICATI, RIVEDERE

    return fan_out

# --- ESEMPIO DI UTILIZZO ---
if __name__ == "__main__":
    
    with open("TestStorm.java", "w") as f:
        f.write("""package org.apache.storm.topology;

        import java.util.Map;
        import java.io.File;
        import javax.servlet.http.HttpServlet;
        import org.apache.storm.task.OutputCollector;
        import org.apache.storm.task.TopologyContext;

        public class TestStorm { }
        """)

    with open("TestStorm.java", "r") as file_da_analizzare:
        # Ora la funzione restituisce direttamente il numero!
        numero_fan_out = calcola_fan_out_progetto(file_da_analizzare)
        
        print(f"Il Fan-out del progetto è: {numero_fan_out}") 
        # Risultato atteso: 2 (ignora Map, File e HttpServlet)