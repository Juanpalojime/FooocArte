from typing import Optional, Dict, Any
import ldm_patched.modules.model_management as model_management
from .global_state import GlobalStateMachine
from .state_enum import GlobalState
from ..persistence.storage import PersistenceManager
from ..logging.audit_log import TechnicalLogger

class FooocArteEngine(GlobalStateMachine):
    def __init__(self):
        super().__init__()
        self.persistence = PersistenceManager(self)
        self.logger = TechnicalLogger(self.persistence.log_path)
        self.quality_filter = None
        self.clip_threshold = 0.7

    def init_quality_filter(self):
        if self.quality_filter is None:
            from ..quality.clip_filter import CLIPQualityFilter
            self.quality_filter = CLIPQualityFilter()

    def _transition(self, new_state: GlobalState, metadata: Optional[Dict[str, Any]] = None) -> None:
        super()._transition(new_state, metadata)
        
        # Sync with native Fooocus interruption mechanism
        if new_state == GlobalState.CANCELLING:
            model_management.interrupt_current_processing(True)
        elif new_state == GlobalState.IDLE:
            model_management.interrupt_current_processing(False)
            
        # Trigger persistence on every state change
        self.persistence.save_state_async()

    def tick(self, success: bool = True) -> None:
        super().tick(success)
        self.persistence.save_state_async()
