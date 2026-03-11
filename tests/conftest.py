import sys
from pathlib import Path

# Add server directory to Python path so tests can import server modules
sys.path.insert(0, str(Path(__file__).parent.parent / "server"))
