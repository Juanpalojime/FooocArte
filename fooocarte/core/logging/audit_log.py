from datetime import datetime

class TechnicalLogger:
    """Handles professional generation logging (log.txt)."""
    def __init__(self, path: str):
        self.path = path

    def log(self, status: str, prompt: str, result: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] [{status}] PROMPT: \"{prompt[:100]}...\" | RESULT: {result}\n"
        try:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(entry)
        except Exception as e:
            print(f"[FooocArte] Logging error: {e}")
