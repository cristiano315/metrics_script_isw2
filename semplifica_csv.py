import pandas as pd

def simplify_class_name(full_path):
    """
    Prende il path completo e restituisce solo il nome del file.
    """
    return full_path.replace("\\", "/").split("/")[-1]


def simplify_dataset(input_path, output_path):
    print(f"Carico dataset: {input_path}")
    df = pd.read_csv(input_path)

    if "class" not in df.columns:
        print("❌ Colonna 'class' non trovata")
        return

    print("Semplifico i nomi delle classi...")

    df["class"] = df["class"].apply(simplify_class_name)

    print(f"Salvo nuovo dataset: {output_path}")
    df.to_csv(output_path, index=False)

    print("✅ Dataset semplificato creato!")


# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    input_csv = "./dataset_with_smells.csv"
    output_csv = "./dataset_simplified.csv"

    simplify_dataset(input_csv, output_csv)