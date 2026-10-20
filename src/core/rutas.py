from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DATA_DIR        = BASE_DIR / "data"
RAW_DIR         = DATA_DIR / "raw"
ARCHIVE_DIR     = RAW_DIR / "archive"
CAPTURAS_DIR    = RAW_DIR / "capturas"
PROCESSED_DIR   = DATA_DIR / "processed"
SPLITS_DIR      = DATA_DIR / "splits"
LOGS_DIR        = BASE_DIR / "logs"

METADATA_PROCESSED = PROCESSED_DIR / "metadata.csv"
METADATA_CAPTURAS  = CAPTURAS_DIR / "metadata_capturas.csv"

CLASES_VALIDAS  = ("carton", "papel", "tela")
VERSION_DATASET = "1.0.0"