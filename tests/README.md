# 🧪 FooocArte Test Suite

## Descripción

Suite completa de tests para el sistema de State Machine y Cola de Batches, diseñada para prevenir regresiones y garantizar la estabilidad del sistema.

## Estructura

```
tests/
├── __init__.py
├── requirements.txt
├── test_batch_state_machine.py  # Tests del State Machine
├── test_batch_queue.py           # Tests de la cola FIFO
└── test_ux_rules.py              # Tests de reglas UX
```

## Instalación

```bash
# Instalar dependencias de test
pip install -r tests/requirements.txt
```

## Ejecución

### Ejecutar todos los tests

```bash
pytest -v
```

### Ejecutar tests específicos

```bash
# Solo State Machine
pytest tests/test_batch_state_machine.py -v

# Solo Queue
pytest tests/test_batch_queue.py -v

# Solo UX Rules
pytest tests/test_ux_rules.py -v
```

### Con cobertura

```bash
pytest --cov=modules.batch_state_machine --cov=modules.batch_queue --cov-report=html
```

### Ejecutar tests marcados

```bash
# Solo tests unitarios
pytest -m unit

# Solo tests de integración
pytest -m integration

# Solo tests UX
pytest -m ux
```

## Cobertura de Tests

### `test_batch_state_machine.py`

- ✅ Estado inicial
- ✅ Flujos completos exitosos
- ✅ Pausar y reanudar
- ✅ Cancelación
- ✅ Manejo de errores
- ✅ Reset
- ✅ **Transiciones inválidas** (crítico para prevenir bugs)
- ✅ Casos especiales

### `test_batch_queue.py`

- ✅ Singleton pattern
- ✅ Operaciones básicas (agregar, obtener)
- ✅ Comportamiento FIFO
- ✅ Cola vacía
- ✅ Longitud actualizada
- ✅ Concurrencia básica

### `test_ux_rules.py`

- ✅ Reglas de configuración
- ✅ Reglas de pausa/reanudación
- ✅ Reglas de cancelación
- ✅ Reglas de inicio de batch
- ✅ Reglas de visibilidad UI
- ✅ Combinaciones de reglas

## Regla de Oro

> **Si una transición no tiene test, tarde o temprano se rompe en producción.**

## Beneficios

1. **Prevención de Regresiones**: Detecta cambios que rompen funcionalidad existente
2. **Documentación Viva**: Los tests documentan el comportamiento esperado
3. **Refactorización Segura**: Permite cambiar código con confianza
4. **Debugging Rápido**: Identifica exactamente qué se rompió y dónde
5. **CI/CD Ready**: Listo para integración continua

## Ejemplo de Salida

```
tests/test_batch_state_machine.py::TestEstadoInicial::test_estado_inicial PASSED
tests/test_batch_state_machine.py::TestFlujosExitosos::test_flujo_completo_batch PASSED
tests/test_batch_state_machine.py::TestTransicionesInvalidas::test_tick_sin_iniciar PASSED
tests/test_batch_queue.py::TestFIFOBehavior::test_orden_fifo PASSED
tests/test_ux_rules.py::TestConfigurationRules::test_editar_config_solo_inactivo PASSED

======================== 30 passed in 0.15s ========================
```

## Integración con CI/CD

Agregar a `.github/workflows/tests.yml`:

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -r tests/requirements.txt
      - run: pytest -v --cov
```

## Notas

- Los tests son **independientes** y pueden ejecutarse en cualquier orden
- Cada test limpia su estado (no hay efectos secundarios)
- Los tests de transiciones inválidas son **críticos** para la estabilidad
