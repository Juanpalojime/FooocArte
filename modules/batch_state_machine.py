from enum import Enum, auto

class EstadoBatch(Enum):
    INACTIVO = auto()
    PREPARANDO = auto()
    EJECUTANDO = auto()
    EN_PAUSA = auto()
    CANCELANDO = auto()
    COMPLETADO = auto()
    ERROR = auto()


class BatchStateMachine:
    def __init__(self):
        self.estado = EstadoBatch.INACTIVO
        self.imagen_actual = 0
        self.total = 0
        self.error = None

    def iniciar(self, total):
        self._assert_estado(EstadoBatch.INACTIVO)
        if total <= 0:
            raise ValueError("total debe ser > 0")
        self.total = total
        self.imagen_actual = 0
        self.estado = EstadoBatch.PREPARANDO

    def preparado(self):
        self._assert_estado(EstadoBatch.PREPARANDO)
        self.estado = EstadoBatch.EJECUTANDO

    def tick(self):
        self._assert_estado(EstadoBatch.EJECUTANDO)
        self.imagen_actual += 1
        if self.imagen_actual >= self.total:
            self.estado = EstadoBatch.COMPLETADO

    def pausar(self):
        self._assert_estado(EstadoBatch.EJECUTANDO)
        self.estado = EstadoBatch.EN_PAUSA

    def reanudar(self):
        self._assert_estado(EstadoBatch.EN_PAUSA)
        self.estado = EstadoBatch.EJECUTANDO

    def cancelar(self):
        if self.estado in (EstadoBatch.EJECUTANDO, EstadoBatch.EN_PAUSA, EstadoBatch.PREPARANDO):
             self.estado = EstadoBatch.CANCELANDO
        # Si ya está INACTIVO o COMPLETADO o ERROR, no hace nada o lanza error? El user code dice:
        # if self.estado in (EstadoBatch.EJECUTANDO, EstadoBatch.EN_PAUSA): self.estado = EstadoBatch.CANCELANDO
        # Agregué PREPARANDO por robustez.

    def cancelar_completado(self):
        self._assert_estado(EstadoBatch.CANCELANDO)
        self.estado = EstadoBatch.COMPLETADO

    def error_fatal(self, mensaje):
        self.estado = EstadoBatch.ERROR
        self.error = mensaje

    def reset(self):
        if self.estado not in (EstadoBatch.COMPLETADO, EstadoBatch.ERROR):
            raise RuntimeError(f"reset() debe estar en COMPLETADO o ERROR, actual: {self.estado}")
        self.estado = EstadoBatch.INACTIVO
        self.imagen_actual = 0
        self.total = 0
        self.error = None

    def _assert_estado(self, esperado):
        if self.estado != esperado:
            raise RuntimeError(
                f"Transición inválida: {self.estado} → {esperado}"
            )
