import json
import os

class BatchMetricsCollector:

    def __init__(self, path="outputs/metrics"):
        self.path = path
        os.makedirs(self.path, exist_ok=True)

    def save(self, metric):
        file = os.path.join(self.path, f"{metric.batch_id}.json")
        with open(file, "w") as f:
            json.dump(metric.to_dict(), f, indent=2)

    def load_all(self):
        data = []
        if not os.path.exists(self.path):
            return data
            
        for file in os.listdir(self.path):
            if file.endswith(".json"):
                try:
                    with open(os.path.join(self.path, file)) as f:
                        data.append(json.load(f))
                except Exception as e:
                    print(f"[Metrics] Failed to load {file}: {e}")
        return data
