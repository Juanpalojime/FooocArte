from ...main import engine
from ...core.state.state_enum import GlobalState

def sync_ui_state():
    """Returns visibility and interactivity updates for UI based on Figma mapping."""
    state = engine.state
    
    # Default: IDLE state behavior
    updates = {
        "generate_button": {"interactive": True, "visible": True},
        "cancel_status_btn": {"visible": False}, 
        "pause_status_btn": {"visible": False},
        "resume_status_btn": {"visible": False},
        "reset_engine_button": {"visible": True},
        # Sidebar Controls
        "generation_mode": {"interactive": True, "info": ""},
        "batch_size": {"interactive": True, "info": ""},
        "clip_toggle": {"interactive": True, "info": ""},
        "clip_threshold": {"interactive": True, "info": ""},
        "drive_toggle": {"interactive": True, "info": ""},
        # Prompt & Main Panel
        "prompt": {"interactive": True, "info": ""}
    }

    lock_msg = "Bloqueado durante la generación"

    if state == GlobalState.RUNNING:
        updates["generate_button"]["interactive"] = False
        updates["cancel_status_btn"]["visible"] = True
        updates["pause_status_btn"]["visible"] = True
        # Lock Sidebar/Inputs
        updates["generation_mode"].update({"interactive": False, "info": lock_msg})
        updates["batch_size"].update({"interactive": False, "info": lock_msg})
        updates["prompt"].update({"interactive": False, "info": lock_msg})
        updates["clip_toggle"].update({"interactive": False, "info": lock_msg})
        updates["drive_toggle"].update({"interactive": False, "info": lock_msg})
    
    elif state == GlobalState.PAUSED:
        updates["generate_button"]["interactive"] = False
        updates["cancel_status_btn"]["visible"] = True
        updates["resume_status_btn"]["visible"] = True
        # Keep Sidebar locked
        updates["generation_mode"].update({"interactive": False, "info": "Pausado"})
        updates["batch_size"].update({"interactive": False, "info": "Pausado"})
        updates["prompt"].update({"interactive": False, "info": "Pausado"})
        
    elif state in [GlobalState.PREPARING, GlobalState.CANCELLING]:
        updates["generate_button"]["interactive"] = False
        updates["cancel_status_btn"]["visible"] = True
        msg = "Preparando..." if state == GlobalState.PREPARING else "Cancelando..."
        for k in ["generation_mode", "batch_size", "prompt", "clip_toggle", "drive_toggle"]:
            updates[k].update({"interactive": False, "info": msg})

    elif state == GlobalState.ERROR:
        updates["generate_button"]["interactive"] = False
        updates["generation_mode"].update({"interactive": False, "info": "Error de Motor"})
        updates["prompt"].update({"interactive": False, "info": "Error de Motor"})

    return updates
