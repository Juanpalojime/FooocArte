# 📊 MATRIZ DE RIESGOS — FooocArte v1.0

A continuación se detallan los riesgos identificados en la arquitectura y operación de FooocArte, junto con sus estrategias de mitigación integradas en el Core.

| Riesgo | Impacto | Probabilidad | Mitigación |
| :--- | :--- | :--- | :--- |
| **Paralelismo accidental** | Crítico | Media | Estado global estricto + Loop secuencial único. |
| **Estado desincronizado** | Crítico | Baja | Transiciones validadas via RLock. |
| **UI rompe ejecución** | Alto | Media | Guards por estado en bindings de Gradio. |
| **Pérdida de progreso** | Alto | Media | Persistencia incremental tras cada tick del motor. |
| **CLIP bloquea render** | Medio | Baja | Post-proceso desacoplado del pipeline de inferencia. |
| **OOM no controlado** | Alto | Media | Estado `ERROR` controlado + Liberación de recursos. |
| **Alucinación de IA** | Crítico | Alta | Roadmap de Commits Atómicos (FA-XXX) + Commits pequeños. |

---
**FooocArte Philosophy**: *Predecible, estable, auditable.*
