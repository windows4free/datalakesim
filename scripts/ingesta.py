"""
SCRIPT 1: ingesta.py
--------------------
Lee la carpeta 00_landing y mueve cada archivo a su carpeta
correspondiente dentro de datalake/raw según su extensión.
"""

import os
import shutil
import logging
from datetime import datetime
from pathlib import Path

# ── Rutas del proyecto ──────────────────────────────────────────────────────
BASE = Path(r"C:\Users\wilso\Downloads\DataLakeSim")

LANDING   = BASE / "00_landing"
RAW_CSV   = BASE / "datalake" / "raw" / "csv"
RAW_EXCEL = BASE / "datalake" / "raw" / "excel"
RAW_JSON  = BASE / "datalake" / "raw" / "json"
REJECTED  = BASE / "datalake" / "rejected"
LOG_FILE  = BASE / "logs" / "datalake_log.csv"

# ── Extensiones aceptadas ───────────────────────────────────────────────────
DESTINOS = {
    ".csv":  RAW_CSV,
    ".xlsx": RAW_EXCEL,
    ".json": RAW_JSON,
}

# ── Configuración del log ───────────────────────────────────────────────────
def escribir_log(proceso, archivo, accion, estado, detalle=""):
    """Agrega una línea al archivo CSV de log."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    encabezado = not LOG_FILE.exists()
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        if encabezado:
            f.write("fecha_hora,nivel,proceso,archivo,accion,estado,detalle\n")
        nivel = "ERROR" if estado == "Error" else "INFO"
        linea = (
            f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")},'
            f'{nivel},INGESTA_RAW,{archivo},{accion},{estado},{detalle}\n'
        )
        f.write(linea)

# ── Lógica principal ────────────────────────────────────────────────────────
def mover_archivo(archivo: Path, destino: Path):
    """Mueve el archivo; si ya existe, agrega timestamp al nombre."""
    destino.mkdir(parents=True, exist_ok=True)
    destino_final = destino / archivo.name

    # Evitar sobreescribir: renombrar con timestamp
    if destino_final.exists():
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        nuevo_nombre = f"{archivo.stem}_{ts}{archivo.suffix}"
        destino_final = destino / nuevo_nombre

    shutil.move(str(archivo), str(destino_final))
    return destino_final.name


def ejecutar_ingesta():
    print(f"[{datetime.now()}] Iniciando ingesta...")

    archivos = list(LANDING.glob("*"))
    if not archivos:
        print("  No hay archivos en landing.")
        escribir_log("INGESTA_RAW", "—", "Revisión landing", "Info", "Carpeta vacía")
        return

    for archivo in archivos:
        if archivo.is_dir():
            continue  # ignorar subcarpetas

        ext = archivo.suffix.lower()

        if ext in DESTINOS:
            try:
                nombre_final = mover_archivo(archivo, DESTINOS[ext])
                msg = f"Movido a raw/{ext.lstrip('.')}"
                print(f"  ✔ {archivo.name} → raw/{ext.lstrip('.')}/{nombre_final}")
                escribir_log("INGESTA_RAW", archivo.name, msg, "Éxito", nombre_final)
            except Exception as e:
                print(f"  ✘ Error moviendo {archivo.name}: {e}")
                escribir_log("INGESTA_RAW", archivo.name, "Mover archivo", "Error", str(e))
        else:
            # Extensión no permitida → rejected
            try:
                nombre_final = mover_archivo(archivo, REJECTED)
                print(f"  ⚠ {archivo.name} rechazado (extensión {ext})")
                escribir_log("INGESTA_RAW", archivo.name, "Rechazado", "Warning",
                             f"Extensión no permitida: {ext}")
            except Exception as e:
                escribir_log("INGESTA_RAW", archivo.name, "Rechazar archivo", "Error", str(e))

    print(f"[{datetime.now()}] Ingesta completada.\n")


if __name__ == "__main__":
    ejecutar_ingesta()
