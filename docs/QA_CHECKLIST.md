# 🧪 CHECKLIST QA FINAL — FooocArte v1.0

## 🧠 Estado y Flujo

- [x] No existe más de un estado activo.
- [x] Ninguna acción salta validaciones.
- [x] Estados serializan y deserializan correctamente.

## 🔁 Generación

- [x] Solo una inferencia activa.
- [x] `generate_once()` reutilizado siempre.
- [x] VRAM estable en batches largos.

## 📦 Batch

- [x] Batch cuenta solo imágenes aprobadas.
- [x] Pausa / reanudar exacto.
- [x] Cancelación limpia.

## 💾 Persistencia

- [x] `state.json` se actualiza tras cada imagen.
- [x] `config.json` es inmutable.
- [x] Crash → recovery funcional.

## 🧠 CLIP Filter

- [x] No afecta inferencia.
- [x] Umbral configurable.
- [x] No bloquea batch.

## 🎛️ UI

- [x] Controles reflejan estado real.
- [x] No edición durante RUNNING.
- [x] No lógica crítica en frontend.

## 📊 Logging

- [x] `log.txt` completo.
- [x] Errores registrados.
- [x] Timestamps correctos.

## 🚨 Estabilidad

- [x] OOM pasa a ERROR controlado.
- [x] Recursos liberados.
- [x] No deadlocks (Implementado via RLock).
