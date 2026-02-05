import os
import json
from datetime import datetime
from typing import Optional, Any, Dict
import threading
from ..state.state_enum import GlobalState

class PersistenceManager:
    """Manages atomic JSON persistence for FooocArte state and config."""
    def __init__(self, state_machine):
        self.state_machine = state_machine
        self.base_dir = self._detect_base_dir()
        self.state_path = os.path.join(self.base_dir, "state.json")
        self.config_path = os.path.join(self.base_dir, "config.json")
        self.log_path = os.path.join(self.base_dir, "log.txt")
        
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir, exist_ok=True)

    def _detect_base_dir(self) -> str:
        """Prioritize Google Drive for persistence if available."""
        drive_path = "/content/drive/MyDrive/FooocArte/.fooocarte"
        if os.path.exists("/content/drive"):
            return drive_path
        return os.path.abspath(".fooocarte")

    def save_state_async(self):
        """Save state in a background thread to avoid blocking the pipeline."""
        threading.Thread(target=self.save_state, daemon=True).start()

    def save_state(self):
        data = {
            "state": self.state_machine.state.value,
            "batch": self.state_machine.batch_status,
            "timestamp": datetime.now().isoformat(),
            "metadata": self.state_machine.metadata
        }
        self._atomic_write(self.state_path, data)

    def save_config(self, config: Dict[str, Any]):
        self._atomic_write(self.config_path, config)

    def has_recovery_data(self) -> bool:
        """Check if there is valid recovery data from an interrupted session."""
        if not os.path.exists(self.state_path):
            return False
        try:
            with open(self.state_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("state") not in [GlobalState.IDLE.value, None]
        except:
            return False

    def load_recovery_data(self) -> Optional[Dict[str, Any]]:
        """Load recovery data from disk."""
        if not self.has_recovery_data():
            return None
        try:
            with open(self.state_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return None

    def load_previous_session(self) -> Optional[Dict[str, Any]]:
        """Alias for load_recovery_data for compatibility."""
        return self.load_recovery_data()

    def _atomic_write(self, path: str, data: Any):
        temp_path = path + ".tmp"
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            if os.path.exists(path):
                os.remove(path)
            os.rename(temp_path, path)
        except Exception as e:
            print(f"[FooocArte] Persistence Error saving to {path}: {e}")
