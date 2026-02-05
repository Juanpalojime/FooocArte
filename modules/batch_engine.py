import time
import uuid
import traceback
import torch

from typing import Dict, Any, Optional
from dataclasses import dataclass, field

from modules.default_pipeline import run as fooocus_run
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


# -----------------------------
# Estado del Batch (runtime)
# -----------------------------

@dataclass
class BatchState:
    batch_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    current_index: int = 0
    accepted: int = 0
    rejected: int = 0
    retries: int = 0
    start_time: float = field(default_factory=time.time)

    def eta(self):
        elapsed = time.time() - self.start_time
        if self.current_index == 0:
            return None
        avg = elapsed / self.current_index
        return avg * (self.total - self.current_index)


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
        self.state = BatchState()
        self.state.total = batch_config.batch_size
        self.save_callback = save_callback
        self.drive_callback = drive_callback
        self.event_callback = event_callback
        self.log = logger
        self.controlnet_cache = ControlNetBatchCache()
        self.face_cache = FaceEmbeddingCache()
        self.clip_filter = None # Lazy init or init here if persistent
        self.persistence = BatchPersistence()
        self.clip_scores = []

    def emit(self, message: str):
        if self.event_callback:
            # We assume the callback matches the signature provided by the user
            # or expects the unpacked values for simplicity with Gradio
            try:
                self.event_callback(
                    current=self.state.current_index,
                    total=self.state.total,
                    accepted=self.state.accepted,
                    rejected=self.state.rejected,
                    message=message,
                    eta=self.state.eta()
                )
            except Exception as e:
                self.log(f"[Batch] Event callback failed: {e}")

    # -------------------------
    # Ejecución principal
    # -------------------------

    def run(self):
        self.log(f"[Batch] Starting batch {self.state.batch_id}")
        self.log(f"[Batch] Total images: {self.config.batch_size}")
        
        self.emit("Initializing batch...")
        self.controlnet_cache.clear()
        self.face_cache.clear()
        
        # Init CLIP if enabled and not loaded
        if self.config.enable_quality_filter and self.clip_filter is None:
            self.clip_filter = CLIPQualityFilter()

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
                # Apply other keys if necessary (enable_faceswap logic handled by UI state usually)
            except Exception as e:
                self.log(f"[Batch] Failed to load preset {preset_name}: {e}")
        # ---------------------

        for i in range(self.config.batch_size):
            self.state.current_index = i + 1
            self.emit(f"Generating image {self.state.current_index}/{self.state.total}")
            
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
                     self.emit(f"Generating candidate {attempt_n+1}/{self.config.best_of_n} for image {self.state.current_index}")
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
                self.state.accepted += 1
            else:
                self.state.rejected += 1
            
            self.emit(f"Finished image {self.state.current_index}")
            
            # --- Persistence Save ---
            self.persistence.save_state(
                self.state.batch_id,
                {
                    "current": self.state.current_index,
                    "accepted": self.state.accepted,
                    "rejected": self.state.rejected,
                    "retries": self.state.retries,
                    "total": self.state.total
                }
            )
            # ------------------------

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

                result = fooocus_run(**self.ui_state)

                image = result["image"]          # torch tensor o PIL según build
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


                # ---- Guardado ----
                image_path = None
                if save_output and self.save_callback:
                    image_path = self.save_callback(image, metadata)

                # ---- Drive Sync ----
                if save_output and self.config.enable_drive_sync and self.drive_callback:
                    if image_path:
                        self.drive_callback(image_path, metadata)

                self.log(f"[Batch] Image {index+1} accepted")
                return True, image, metadata, final_score

            except Exception as e:
                attempt += 1
                self.state.retries += 1
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
        elapsed = time.time() - self.state.start_time

        report = {
            "batch_id": self.state.batch_id,
            "total": self.state.total,
            "accepted": self.state.accepted,
            "rejected": self.state.rejected,
            "retries": self.state.retries,
            "total_time_sec": round(elapsed, 2),
            "avg_time_per_image": round(elapsed / max(1, self.state.total), 2)
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
                batch_id=self.state.batch_id,
                timestamp=time.time(),
                mode=self.ui_state.get("mode", "unknown"),
                preset=self.ui_state.get("batch_preset"),
                total=self.state.total,
                accepted=self.state.accepted,
                rejected=self.state.rejected,
                avg_time=elapsed / max(1, self.state.total),
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
