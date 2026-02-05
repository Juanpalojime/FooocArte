import os
import threading
import uuid
import time
import torch
from enum import Enum

from typing import Dict, Any, Optional
from dataclasses import dataclass, field

from modules.async_worker import process_tasks
from modules.flags import PerformanceFlags
from modules.util import free_cuda_memory
from modules import flags
from modules.controlnet_batch import ControlNetBatchCache
from modules.faceswap_cache import FaceEmbeddingCache
from modules.clip_quality import CLIPQualityFilter
from modules.batch_persistence import BatchPersistence
from modules.batch_presets import BatchPresetManager
from modules.batch_comparator import BatchComparator
from modules.batch_metrics import BatchMetric
from modules.batch_metrics_collector import BatchMetricsCollector


# -----------------------------
# Configuración del Batch
# -----------------------------

@dataclass
class BatchConfig:
    batch_size: int = 10          # 1–50
    max_retries: int = 2
    enable_quality_filter: bool = True
    save_rejected: bool = False
    enable_drive_sync: bool = False
    best_of_n: int = 1            # 1 = standard, >1 = best of N comparator
    input_folder: str = ""        # Path to input folder for batch processing


from modules.batch_state_machine import BatchStateMachine, EstadoBatch

@dataclass
class BatchStats:
    batch_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    accepted: int = 0
    rejected: int = 0
    retries: int = 0
    start_time: float = field(default_factory=time.time)
    
    def eta(self, current, total):
        elapsed = time.time() - self.start_time
        if current == 0:
            return None
        avg = elapsed / current
        return avg * (total - current)


# -----------------------------
# Quality Filter (técnico)
# -----------------------------

def basic_quality_filter(image_tensor: torch.Tensor) -> bool:
    """
    Filtro técnico REAL:
    - Rechaza frames negros
    - Rechaza saturación extrema
    """
    with torch.no_grad():
        mean = image_tensor.mean().item()
        std = image_tensor.std().item()

        # Black frame o washout
        if mean < 0.05 or mean > 0.95:
            return False

        # Colapso de modo
        if std < 0.02:
            return False

    return True


# -----------------------------
# Batch Engine Principal
# -----------------------------

