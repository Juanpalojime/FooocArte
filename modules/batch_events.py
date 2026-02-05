from dataclasses import dataclass
from typing import Optional

@dataclass
class BatchEvent:
    current: int
    total: int
    accepted: int
    rejected: int
    message: str
    eta: Optional[float]
