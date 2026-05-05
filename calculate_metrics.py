import os
from metrics_scripts import size as sm
from metrics_scripts import churn 

import os

metrics = {}

def create_dataset(directory_path):
    file_history = {}
    
    # os.walk generates the file names in a directory tree
    
    for current_folder, subfolders, files in os.walk(directory_path):
        print(f"\n📂 Exploring release: {current_folder}")
        
        for file_name in files:
            # os.path.join concatenates the folder path and the file name
            full_path = os.path.join(current_folder, file_name)

            # Se è la prima volta che incontriamo questa classe, inizializziamo le metriche
            if file_name not in metrics:
                metrics[file_name] = {
                    "Churn_Totale": 0,
                    "max_churn": 0,
                    "average_churn": 0,
                    "loc_added_total": 0,
                    "fan_in": 0,
                    "age": 0
                }
            
            # Use a try-except block to handle potential errors (e.g., binary files or missing permissions)
            try:
                # Open the file in text read mode ('r')
                with open(full_path, 'r', encoding='utf-8') as new_file:

                    new_lines = new_file.readlines()
                    
                    old_lines = file_history.get(file_name, [])
                    
                    # Here we calculate the metrics
                    print(f"  📄 Opened: {file_name} (Successfully read)")

                    current_metrics  = calculate_all_metrics(old_lines, new_lines, file_name)

                    print(f"    📊 Metrics for {file_name}: {current_metrics}")

                    file_history[file_name] = new_lines
                    
            except UnicodeDecodeError:
                # Occurs if trying to read a non-text file (e.g., images, .pdf, .zip)
                print(f"  ⚠️ Skipped: {file_name} (Not a readable text file)")
            except PermissionError:
                print(f"  ⛔ Access denied: {file_name} (Insufficient permissions)")
            except Exception as e:
                print(f"  ❌ Unexpected error with {file_name}: {e}")


def calculate_all_metrics(old_file, new_file, class_name):
    # LOC
    loc = sm.calcola_loc_java(new_file)
    
    # CHURN
    current_churn = churn.calcola_churn_sloc(old_file, new_file)

    #CHURN TOTAL
    metrics[class_name]["Churn_Totale"] += current_churn
    churn_total = metrics[class_name]["Churn_Totale"]
    
    # LOC ADDED
    loc_added = sm.calculate_loc_added(new_file, loc)

    #MAX CHURN
    if current_churn > metrics[class_name]["max_churn"]:
        metrics[class_name]["max_churn"] = current_churn
    max_churn = metrics[class_name]["max_churn"]

    #LOC ADDED
    loc_added = sm.calculate_loc_added(old_file, loc)

    #LOC ADDED TOTAL
    metrics[class_name]["loc_added_total"] += loc_added
    loc_added_total = metrics[class_name]["loc_added_total"]
    
    #FAN OUT
    #importare
    
    #FAN IN
    #insieme a fan out
    
    #AGE
    #importare
    
    #WEIGHTED AGE
    #importare
    
    return {
        "loc": loc,
        "churn": current_churn,
        "churn_total": churn_total,
        "max_churn": max_churn,
        "loc_added_total": loc_added_total,
        "loc_added": loc_added,
        # "fan_out": fan_out,
        # "fan_in": fan_in,
        # "age": age,
        # "weighted_age": weighted_age,
    }


if __name__ == "__main__":
    
    target_directory = "./syncope_java_releases"
    
    create_dataset(target_directory)        


