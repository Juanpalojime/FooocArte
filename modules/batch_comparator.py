class BatchComparator:

    def __init__(self):
        self.best_score = -1
        self.best_image = None
        self.best_metadata = None

    def consider(self, image, score, metadata):
        if score > self.best_score:
            self.best_score = score
            self.best_image = image
            self.best_metadata = metadata

    def result(self):
        return self.best_image, self.best_metadata
