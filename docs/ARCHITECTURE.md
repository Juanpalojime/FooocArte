# FooocArte Architecture Overview

## Visual Architecture Model

### Modelo de Operación

**Core-driven / State-first / Single-pipeline**

```mermaid
graph TD
    subgraph UI_Layer [UI Layer]
        UI["UI (React / Gradio)"]
    end

    subgraph Core_Engine [FooocArte Core Engine]
        GSM["GlobalStateMachine (Single Source of Truth)"]
        GC["Generation Controller"]
        SL["Sequential Loop (SINGLE / BATCH)"]
    end

    subgraph Inference_Layer [Inference Layer]
        SDXL["SDXL / ControlNet Core"]
    end

    subgraph Post_Processing [Post-Generation Hooks]
        CF["CLIP Filter"]
        LOG["Logging"]
        PER["Persistence"]
    end

    UI -- "requests only" --> GSM
    GSM -- "validated transitions" --> GC
    GC --> SL
    SL --> SDXL
    SDXL --> CF
    SDXL --> LOG
    SDXL --> PER
    PER -- "updates state" --> GSM
```

### 🔑 Claves del Diseño

- **La UI nunca toca GPU**: Toda la lógica de inferencia está aislada en el Core.
- **El estado nunca vive en la UI**: El motor de estados en Python es el único dueño de la verdad.
- **El loop no paraleliza**: Garantiza estabilidad y predictibilidad en la gestión de VRAM.
- **El pipeline no se duplica**: Arquitectura limpia sin fragmentación de procesos.

## Unified Core Design

FooocArte replaces the fragmented logic of Fooocus with a centralized package structure located in `fooocarte/`.

### 📂 Directory Hierarchy

- **`core/state/`**: The heart of the system.
  - `GlobalStateMachine`: Manages `IDLE`, `PREPARING`, `RUNNING`, `CANCELLING`, `ERROR`.
  - `Transitions`: Specialized engine logic and thread-safe operations (RLock).
- **`core/generation/`**:
  - `generator.py`: Atomic unit of generation (`generate_once`).
  - `loop.py`: Orchestrates sequential execution.
- **`core/persistence/`**:
  - `storage.py`: Atomic JSON writing for `state.json` and `config.json`.
  - `recovery.py`: Logic to detect and resume interrupted sessions.
- **`core/quality/`**:
  - `clip_filter.py`: Scoring engine for output validation.
- **`ui/bindings/`**:
  - `state_binding.py`: Maps engine states to Gradio component updates.

## State Machine Lifecycle

```mermaid
graph TD
    IDLE --> PREPARING
    PREPARING --> RUNNING
    RUNNING --> COMPLETADO
    COMPLETADO --> IDLE
    RUNNING --> CANCELLING
    CANCELLING --> IDLE
    RUNNING --> ERROR
    ERROR --> IDLE
```

## Resilience and Persistence

The system performs an **atomic sync** of the global state after every successful generation tick. This ensures that even in the event of a hard crash (OOM, Power Loss), the session can be resumed from the very next image index.
