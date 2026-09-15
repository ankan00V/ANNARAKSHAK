import os
import sys
import tempfile
from pathlib import Path

# Point the app at a throwaway data dir BEFORE app.config is imported.
_tmp = tempfile.mkdtemp(prefix="annrakshak-test-")
os.environ["ANNRAKSHAK_DATA_DIR"] = _tmp
# Hermetic: never call the paid Sarvam API from tests (load_dotenv does not
# override an already-set variable, so an empty value wins over .env).
os.environ["SARVAM_API_KEY"] = ""
# Deterministic stub scenarios, even when a trained model sits in ml/artifacts.
os.environ["ANNRAKSHAK_VISION"] = "stub"
os.environ["ANNRAKSHAK_DB_URL"] = f"sqlite:///{Path(_tmp) / 'test.db'}"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
