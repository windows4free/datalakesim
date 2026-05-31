"""
SCRIPT 2: limpieza.py
---------------------
Lee los archivos de datalake/raw (csv, excel, json),
aplica limpieza básica y guarda el resultado en silver_clean.
"""

import os
import pandas as pd
from datetime import datetime
from pathlib import Path

# ── Rutas del proyecto ──────────────────────────────────────────────────────
BASE = Path(r"C:\Users\wilso\Downloads\DataLakeSim")

RAW_CSV    = BASE / "datalake" / "raw" / "csv"
RAW_EXCEL  = BASE / "datalake" / "raw" / "excel"
RAW_JSON   = BASE / "datalake" / "raw" / "json"
SILVER     = BASE / "datalake" / "silver_clean"
REJECTED   = BASE / "datalake" / "rejected"
LOG_FILE   = BASE / "logs" / "datalake_log.csv"

# ── Log ─────────────────────────────────────────────────────────────────────
def escribir_log(archivo, accion, estado, detalle=""):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    encabezado = not LOG_FILE.exists()
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        if encabezado:
            f.write("fecha_hora,nivel,proceso,archivo,accion,estado,detalle\n")
        nivel = "ERROR" if estado == "Error" else "INFO"
        linea = (
            f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")},'
            f'{nivel},LIMPIEZA_RAW,{archivo},{accion},{estado},{detalle}\n'
        )
        f.write(linea)

# ── Limpieza ─────────────────────────────────────────────────────────────────
def limpiar_dataframe(df: pd.DataFrame, nombre_archivo: str) -> tuple[pd.DataFrame, str]:
    """
    Aplica limpieza estándar al DataFrame.
    Retorna (df_limpio, resumen).
    """
    filas_antes = len(df)

    # 1. Normalizar nombres de columnas
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace(r"[^a-z0-9_]", "", regex=True)
    )

    # 2. Eliminar filas completamente vacías
    df.dropna(how="all", inplace=True)

    # 3. Quitar espacios en todos los valores y convertir a string
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip().str.replace(r"\s+", " ", regex=True)

    # 4. Reemplazar celdas vacías o nulas por "N/A"
    df.replace("", "N/A", inplace=True)
    df.replace("nan", "N/A", inplace=True)
    df.replace("None", "N/A", inplace=True)
    df.replace("<NA>", "N/A", inplace=True)

    # 5. Eliminar duplicados DESPUÉS de limpiar espacios
    duplicados = df.duplicated().sum()
    df.drop_duplicates(inplace=True)

    # 6. Contar celdas que quedaron como N/A
    nulos = (df == "N/A").sum().sum()

    filas_despues = len(df)
    resumen = (
        f"Filas antes={filas_antes} | "
        f"Filas después={filas_despues} | "
        f"Duplicados eliminados={duplicados} | "
        f"Celdas reemplazadas con N/A={nulos}"
    )
    return df, resumen


def procesar_archivo(ruta: Path):
    nombre = ruta.name
    ext = ruta.suffix.lower()
    print(f"  Procesando: {nombre}")

    try:
        # Leer según tipo
        if ext == ".csv":
            # keep_default_na=False para que las celdas vacías lleguen como "" y no como NaN
            df = pd.read_csv(ruta, encoding="utf-8", skipinitialspace=True, keep_default_na=False)
        elif ext in (".xlsx", ".xls"):
            df = pd.read_excel(ruta, keep_default_na=False)
        elif ext == ".json":
            df = pd.read_json(ruta)
        else:
            raise ValueError(f"Formato no soportado: {ext}")

        # Limpiar
        df_limpio, resumen = limpiar_dataframe(df, nombre)

        # Guardar en silver_clean como CSV
        SILVER.mkdir(parents=True, exist_ok=True)
        nombre_salida = ruta.stem + "_clean.csv"
        ruta_salida = SILVER / nombre_salida
        df_limpio.to_csv(ruta_salida, index=False, encoding="utf-8")

        print(f"    ✔ Guardado en silver_clean/{nombre_salida}")
        print(f"    ℹ {resumen}")
        escribir_log(nombre, "Limpieza y guardado", "Éxito", resumen)

    except Exception as e:
        print(f"    ✘ Error procesando {nombre}: {e}")
        escribir_log(nombre, "Limpieza", "Error", str(e))
        # Mover a rejected para no bloquear el flujo
        try:
            destino = REJECTED / nombre
            ruta.rename(destino)
            escribir_log(nombre, "Enviado a rejected", "Warning", "No se pudo procesar")
        except Exception as e2:
            escribir_log(nombre, "Mover a rejected", "Error", str(e2))


def generar_gold():
    """Une todos los archivos de silver_clean en un solo CSV en gold."""
    try:
        archivos = list(SILVER.glob("*_clean.csv"))
        if not archivos:
            print("  No hay archivos en silver_clean para consolidar.")
            return

        dfs = []
        for archivo in archivos:
            df = pd.read_csv(archivo, dtype=str)
            df["_fuente"] = archivo.name  # columna extra para saber de dónde viene
            dfs.append(df)

        consolidado = pd.concat(dfs, ignore_index=True)

        GOLD = BASE / "datalake" / "gold"
        GOLD.mkdir(parents=True, exist_ok=True)
        salida = GOLD / f"consolidado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        consolidado.to_csv(salida, index=False, encoding="utf-8")

        print(f"  ✔ Gold generado: {salida.name} ({len(consolidado)} filas totales)")
        escribir_log("consolidado", "Generado gold", "Éxito",
                     f"Archivos unidos={len(archivos)} | Filas totales={len(consolidado)}")

    except Exception as e:
        print(f"  ✘ Error generando gold: {e}")
        escribir_log("consolidado", "Generar gold", "Error", str(e))


def ejecutar_limpieza():
    print(f"[{datetime.now()}] Iniciando limpieza...")

    carpetas = [RAW_CSV, RAW_EXCEL, RAW_JSON]
    total = 0

    for carpeta in carpetas:
        if not carpeta.exists():
            continue
        archivos = list(carpeta.glob("*"))
        for archivo in archivos:
            if archivo.is_file():
                procesar_archivo(archivo)
                total += 1

    if total == 0:
        print("  No hay archivos en raw para procesar.")
        escribir_log("—", "Revisión raw", "Info", "Sin archivos para limpiar")

    print(f"[{datetime.now()}] ocesados:Limpieza completada. Archivos pr {total}")

    # Generar gold automáticamente al final
    print(f"[{datetime.now()}] Generando gold...")
    generar_gold()
    print(f"[{datetime.now()}] Proceso completo.\n")


if __name__ == "__main__":
    ejecutar_limpieza()