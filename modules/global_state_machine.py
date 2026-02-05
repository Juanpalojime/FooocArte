"""
GlobalStateMachine - FooocArte Core State Management
Created by Soboost Corp.

PRINCIPLES:
- One pipeline, one state, one GPU
- Explicit state transitions with validation
- Serializable state for recovery
- No UI logic, no inference logic
- Thread-safe for future extensions

STATES:
- IDLE: System ready, no generation active
- PREPARING: Initializing generation (loading models, preparing inputs)
- RUNNING: Active generation in progress
- PAUSED: Generation temporarily suspended
- CANCELLING: Cancellation in progress
- COMPLETED: Generation finished successfully
- ERROR: Generation failed with error

TRANSITION RULES:
- IDLE → PREPARING (start generation)
- PREPARING → RUNNING (initialization complete)
- PREPARING → ERROR (initialization failed)
- RUNNING → PAUSED (user pause)
- RUNNING → CANCELLING (user cancel)
- RUNNING → COMPLETED (generation finished)
- RUNNING → ERROR (generation failed)
- PAUSED → RUNNING (user resume)
- PAUSED → CANCELLING (user cancel)
- CANCELLING → IDLE (cancellation complete)
- COMPLETED → IDLE (reset for new generation)
- ERROR → IDLE (reset after error)
"""

from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
import threading


class GlobalState(Enum):
    """Global states for FooocArte generation system"""
    IDLE = "idle"
    PREPARING = "preparing"
    RUNNING = "running"
    PAUSED = "paused"
    CANCELLING = "cancelling"
    COMPLETED = "completed"
    ERROR = "error"


class StateTransitionError(Exception):
    """Raised when an invalid state transition is attempted"""
    pass


