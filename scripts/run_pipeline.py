from pathlib import Path
import sys

# Add src/ to the Python path to allow importing ceo_radar
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))
sys.path.append(str(ROOT_DIR / "src"))

from ceo_radar.pipeline import run_pipeline

if __name__ == "__main__":
    run_pipeline()
