import json
import os

class BatchPresetManager:

    # Adjust path to be absolute or relative to execution context if needed.
    # For now relying on default or passed path.
    def __init__(self, path="presets/batch_industries"):
        self.path = path

    def load(self, name):
        # Allow loading by simple name (e.g. "portrait") even if file is "portrait.json"
        if not name.endswith(".json"):
            filename = f"{name}.json"
        else:
            filename = name
            
        file = os.path.join(self.path, filename)
        if not os.path.exists(file):
             # Fallback to check if it's a path relative to root if default fails
             if os.path.exists(name):
                 file = name
             else:
                 raise FileNotFoundError(f"Preset {name} not found at {file}")

        with open(file, "r") as f:
            return json.load(f)
