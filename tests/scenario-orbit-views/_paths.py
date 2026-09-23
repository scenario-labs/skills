import pathlib
import sys

SCRIPTS = pathlib.Path(__file__).resolve().parents[2] / "skills" / "scenario-orbit-views" / "scripts"
sys.path.insert(0, str(SCRIPTS))