class BatchEngine:

    def __init__(
        self,
        ui_state: Dict[str, Any],
        batch_config: BatchConfig,
        save_callback=None,
        drive_callback=None,
        event_callback=None,
        logger=print
    ):
        """
        ui_state: snapshot completo del estado UI de Fooocus
        save_callback(image, metadata)
        drive_callback(image_path, metadata)
        event_callback(BatchEvent) OR event_callback(current, total, accepted, rejected, message, eta)
        """
        self.ui_state = ui_state
        self.config = batch_config
        # State Machine & Stats
        self.sm = BatchStateMachine() # Strict State Machine
        self.stats = BatchStats()     # Statistics (ID, Accepted, Rejected)
        
        self.save_callback = save_callback
        self.drive_callback = drive_callback
        self.event_callback = event_callback
        self.log = logger
        self.controlnet_cache = ControlNetBatchCache()
        self.face_cache = FaceEmbeddingCache()
        self.clip_filter = None # Lazy init or init here if persistent
        self.persistence = BatchPersistence(self.config.enable_drive_sync)
        if self.config.enable_drive_sync:
             self.persistence.ensure_drive_mount()
             
        self.clip_scores = []
        self.pause_event = threading.Event()
        self.pause_event.set() # Initially running (not paused)

    def pause(self):
        try:
            self.sm.pausar()
            self.pause_event.clear()
            self.emit("Lote pausado.")
            self.log("[Batch] Proceso pausado por usuario.")
        except Exception as e:
            self.log(f"[Batch] Error al pausar: {e}")

    def resume(self):
        try:
            self.sm.reanudar()
            self.pause_event.set()
            self.emit("Lote reanudado.")
            self.log("[Batch] Proceso reanudado.")
        except Exception as e:
            self.log(f"[Batch] Error al reanudar: {e}")

    def emit(self, message: str):
        if self.event_callback:
            try:
                self.event_callback({
                    'batch_id': self.stats.batch_id,
                    'current': self.sm.imagen_actual,
                    'total': self.sm.total,
                    'accepted': self.stats.accepted,
                    'rejected': self.stats.rejected,
                    'status': self.sm.estado.name, # Send String name of Enum
                    'message': message,
                    'eta': self.stats.eta(self.sm.imagen_actual, self.sm.total)
                })
            except Exception as e:
                self.log(f"[Batch] Event callback failed: {e}")

    # -------------------------
    # Ejecución principal
    # -------------------------

    def run(self, task=None):
        try:
            self.sm.iniciar(self.config.batch_size) 
        except Exception as e:
            self.log(f"[Batch] Error inicio: {e}")
            return

        self.log(f"[Batch] Iniciando lote {self.stats.batch_id}")
        self.log(f"[Batch] Imágenes totales: {self.config.batch_size}")
        
        self.emit("Iniciando lote...")
        self.controlnet_cache.clear()
        self.face_cache.clear()
        
        # Init CLIP if enabled and not loaded
        if self.config.enable_quality_filter and self.clip_filter is None:
            self.clip_filter = CLIPQualityFilter()
            
        # --- Folder Mode Branch ---
        if self.config.input_folder and os.path.exists(self.config.input_folder):
             self._run_folder_mode(task=task)
             return
        # --------------------------

        # --- Batch Presets ---
        preset_name = self.ui_state.get("batch_preset")
        if preset_name:
            try:
                manager = BatchPresetManager()
                preset_config = manager.load(preset_name)
                
                self.log(f"[Batch] Applying preset: {preset_config.get('name', preset_name)}")
                if "max_retries" in preset_config:
                    self.config.max_retries = preset_config["max_retries"]
                if "clip_threshold" in preset_config:
                    self.ui_state["clip_threshold"] = preset_config["clip_threshold"]
            except Exception as e:
                self.log(f"[Batch] Failed to load preset {preset_name}: {e}")
        # ---------------------

        try:
            self.sm.preparado()
        except:
            pass

        

        for i in range(self.config.batch_size):
            # --- Cancellation & Pause Check ---
            # Replaced "task.last_stop" logic with SM check
            if task and task.last_stop in ['stop', 'skip']:
                 self.sm.cancelar()
                 self.log("[Batch] Proceso cancelado por el usuario.")
                 self.emit("Lote cancelado.")
                 # Break, but first handle state
                 if self.sm.estado == EstadoBatch.CANCELANDO:
                     self.sm.cancelar_completado()
                 break
            
            # Wait if paused
            if not self.pause_event.is_set():
                 self.sm.pausar() # Transition to PAUSED
                 self.emit("Lote pausado (esperando)...")
                 self.pause_event.wait() # Block
                 self.sm.reanudar() # Transition to RUNNING
                 # Re-check cancellation after wake up
                 if task and task.last_stop in ['stop', 'skip']:
                     self.sm.cancelar()
                     if self.sm.estado == EstadoBatch.CANCELANDO: # Should be
                        self.sm.cancelar_completado()
                     break
            # --------------------------
            
            self.emit(f"Generando imagen {self.sm.imagen_actual + 1}/{self.sm.total}")
            
            # --- ControlNet Cache Optimization ---
            if self.ui_state.get("controlnet_enabled") and "controlnet_image" in self.ui_state:
                try:
                    # Assuming controlnet_image has tobytes() (PIL or Tensor or Numpy)
                    pose_key = hash(self.ui_state["controlnet_image"].tobytes())
                    
                    # Placeholder for the actual compute function if not globally available
                    # In a real integration, this would call the actual preprocessor
                    def compute_controlnet(state):
                        # This would invoke the heavy calculation
                        # For now we assume the pipeline might handle it if we don't, 
                        # but the optimization requires us to pre-calculate and pass it.
                        # Since we don't have the compute_controlnet function defined in this context,
                        # this is structurally ready but might need the import.
                        return None 

                    self.ui_state["controlnet_data"] = self.controlnet_cache.get_or_compute(
                        pose_key,
                        lambda: compute_controlnet(self.ui_state)
                    )
                except Exception as e:
                    self.log(f"[Batch] ControlNet cache warning: {e}")
            # -------------------------------------

            # --- FaceSwap Cache Optimization ---
            if self.ui_state.get("faceswap_enabled") and "faceswap_image" in self.ui_state:
                try:
                    def compute_face_embedding(img):
                        # Placeholder: In strict real implementation this calls the InsightFace model
                        return None
                        
                    self.ui_state["face_embedding"] = self.face_cache.get_embedding(
                        self.ui_state["faceswap_image"],
                        compute_face_embedding
                    )
                except Exception as e:
                    self.log(f"[Batch] FaceSwap cache warning: {e}")
            # -----------------------------------

            # --- Best-of-N Logic ---
            if self.config.best_of_n > 1:
                comparator = BatchComparator()
                success_final = False
                
                for attempt_n in range(self.config.best_of_n):
                     self.emit(f"Generating candidate {attempt_n+1}/{self.config.best_of_n} for image {self.sm.imagen_actual}")
                     # Run without auto-saving
                     success, img, meta, score = self._run_single(i, save_output=False)
                     
                     if success and img:
                         final_score = score if score is not None else 0.0
                         comparator.consider(img, final_score, meta)
                
                best_image, best_meta = comparator.result()
                
                if best_image:
                     # Save the winner
                     try:
                         image_path = None
                         if self.save_callback:
                             image_path = self.save_callback(best_image, best_meta)
                         if self.config.enable_drive_sync and self.drive_callback and image_path:
                             self.drive_callback(image_path, best_meta)
                         
                         success_final = True
                         self.log(f"[Batch] Chosen best of {self.config.best_of_n} with score {comparator.best_score:.4f}")
                         
                         # Add best score to metrics track
                         if comparator.best_score > -1:
                             self.clip_scores.append(comparator.best_score)

                     except Exception as e:
                         self.log(f"[Batch] Error saving best image: {e}")
                         success_final = False
                else:
                     self.log("[Batch] All candidates failed or no image produced")
                     success_final = False
                
                success = success_final
            else:
                # Standard Mode
                success, _, _, score = self._run_single(i, save_output=True)
                if score is not None:
                    self.clip_scores.append(score)
            # -----------------------

            if success:
                self.stats.accepted += 1
            else:
                self.stats.rejected += 1
            
            # Advance State Machine
            self.sm.tick()
            
            self.emit(f"Finished image {self.sm.imagen_actual}")
            
            # --- Persistence Save ---
            self.persistence.save_state(
                self.stats.batch_id,
                {
                    "current": self.sm.imagen_actual,
                    "accepted": self.stats.accepted,
                    "rejected": self.stats.rejected,
                    "retries": self.stats.retries,
                    "total": self.sm.total
                }
            )
            # ------------------------

        # Final state check
        if self.sm.estado == EstadoBatch.COMPLETADO:
            self.emit("Lote completado.")
        self._final_report()
            
    def _run_folder_mode(self, task=None):
        import glob
        import cv2
        import numpy as np
        
        # Store task for inner loop check if passed
        if task:
            self.task = task
        
        # Supported extensions
        exts = ['*.png', '*.jpg', '*.jpeg', '*.webp', '*.bmp']
        files = []
        for ext in exts:
            files.extend(glob.glob(os.path.join(self.config.input_folder, ext)))
            
        files = sorted(list(set(files)))
        self.log(f"[Batch] Folder Mode: Found {len(files)} images in {self.config.input_folder}")
        
        if not files:
            self.emit("No images found in folder.")
            return

        total_images = len(files)
        # Total tasks = files * batch_size
        self.sm.total = total_images * self.config.batch_size
        
        indices = self.ui_state.get("indices", {})
        
        for f_idx, file_path in enumerate(files):
             # --- Cancellation Check ---
            if hasattr(self, 'task') and self.task and self.task.last_stop in ['stop', 'skip']:
                 self.log("[Batch] Process cancelled by user.")
                 break
            # --------------------------
            
            self.log(f"[Batch] Procesando archivo {f_idx+1}/{total_images}: {os.path.basename(file_path)}")
            
            # Load Image (Fooocus expects numpy arrays usually for gr.Image type inputs in pipeline?)
            # Pipeline expects whatever the Gradio components provided.
            # webui.py UOV image is type='numpy'.
            # Image Prompt is type='numpy'.
            try:
                # Load as RGB BGR -> RGB
                img_cv = cv2.imread(file_path)
                if img_cv is None:
                    self.log(f"[Batch] Failed to load {file_path}")
                    continue
                img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
                
                # Injection Logic
                # We need to know where to put it.
                # Heuristic:
                # 1. If UOV/Upscale is enabled? How to know? 
                #    We check if 'uov_method' (index) has a value?
                #    Indices dict should have 'uov_method_index' and 'uov_image_index'.
                #    But simplistic approach: If user checked "Input Image" -> "Upscale", then uov is active.
                #    We can check the actual args list values if we know the index.
                #    Let's assume the UI sends us the target intent or we try both if available.
                #    BETTER: Inject into ALL mapped image slots to be safe, OR prefer IP[0].
                
                # Default: Inject to Image Prompt 0
                if "ip_image_0" in indices:
                     idx = indices["ip_image_0"]
                     if idx < len(self.ui_state["args_list"]):
                         self.ui_state["args_list"][idx] = img_rgb
                         
                # Also Inject to UOV if mapped
                if "uov_image" in indices:
                     idx = indices["uov_image"]
                     if idx < len(self.ui_state["args_list"]):
                         self.ui_state["args_list"][idx] = img_rgb
                         
                # Also Inject to Inpaint if mapped
                if "inpaint_image" in indices:
                     idx = indices["inpaint_image"]
                     if idx < len(self.ui_state["args_list"]):
                         self.ui_state["args_list"][idx] = img_rgb
                         self.ui_state["args_list"][idx] = {"image": img_rgb, "mask": None} # Inpaint often expects dict (sketch)
                         # Wait, Fooocus inpaint input tool='sketch' returns a dict with 'image' and 'mask'.
                         # If we just pass numpy, it might fail if pipeline expects dict.
                         # See webui.py: type='numpy', tool='sketch'. 
                         # Gradio yields {image: np, mask: np}.
                         # So we should format it.
                         mask_dummy = np.zeros(img_rgb.shape[:2], dtype=np.uint8) # No mask? Or full mask?
                         # Usually 0=masked? 
                         # For now let's skip complex Inpaint injection unless requested.
                         pass

            except Exception as e:
                self.log(f"[Batch] Error loading {file_path}: {e}")
                continue

            # Run Batch Loop for this file
            for i in range(self.config.batch_size):
                self.sm.imagen_actual = (f_idx * self.config.batch_size) + i + 1
                self.emit(f"Processing {os.path.basename(file_path)} ({i+1}/{self.config.batch_size})")

                # Re-use run logic?
                # _run_single expects 'index' as loop index, but we can manage local index
                success, _, _, _ = self._run_single(self.sm.imagen_actual, save_output=True)
                
                if success:
                    self.stats.accepted += 1
                else:
                    self.stats.rejected += 1
                
                # Persistence
                self.persistence.save_state(
                    self.stats.batch_id,
                    {
                        "current": self.sm.imagen_actual,
                        "accepted": self.stats.accepted,
                        "rejected": self.stats.rejected,
                        "files_processed": f_idx + 1
                    }
                )

        self._final_report()

    # -------------------------
    # Generación individual
    # -------------------------

    def _run_single(self, index: int, save_output: bool = True):
        attempt = 0
        final_score = None

        while attempt <= self.config.max_retries:
            try:
                self.log(f"[Batch] Image {index+1} attempt {attempt+1}")

                # result = fooocus_run(**self.ui_state)
                
                # Correct Fooocus Async Worker Call
                tasks = [{
                    "task_id": f"batch_{self.stats.batch_id}_{index}_{attempt}",
                    "args": self.ui_state
                }]

                results = process_tasks(
                    tasks=tasks,
                    flags=PerformanceFlags()
                )

                result = results[0]
                image = result["image"]
                metadata = result.get("metadata", {})

                if self.config.enable_quality_filter:
                    # 1. Technical Filter
                    if not basic_quality_filter(result.get("image_tensor", torch.tensor([1.0]))): # Fallback if no tensor
                        raise ValueError("Technical quality filter rejected image (black/noise)")
                    
                    # 2. Semantic CLIP Filter
                    if self.clip_filter:
                        # Assuming result['image'] is a PIL image or list of them. 
                        # Fooocus usually returns singleton list or image. 
                        # We take the first one if list.
                        img_to_score = image
                        if isinstance(image, list):
                            img_to_score = image[0]
                            
                        # Extract prompt from state or metadata
                        prompt = result.get("metadata", {}).get("prompt", self.ui_state.get("prompt", ""))
                        
                        clip_score = self.clip_filter.score(img_to_score, prompt)
                        final_score = clip_score # Capture for return
                        self.log(f"[Batch] CLIP Score: {clip_score:.4f}")
                        
                        if clip_score < self.ui_state.get("clip_threshold", 0.25):
                            raise ValueError(f"CLIP score too low: {clip_score:.4f} < {self.ui_state.get('clip_threshold', 0.25)}")


                # ---- Enriched Metadata ----
                # Inject Batch Context for Drive Sync
                metadata["batch_id"] = self.stats.batch_id
                metadata["preset"] = self.ui_state.get("batch_preset", "None")
                metadata["mode"] = "folder" if self.config.input_folder else "batch"
                if final_score is not None:
                     metadata["clip_score"] = round(final_score, 4)
                     
                # Add input file info if in folder mode
                if "input_file" not in metadata and self.config.input_folder:
                     # Calculate from current index? Or pass it down?
                     # We don't have file path easily here in _run_single unless we pass it.
                     # Let's assume the caller loop set it in ui_state TEMPORARILY or we ignore it.
                     pass

                # ---- Guardado ----
                image_path = None
                if save_output and self.save_callback:
                    image_path = self.save_callback(image, metadata)

                # ---- Drive Sync ----
                if save_output and self.config.enable_drive_sync and self.drive_callback:
                    if image_path:
                        self.drive_callback(image_path, metadata)

                self.log(f"[Batch] Image {index+1} accepted (CLIP: {metadata.get('clip_score', 'N/A')})")
                return True, image, metadata, final_score

            except Exception as e:
                attempt += 1
                self.stats.retries += 1
                self.log(f"[Batch] Image {index+1} failed: {str(e)}")

                if attempt > self.config.max_retries:
                    self.log(f"[Batch] Image {index+1} rejected")

                    if save_output and self.config.save_rejected and self.save_callback:
                        try:
                            self.save_callback(
                                result.get("image"),
                                {**metadata, "rejected": True}
                            )
                        except Exception:
                            pass

                    return False, None, None, None

            finally:
                free_cuda_memory()

    # -------------------------
    # Reporte final
    # -------------------------

    def _final_report(self):
        elapsed = time.time() - self.stats.start_time

        report = {
            "batch_id": self.stats.batch_id,
            "total": self.sm.total,
            "accepted": self.stats.accepted,
            "rejected": self.stats.rejected,
            "retries": self.stats.retries,
            "total_time_sec": round(elapsed, 2),
            "avg_time_per_image": round(elapsed / max(1, self.sm.total), 2)
        }

        self.log("[Batch] Finished")
        self.log(report)
        
        # --- Metrics Collection ---
        try:
            collector = BatchMetricsCollector()
            
            # Safe calcs for stats
            c_avg = 0.0
            c_min = 0.0
            c_max = 0.0
            if self.clip_scores:
                c_avg = sum(self.clip_scores) / len(self.clip_scores)
                c_min = min(self.clip_scores)
                c_max = max(self.clip_scores)
            
            # GPU Info safe retrieval
            gpu_name = "CPU/Unknown"
            vram = 0.0
            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
                vram = torch.cuda.get_device_properties(0).total_memory / 1e9

            metric = BatchMetric(
                batch_id=self.stats.batch_id,
                timestamp=time.time(),
                mode=self.ui_state.get("mode", "unknown"),
                preset=self.ui_state.get("batch_preset"),
                total=self.sm.total,
                accepted=self.stats.accepted,
                rejected=self.stats.rejected,
                avg_time=elapsed / max(1, self.sm.total),
                clip_avg=c_avg,
                clip_min=c_min,
                clip_max=c_max,
                gpu_name=gpu_name,
                vram_gb=vram
            )
            
            collector.save(metric)
            self.log(f"[Batch] Metrics saved for batch {self.state.batch_id}")
        except Exception as e:
            self.log(f"[Batch] Failed to save metrics: {e}")
        # --------------------------
