from ...main import engine
from ...core.state.state_enum import GlobalState

def sync_ui_state():
    """Returns visibility and interactivity updates for UI based on engine state."""
    state = engine.state
    
    if state == GlobalState.RUNNING:
        return {
            "generate_button": {"interactive": False},
            "stop_button": {"visible": True},
            "skip_button": {"visible": True}
        }
    else:
        return {
            "generate_button": {"interactive": True},
            "stop_button": {"visible": False},
            "skip_button": {"visible": False}
        }
