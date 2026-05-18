from pathlib import Path

STUDENT_NAME = "Mohid Faisal"
STUDENT_ID = "BSCS23092"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_DB_PATH = DATA_DIR / "studysync.db"
