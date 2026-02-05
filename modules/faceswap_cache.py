class FaceEmbeddingCache:
    def __init__(self):
        self.cache = {}

    def get_embedding(self, image, compute_fn):
        key = hash(image.tobytes())
        if key not in self.cache:
            self.cache[key] = compute_fn(image)
        return self.cache[key]

    def clear(self):
        self.cache.clear()
