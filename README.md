# DataLakeSim – Simulación Local de Data Lake

## ¿Qué hace este proyecto?

Simula cómo funciona un Data Lake real usando carpetas locales y dos scripts de Python:

| Script | Qué hace |
|--------|----------|
| `ingesta.py` | Revisa `00_landing`, mueve cada archivo a `raw/csv`, `raw/excel` o `raw/json` según su extensión. Si el formato no es válido, lo manda a `rejected`. |
| `limpieza.py` | Lee los archivos de `raw`, les aplica limpieza (quita duplicados, filas vacías, espacios) y guarda el resultado limpio en `silver_clean`. |

Todo queda registrado automáticamente en `logs/datalake_log.csv`.


## Estructura de carpetas

```
C:\DataLakeSim\
├── 00_landing\          ← Aquí colocas los archivos nuevos (CSV, Excel, JSON)
├── datalake\
│   ├── raw\
│   │   ├── csv\         ← Archivos .csv recién llegados (sin limpiar)
│   │   ├── excel\       ← Archivos .xlsx/.xls recién llegados
│   │   └── json\        ← Archivos .json recién llegados
│   ├── silver_clean\    ← Archivos ya limpios y listos para analizar
│   ├── gold\            ← (Reservado para reportes finales)
│   └── rejected\        ← Archivos con error o formato no permitido
├── scripts\
│   ├── ingesta.py
│   └── limpieza.py
├── logs\
│   └── datalake_log.csv ← Registro automático de todo lo que ocurre
└── evidencias\          ← Capturas de pantalla para la entrega
```

## Lenguaje y decisiones tomadas

- **Lenguaje:** Python 3
- **Librerías:** `pandas` (limpieza de datos), `openpyxl` (leer/escribir Excel)
- **Formato de salida:** CSV (fácil de abrir y revisar)
- **Duplicados en landing:** Se renombran con timestamp para no perder archivos
- **Errores:** Si un archivo falla, el proceso continúa con el siguiente
