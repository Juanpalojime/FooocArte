import os
import json
from .storage import PersistenceManager
from ..state.state_enum import GlobalState

class RecoveryManager:
    """Handles auto-resume logic based on persisted state."""
    def __init__(self, engine):
        self.engine = engine
        self.persistence = engine.persistence

    def check_for_recovery(self):
        data = self.persistence.load_previous_session()
        if not data:
            return None
            
        print(f"[FooocArte] Recovery: System was interrupted at image {data['batch']['current'] + 1}")
        return data
