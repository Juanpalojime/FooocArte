class ControlNetBatchCache:
    def __init__(self):
        self.cached_inputs = {}

    def get_or_compute(self, key, compute_fn):
        if key not in self.cached_inputs:
            self.cached_inputs[key] = compute_fn()
        return self.cached_inputs[key]

    def clear(self):
        self.cached_inputs.clear()
