import json
import os
import time

class BatchPersistence:

    def __init__(self, base_path="outputs/batches"):
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)

    def _path(self, batch_id):
        return os.path.join(self.base_path, f"{batch_id}.json")

    def save_state(self, batch_id, state: dict):
        payload = {
            "timestamp": time.time(),
            "state": state
        }
        with open(self._path(batch_id), "w") as f:
            json.dump(payload, f, indent=2)

    def load_state(self, batch_id):
        path = self._path(batch_id)
        if not os.path.exists(path):
            return None
        with open(path, "r") as f:
            return json.load(f)
