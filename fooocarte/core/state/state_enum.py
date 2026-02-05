from enum import Enum

class GlobalState(Enum):
    IDLE = "IDLE"
    PREPARING = "PREPARING"
    RUNNING = "EJECUTANDO"
    PAUSED = "EN_PAUSA"
    CANCELLING = "CANCELANDO"
    COMPLETADO = "COMPLETADO"
    ERROR = "ERROR"
