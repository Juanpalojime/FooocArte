import threading
from typing import Optional, Dict, Any
from .state_enum import GlobalState

class GlobalStateMachine:
    def __init__(self):
        self._state = GlobalState.IDLE
        self._lock = threading.RLock()
        self._metadata = {}
        
        # Batch Counters (Fase 15)
        self._batch_current = 0
        self._batch_total = 0
        self._valid_images = 0
        self._mode = "SINGLE" # SINGLE | BATCH
        self._paused = False

    def reset(self):
        with self._lock:
            self._state = GlobalState.IDLE
            self._batch_current = 0
            self._batch_total = 0
            self._valid_images = 0
            self._metadata = {}
            self._paused = False
            print("[FooocArte] State Machine RESET to IDLE")

    @property
    def state(self) -> GlobalState:
        with self._lock:
            return self._state

    @property
    def metadata(self) -> Dict[str, Any]:
        with self._lock:
            return self._metadata.copy()

    @property
    def batch_status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "current": self._batch_current,
                "total": self._batch_total,
                "valid": self._valid_images,
                "mode": self._mode,
                "state": self._state.value,
                "paused": self._paused
            }

    @property
    def batch_current(self) -> int:
        return self._batch_current

    @property
    def batch_total(self) -> int:
        return self._batch_total

    @property
    def valid_images(self) -> int:
        return self._valid_images

    def can_start(self) -> bool:
        return self.state in [GlobalState.IDLE, GlobalState.COMPLETADO, GlobalState.ERROR]

    def start_generation(self, metadata: Optional[Dict[str, Any]] = None, total: int = 1) -> None:
        with self._lock:
            if not self.can_start():
                raise RuntimeError(f"Cannot start from state {self._state}")
            
            # Reset Batch Counters
            self._batch_current = 0
            self._batch_total = total
            self._valid_images = 0
            self._mode = "BATCH" if total > 1 else "SINGLE"
            
            self._transition(GlobalState.PREPARING, metadata)
            self._transition(GlobalState.RUNNING)

    def tick(self, success: bool = True) -> None:
        with self._lock:
            self._batch_current += 1
            if success:
                self._valid_images += 1
            print(f"[FooocArte] Tick: {self._batch_current}/{self._batch_total} (Valid: {self._valid_images})")

    def mark_ready(self) -> None:
        with self._lock:
            self._transition(GlobalState.RUNNING)

    def pause(self) -> None:
        with self._lock:
            self._paused = True
            print("[FooocArte] Execution PAUSED")

    def resume(self) -> None:
        with self._lock:
            self._paused = False
            print("[FooocArte] Execution RESUMED")

    def is_paused(self) -> bool:
        with self._lock:
            return self._paused

    def complete(self) -> None:
        with self._lock:
            self._transition(GlobalState.COMPLETADO)
            self._transition(GlobalState.IDLE)

    def error(self, message: str) -> None:
        with self._lock:
            print(f"[FooocArte] ERROR: {message}")
            self._transition(GlobalState.ERROR)

    def cancel(self) -> None:
        with self._lock:
            if self._state == GlobalState.RUNNING:
                self._transition(GlobalState.CANCELLING)

    def finish(self, success: bool = True) -> None:
        with self._lock:
            new_state = GlobalState.COMPLETADO if success else GlobalState.ERROR
            self._transition(new_state)
            self._transition(GlobalState.IDLE)

    def _transition(self, new_state: GlobalState, metadata: Optional[Dict[str, Any]] = None) -> None:
        print(f"[FooocArte] State Change: {self._state.name} -> {new_state.name}")
        self._state = new_state
        if metadata:
            self._metadata.update(metadata)
