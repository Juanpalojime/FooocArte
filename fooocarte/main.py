from .core.state.transitions import FooocArteEngine
from .core.state.state_enum import GlobalState

# Singleton Instance
engine = FooocArteEngine()

# Shorthand for easier access
state = engine

def get_engine() -> FooocArteEngine:
    return engine

PRINCIPLES = """
FOOOARTE - NÚCLEO ARQUITECTÓNICO
--------------------------------
1. PIPELINE ÚNICO: Todas las generaciones deben pasar por modules.async_worker.
2. ESTADO ÚNICO: fooocarte.state es la única fuente de verdad.
3. GPU ÚNICA: Solo se permite el uso de la GPU 0 para tareas de inferencia.
4. SIN PARALELISMO: No se permite torch.multiprocessing ni hilos de inferencia paralelos.
"""
