from PIL import Image
from ..state.state_enum import GlobalState

def generate_once(engine, all_steps, async_task, callback, controlnet_canny_path, controlnet_cpds_path, current_task_id,
                  denoising_strength, final_scheduler_name, goals, initial_latent, steps, switch, task, loras,
                  tiled, use_expansion, width, height, current_progress, preparation_steps, total_count,
                  show_intermediate_results, persist_image=True):
    """
    FooocArte Atomic Generation: Processes a single image in the pipeline.
    This is the core unit of work for sequential batching.
    """
    # Import process_task here to avoid circular dependencies if necessary, 
    # but since it's in async_worker, we'll assume it's passed or available.
    from modules.async_worker import process_task
    
    print(f"[FooocArte] Atomic Generation Start: Image {current_task_id + 1}/{total_count}")
    
    # Internal process call
    imgs, img_paths, current_progress = process_task(
        all_steps, async_task, callback, controlnet_canny_path, controlnet_cpds_path, 
        current_task_id, denoising_strength, final_scheduler_name, goals, initial_latent, 
        steps, switch, task['c'], task['uc'], task, loras, tiled, use_expansion, 
        width, height, current_progress, preparation_steps, total_count, 
        show_intermediate_results, persist_image
    )
    
    # Phase 18: Quality Filter
    is_valid = True
    if engine.clip_threshold > 0:
        engine.init_quality_filter()
        if engine.quality_filter:
            # Convert first image to PIL for CLIP
            pil_img = Image.fromarray(imgs[0])
            score = engine.quality_filter.score(pil_img, async_task.prompt)
            print(f"[FooocArte] CLIP Quality Score: {score:.4f} (Threshold: {engine.clip_threshold})")
            if score < engine.clip_threshold:
                is_valid = False
                print(f"[FooocArte] Image {current_task_id + 1} REJECTED by CLIP filter.")

    # Phase 20: Technical Logging
    status = "APPROVED" if is_valid else "REJECTED"
    result_path = img_paths[0] if img_paths else "N/A"
    engine.logger.log(status, async_task.prompt, result_path)

    # Tick the state machine after atomic success
    engine.tick(success=is_valid)
    
    return imgs, img_paths, current_progress, score if 'score' in locals() else 1.0, is_valid
