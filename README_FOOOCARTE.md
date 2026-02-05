
# FooocArte (Fooocus Fork)

**FooocArte** is a production-optimized fork of Fooocus designed for high-volume, professional workflows. It maintains 100% compatibility with the original Fooocus UI while adding powerful batch processing and auditing capabilities.

## Key Features

### 1. Advanced Batch Engine

* **Sequential Processing**: Optimized for stability on 8GB-16GB VRAM GPUs (e.g. T4).
* **Resumable Sessions**: Automatic JSON persistence allows resuming batches after crashes.
* **Metrics & Telemetry**: Internal dashboard tracks accepted/rejected rates, CLIP scores, and GPU usage.

### 2. Auto-Quality Assurance (QA)

* **CLIP Scoring**: Automatically scores images against prompts.
* **Auto-Filter**: Rejects images below a configurable semantic threshold (e.g., < 0.25).
* **Technical Filter**: Detects and rejects black frames or noise collapse.

### 3. Industry Presets

* Pre-configured optimization profiles for specific use cases:
  * **Portrait**: Optimized for face coherence (FaceSwap enabled, High CLIP threshold).
  * **Ecommerce**: Optimized for fidelity and product details.
  * **Branding**: Balanced settings for asset consistency.

### 4. Smart Caching

* **ControlNet Cache**: Reuses pose/depth maps across the batch (10x speedup for same-pose batches).
* **FaceSwap Cache**: Computes InsightFace embeddings once per batch.

### 5. Best-of-N Selector

* Generates N candidates per requested image.
* Automatically selects and saves only the one with the highest CLIP score.

## Installation

Follow the standard Fooocus installation instructions.

## Usage

1. Launch `run.bat` or `python launch.py`.
2. Check **"Batch Mode"** in the Advanced sidebar.
3. Configure **Batch Count**, **Preset**, and **Auto-filter** settings.
4. Click **Generate**.

## Project Structure

* `modules/batch_engine.py`: Core logic for sequential batching.
* `modules/batch_metrics.py`: Telemetry data models.
* `modules/batch_presets.py`: JSON configuration loader.
* `presets/batch_industries/`: Industry-specific configuration files.

---
*Based on Fooocus by lllyasviel.*
