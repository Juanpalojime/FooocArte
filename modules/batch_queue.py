from collections import deque
import threading

class BatchQueue:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(BatchQueue, cls).__new__(cls)
                    cls._instance.cola = deque()
                    cls._instance.batch_actual = None
        return cls._instance

    def agregar(self, batch_task):
        """
        Agrega una tarea de batch (AsyncTask) a la cola.
        """
        with self._lock:
            self.cola.append(batch_task)
            return len(self.cola)

    def obtener_siguiente(self):
        """
        Obtiene la siguiente tarea si no hay batch activo (o si el activo terminó).
        NOTA: La lógica de 'tick' del usuario asumía que la cola controla el ciclo.
        Aquí, 'worker_thread' pedirá el siguiente.
        """
        with self._lock:
            if self.cola:
                return self.cola.popleft()
            return None
    
    def esta_vacia(self):
        return len(self.cola) == 0

    def longitud(self):
        return len(self.cola)
