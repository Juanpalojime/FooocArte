# FooocArte

## Professional Visual Generation Engine

**by Soboost Corp.**

FooocArte es la evolución oficial de Fooocus hacia un motor profesional de producción visual, manteniendo su simplicidad, pero ampliando radicalmente su arquitectura interna.

---

## 🚀 ¿Qué es FooocArte?

No es un plugin. No es un fork cosmético. **Es Fooocus redefinido.**

- **Un solo pipeline de inferencia**: Eliminación de fragmentación y duplicidad.
- **Un solo estado global**: Motor de estados síncrono y predecible.
- **Generación secuencial segura**: Flujo de trabajo atómico y robusto.
- **Batch nativo**: El modo por lotes es el estándar, no un añadido.
- **Persistencia y recuperación**: Resiliencia total ante interrupciones.
- **Auditoría y control profesional**: Logs técnicos y filtrado de calidad industrial.

---

## 🧠 Principios Clave

1. **Estabilidad > Velocidad**: La fiabilidad del resultado es nuestra prioridad.
2. **Coherencia > Features**: Una base sólida antes que funciones aisladas.
3. **Estado explícito > Hacks**: Control total sobre el ciclo de vida de la generación.

- **Ingeniería por Prompts**: Basado en el roadmap oficial `FA-XXX`.

1. **Producción real > Demos**: Diseñado para flujos de trabajo profesionales.

---

## 🏗️ Arquitectura

La arquitectura de FooocArte se basa en un núcleo centralizado y modular:

- **Estado global validado**: Motor de estados con transiciones bloqueadas.
- **Loop secuencial controlado**: Cada imagen se procesa como una unidad atómica.
- **Batch como modo nativo**: Optimización de recursos para generación a escala.
- **UI reactiva al core**: La interfaz de Gradio refleja fielmente el estado interno del motor.

> [!TIP]
> **Explora el [Diagrama Visual de Arquitectura](docs/ARCHITECTURE.md#visual-architecture-model)** para entender cómo FooocArte separa las capas de UI, Estado e Inferencia.

---

## 🧪 Calidad y Validación

- **Auto-filtro CLIP**: Clasificación inteligente de resultados.
- **Persistencia incremental**: Guardado tras cada paso exitoso.
- **QA Riguroso**: Consulta nuestro [Checklist QA Final](docs/QA_CHECKLIST.md).

---

## 🏢 Autoría

**FooocArte** es una plataforma diseñada para estudios, agencias y producción a escala desarrollada por **Soboost Corp.**

- [Guía para Contributors Internos](CONTRIBUTING.md)
- [Plan de Release v1.0](docs/RELEASE_PLAN.md)
- [Matriz de Riesgos Profesional](docs/RISK_MATRIX.md)

## 📜 Licencia

*(Sujeto a los términos y estrategia comercial de Soboost Corp.)*
