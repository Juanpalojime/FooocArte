"""
FooocArte Core - Soboost Corp.

This module centralizes the global state and core principles of FooocArte.
It implements the singleton GlobalStateMachine and ensures synchronization
with native Fooocus mechanisms.

PRINCIPLES:
1. Un solo pipeline de inferencia.
2. Un solo estado global.
3. Una sola GPU activa (GPU 0).
4. El modo Batch es nativo (no externo).
"""

import os
import threading
from modules.global_state_machine import GlobalStateMachine, GlobalState
import ldm_patched.modules.model_management as model_management

# Singleton implementation of the Global State Machine
class FooocArteStateMachine(GlobalStateMachine):
    def _transition(self, new_state: GlobalState, metadata: Optional[Dict[str, Any]] = None) -> None:
        super()._transition(new_state, metadata)
        
        # Sync with native Fooocus interruption mechanism
        if new_state == GlobalState.CANCELLING:
            model_management.interrupt_current_processing(True)
        elif new_state == GlobalState.IDLE:
            model_management.interrupt_current_processing(False)

# Global Instance
state = FooocArteStateMachine()

def get_state():
    """Access the global FooocArte state"""
    return state

# Principles Document for internal reference
PRINCIPLES = """
FOOOARTE - NÚCLEO ARQUITECTÓNICO
--------------------------------
1. PIPELINE ÚNICO: Todas las generaciones deben pasar por modules.async_worker.
2. ESTADO ÚNICO: modules.fooocarte_core.state es la única fuente de verdad.
3. GPU ÚNICA: Solo se permite el uso de la GPU 0 para tareas de inferencia.
4. SIN PARALELISMO: No se permite torch.multiprocessing ni hilos de inferencia paralelos.
"""