class GlobalStateMachine:
    """
    Global state machine for FooocArte generation lifecycle.
    
    Manages the single, unified state of the generation system.
    Thread-safe for concurrent state queries.
    
    Example:
        >>> sm = GlobalStateMachine()
        >>> sm.start_generation()
        >>> sm.state
        <GlobalState.PREPARING: 'preparing'>
        >>> sm.mark_ready()
        >>> sm.state
        <GlobalState.RUNNING: 'running'>
    """
    
    # Valid state transitions
    _VALID_TRANSITIONS = {
        GlobalState.IDLE: {GlobalState.PREPARING},
        GlobalState.PREPARING: {GlobalState.RUNNING, GlobalState.ERROR},
        GlobalState.RUNNING: {GlobalState.PAUSED, GlobalState.CANCELLING, 
                             GlobalState.COMPLETED, GlobalState.ERROR},
        GlobalState.PAUSED: {GlobalState.RUNNING, GlobalState.CANCELLING},
        GlobalState.CANCELLING: {GlobalState.IDLE},
        GlobalState.COMPLETED: {GlobalState.IDLE},
        GlobalState.ERROR: {GlobalState.IDLE},
    }
    
    def __init__(self):
        """Initialize state machine in IDLE state"""
        self._state = GlobalState.IDLE
        self._lock = threading.Lock()
        self._metadata: Dict[str, Any] = {}
        self._error_message: Optional[str] = None
        self._state_history = []
        self._transition_timestamp = datetime.now()
    
    @property
    def state(self) -> GlobalState:
        """Get current state (thread-safe)"""
        with self._lock:
            return self._state
    
    @property
    def error_message(self) -> Optional[str]:
        """Get error message if state is ERROR"""
        with self._lock:
            return self._error_message
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Get state metadata (read-only copy)"""
        with self._lock:
            return self._metadata.copy()
    
    def _transition(self, new_state: GlobalState, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Internal method to perform state transition with validation.
        
        Args:
            new_state: Target state
            metadata: Optional metadata to attach to state
            
        Raises:
            StateTransitionError: If transition is invalid
        """
        with self._lock:
            # Validate transition
            valid_next_states = self._VALID_TRANSITIONS.get(self._state, set())
            if new_state not in valid_next_states:
                raise StateTransitionError(
                    f"Invalid transition: {self._state.value} → {new_state.value}. "
                    f"Valid transitions from {self._state.value}: "
                    f"{[s.value for s in valid_next_states]}"
                )
            
            # Record transition
            old_state = self._state
            self._state = new_state
            self._transition_timestamp = datetime.now()
            
            # Update metadata
            if metadata:
                self._metadata.update(metadata)
            
            # Clear error message if leaving ERROR state
            if old_state == GlobalState.ERROR and new_state != GlobalState.ERROR:
                self._error_message = None
            
            # Record in history (keep last 100 transitions)
            self._state_history.append({
                'from': old_state.value,
                'to': new_state.value,
                'timestamp': self._transition_timestamp.isoformat(),
                'metadata': metadata or {}
            })
            if len(self._state_history) > 100:
                self._state_history.pop(0)
    
    # ==========================================
    # PUBLIC API - State Transitions
    # ==========================================
    
    def start_generation(self, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Start a new generation (IDLE → PREPARING).
        
        Args:
            metadata: Optional metadata (e.g., prompt, settings)
            
        Raises:
            StateTransitionError: If not in IDLE state
        """
        self._transition(GlobalState.PREPARING, metadata)
    
    def mark_ready(self) -> None:
        """
        Mark preparation complete (PREPARING → RUNNING).
        
        Raises:
            StateTransitionError: If not in PREPARING state
        """
        self._transition(GlobalState.RUNNING)
    
    def pause(self) -> None:
        """
        Pause generation (RUNNING → PAUSED).
        
        Raises:
            StateTransitionError: If not in RUNNING state
        """
        self._transition(GlobalState.PAUSED)
    
    def resume(self) -> None:
        """
        Resume generation (PAUSED → RUNNING).
        
        Raises:
            StateTransitionError: If not in PAUSED state
        """
        self._transition(GlobalState.RUNNING)
    
    def cancel(self) -> None:
        """
        Cancel generation (RUNNING/PAUSED → CANCELLING).
        
        Raises:
            StateTransitionError: If not in RUNNING or PAUSED state
        """
        self._transition(GlobalState.CANCELLING)
    
    def complete(self, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Mark generation complete (RUNNING → COMPLETED).
        
        Args:
            metadata: Optional metadata (e.g., output paths, stats)
            
        Raises:
            StateTransitionError: If not in RUNNING state
        """
        self._transition(GlobalState.COMPLETED, metadata)
    
    def error(self, error_message: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Mark generation as failed (PREPARING/RUNNING → ERROR).
        
        Args:
            error_message: Description of the error
            metadata: Optional error metadata
            
        Raises:
            StateTransitionError: If not in PREPARING or RUNNING state
        """
        with self._lock:
            self._error_message = error_message
        self._transition(GlobalState.ERROR, metadata)
    
    def reset(self) -> None:
        """
        Reset to IDLE (CANCELLING/COMPLETED/ERROR → IDLE).
        
        Raises:
            StateTransitionError: If not in terminal state
        """
        self._transition(GlobalState.IDLE)
        with self._lock:
            self._metadata.clear()
    
    # ==========================================
    # QUERY API
    # ==========================================
    
    def is_idle(self) -> bool:
        """Check if state is IDLE"""
        return self.state == GlobalState.IDLE
    
    def is_active(self) -> bool:
        """Check if generation is active (PREPARING, RUNNING, or PAUSED)"""
        return self.state in {GlobalState.PREPARING, GlobalState.RUNNING, GlobalState.PAUSED}
    
    def is_running(self) -> bool:
        """Check if state is RUNNING"""
        return self.state == GlobalState.RUNNING
    
    def is_paused(self) -> bool:
        """Check if state is PAUSED"""
        return self.state == GlobalState.PAUSED
    
    def is_terminal(self) -> bool:
        """Check if state is terminal (COMPLETED, ERROR, CANCELLING)"""
        return self.state in {GlobalState.COMPLETED, GlobalState.ERROR, GlobalState.CANCELLING}
    
    def can_start(self) -> bool:
        """Check if new generation can be started"""
        return self.state == GlobalState.IDLE
    
    def can_pause(self) -> bool:
        """Check if generation can be paused"""
        return self.state == GlobalState.RUNNING
    
    def can_resume(self) -> bool:
        """Check if generation can be resumed"""
        return self.state == GlobalState.PAUSED
    
    def can_cancel(self) -> bool:
        """Check if generation can be cancelled"""
        return self.state in {GlobalState.RUNNING, GlobalState.PAUSED}
    
    # ==========================================
    # SERIALIZATION
    # ==========================================
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize state to dictionary.
        
        Returns:
            Dictionary with state, metadata, and error info
        """
        with self._lock:
            return {
                'state': self._state.value,
                'metadata': self._metadata.copy(),
                'error_message': self._error_message,
                'timestamp': self._transition_timestamp.isoformat(),
                'history': self._state_history[-10:]  # Last 10 transitions
            }
    
    def __repr__(self) -> str:
        """String representation"""
        return f"GlobalStateMachine(state={self.state.value})"
    
    def __str__(self) -> str:
        """Human-readable string"""
        with self._lock:
            if self._state == GlobalState.ERROR and self._error_message:
                return f"State: {self._state.value} (Error: {self._error_message})"
            return f"State: {self._state.value}"
