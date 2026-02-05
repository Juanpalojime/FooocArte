from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class BatchMetric:
    batch_id: str
    timestamp: float
    mode: str                 # txt2img, img2img, faceswap
    preset: str | None
    total: int
    accepted: int
    rejected: int
    avg_time: float
    clip_avg: float
    clip_min: float
    clip_max: float
    gpu_name: str
    vram_gb: float

    def to_dict(self):
        return asdict(self)
