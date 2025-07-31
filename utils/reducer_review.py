import pandas as pd
import os

def reduce_csv_size(input_csv_path, output_csv_path, sample_percentage=None, num_rows_to_sample=None, random_seed=42):
    """
    Reduce el tamaño de un archivo CSV tomando una muestra de sus filas.

    Args:
        input_csv_path (str): Ruta al archivo CSV de entrada (el grande).
        output_csv_path (str): Ruta donde se guardará el nuevo archivo CSV reducido.
        sample_percentage (float, optional): Porcentaje de filas a muestrear (ej. 0.1 para 10%).
                                            Debe ser un valor entre 0.0 y 1.0.
                                            Si se especifica, 'num_rows_to_sample' será ignorado.
        num_rows_to_sample (int, optional): Número exacto de filas a muestrear.
                                            Si se especifica, 'sample_percentage' será ignorado.
        random_seed (int, optional): Semilla para la generación de números aleatorios,
                                     asegurando que el muestreo sea reproducible.
    Returns:
        bool: True si el archivo se redujo con éxito, False en caso contrario.
    """


    if sample_percentage is None and num_rows_to_sample is None:
        print("Error: Debes especificar 'sample_percentage' o 'num_rows_to_sample'.")
        return False

    try:
        print(f"Cargando el archivo CSV grande desde: {input_csv_path}")
        # Cargar el archivo CSV completo. Para archivos muy grandes que no caben en RAM,
        # se necesitaría un enfoque de lectura por bloques (chunking).
        # Para 1GB, pandas debería manejarlo bien en la mayoría de los sistemas modernos.
        df = pd.read_csv(input_csv_path)
        print(f"Archivo cargado. Filas originales: {len(df)}")

        df_sampled = pd.DataFrame() # Inicializar un DataFrame vacío para la muestra

        if sample_percentage is not None:
            if not (0.0 < sample_percentage <= 1.0):
                print("Error: 'sample_percentage' debe ser un valor entre 0.0 y 1.0.")
                return False
            print(f"Muestreando el {sample_percentage*100:.2f}% de las filas...")
            df_sampled = df.sample(frac=sample_percentage, random_state=random_seed)
        elif num_rows_to_sample is not None:
            if num_rows_to_sample <= 0:
                print("Error: 'num_rows_to_sample' debe ser un número positivo.")
                return False
            if num_rows_to_sample > len(df):
                print(f"Advertencia: 'num_rows_to_sample' ({num_rows_to_sample}) es mayor que el número total de filas ({len(df)}). Se usará el archivo completo.")
                df_sampled = df
            else:
                print(f"Muestreando {num_rows_to_sample} filas...")
                df_sampled = df.sample(n=num_rows_to_sample, random_state=random_seed)
        else:
            # Esto no debería ocurrir debido a la comprobación inicial, pero es una salvaguarda
            print("No se especificó un método de muestreo válido.")
            return False

        print(f"Muestreo completado. Filas en el archivo reducido: {len(df_sampled)}")

        print(f"Guardando el archivo reducido en: {output_csv_path}")
        df_sampled.to_csv(output_csv_path, index=False) # index=False para no guardar el índice de pandas
        print("Archivo reducido guardado exitosamente.")
        return True

    except Exception as e:
        print(f"Ocurrió un error al procesar el archivo: {e}")
        return False

# --- Cómo usar la función ---
if __name__ == "__main__":
    # Define la ruta de tu archivo CSV original
    original_csv = "https://huggingface.co/datasets/Pauleera/Goodreads-Book-Reviews/resolve/main/goodreads_reviews.csv"
    # Define la ruta para el nuevo archivo CSV reducido
    reduced_csv = 'reviews_reduced.csv'

    # --- OPCIONES DE MUESTREO ---
    # Opción 1: Muestrear un porcentaje de las filas (ej. 10% de las filas)
    # Descomenta la línea que quieras usar y comenta las otras
    success = reduce_csv_size(original_csv, reduced_csv, sample_percentage=0.2)

    # Opción 2: Muestrear un número fijo de filas (ej. 100,000 filas)
    # success = reduce_csv_size(original_csv, reduced_csv, num_rows_to_sample=100000)

    if success:
        print("\n¡Proceso de reducción de CSV completado!")
        # Puedes verificar el tamaño del nuevo archivo
        if os.path.exists(reduced_csv):
            #original_size = os.path.getsize(original_csv) / (1024 * 1024) # en MB
            reduced_size = os.path.getsize(reduced_csv) / (1024 * 1024) # en MB
            #print(f"Tamaño original: {original_size:.2f} MB")
            print(f"Tamaño reducido: {reduced_size:.2f} MB")
    else:
        print("\nEl proceso de reducción de CSV falló.")
