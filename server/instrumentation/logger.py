"""JSON log writer for per-turn metrics and costs."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_LOG_DIR = Path(__file__).parent.parent.parent / "logs"


class MetricsLogger:
    """Writes per-turn JSON metrics to a log file."""

    def __init__(self, log_dir: Path | str | None = None):
        self.log_dir = Path(log_dir) if log_dir else DEFAULT_LOG_DIR
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._session_id: str | None = None
        self._file_path: Path | None = None

    def start_session(self, session_id: str, concept_id: str = "") -> Path:
        """Start a new logging session. Returns the log file path."""
        self._session_id = session_id
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        self._file_path = self.log_dir / f"session_{timestamp}_{session_id[:8]}.jsonl"

        self._write_entry({
            "event": "session_start",
            "session_id": session_id,
            "concept_id": concept_id,
        })

        logger.info(f"Metrics logging to {self._file_path}")
        return self._file_path

    def log_turn(
        self,
        turn_id: int,
        metrics: dict,
        cost: dict | None = None,
        socratic_state: str = "",
        model: str = "",
        transcript: str = "",
        response_length: int = 0,
    ) -> None:
        """Log a completed turn with metrics and optional cost."""
        entry = {
            "event": "turn_complete",
            "turn_id": turn_id,
            "socratic_state": socratic_state,
            "model": model,
            "transcript_length": len(transcript),
            "response_length": response_length,
            "metrics": metrics,
        }
        if cost:
            entry["cost"] = cost

        self._write_entry(entry)

    def log_session_summary(self, metrics_summary: dict, cost_summary: dict | None = None) -> None:
        """Log session-level summary."""
        entry = {
            "event": "session_summary",
            "metrics": metrics_summary,
        }
        if cost_summary:
            entry["cost"] = cost_summary

        self._write_entry(entry)

    def _write_entry(self, entry: dict) -> None:
        """Write a JSON entry to the log file."""
        if not self._file_path:
            return

        entry["timestamp"] = datetime.now(timezone.utc).isoformat()
        entry["session_id"] = self._session_id

        try:
            with open(self._file_path, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to write metrics log: {e}")
