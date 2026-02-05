# 👥 GUÍA PARA CONTRIBUTORS INTERNOS

## FooocArte — Soboost Corp

### 🎯 Objetivo del Contributor

No añadir features por volumen. El objetivo es **mantener la estabilidad, coherencia y calidad suprema** del motor.

---

### 🧠 Reglas de Oro

1. **Un commit = una responsabilidad**: No mezclar refactor con nuevas lógicas.
2. **Nunca tocar GPU directamente**: Toda interacción con modelos debe pasar por el Core/Pipeline.
3. **Nunca romper el estado global**: Las transiciones deben ser validadas por `GlobalStateMachine`.
4. **Nunca paralelizar inferencia**: El pipeline es secuencial por diseño (Estabilidad VRAM).
5. **Nunca asumir estados implícitos**: Si no está definido en el motor de estados, no existe.

---

### 🧱 Flujo de Trabajo

1. Elegir un commit/tarea del roadmap oficial.
2. Ejecutar el prompt de diseño correspondiente para validación.
3. Implementar en un módulo único y aislado.
4. Realizar pruebas manuales y automáticas (Checklist QA).
5. Crear el Pull Request utilizando la [Plantilla Oficial](.github/pull_request_template.md).
6. Code review obligatorio por un experto de Soboost Corp.
7. Merge a la rama principal.

---

### 🚫 Prohibiciones Absolutas

- Refactors masivos sin ticket previo.
- "Optimizaciones" de rendimiento sin métricas comparativas.
- Cambios de arquitectura sin consenso del Lead Architect.
- Implementación de features fuera del roadmap de Soboost Corp.

---

### 🧪 Testing Obligatorio

Todo Pull Request debe obligatoriamente:

- Pasar el **Checklist QA** de su área de impacto.
- Adjuntar evidencia técnica (logs de `audit_log.py` / capturas de UI).
- No introducir nuevos warnings o errores de linting.

---

### 🧠 Filosofía FooocArte
>
> FooocArte no es rápido por accidente. Es **estable por diseño**.
