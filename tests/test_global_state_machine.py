"""
Test suite for GlobalStateMachine
FooocArte by Soboost Corp.

Tests:
- All valid state transitions
- All invalid state transitions
- Thread safety
- Serialization
- Query methods
- Error handling
"""

import pytest
import threading
import time
from modules.global_state_machine import (
    GlobalStateMachine,
    GlobalState,
    StateTransitionError
)


class TestGlobalStateMachine:
    """Test suite for GlobalStateMachine"""
    
    def test_initial_state(self):
        """Test that state machine starts in IDLE"""
        sm = GlobalStateMachine()
        assert sm.state == GlobalState.IDLE
        assert sm.is_idle()
        assert not sm.is_active()
        assert sm.can_start()
    
    def test_valid_transition_idle_to_preparing(self):
        """Test IDLE → PREPARING transition"""
        sm = GlobalStateMachine()
        sm.start_generation({'prompt': 'test'})
        assert sm.state == GlobalState.PREPARING
        assert sm.metadata['prompt'] == 'test'
    
    def test_valid_transition_preparing_to_running(self):
        """Test PREPARING → RUNNING transition"""
        sm = GlobalStateMachine()
        sm.start_generation()
        sm.mark_ready()
        assert sm.state == GlobalState.RUNNING
        assert sm.is_running()
        assert sm.is_active()
    
    def test_valid_transition_running_to_paused(self):
        """Test RUNNING → PAUSED transition"""
        sm = GlobalStateMachine()
        sm.start_generation()
        sm.mark_ready()
        sm.pause()
        assert sm.state == GlobalState.PAUSED
        assert sm.is_paused()
        assert sm.can_resume()
    
    def test_valid_transition_paused_to_running(self):
        """Test PAUSED → RUNNING transition"""
        sm = GlobalStateMachine()
        sm.start_generation()
        sm.mark_ready()
        sm.pause()
        sm.resume()
        assert sm.state == GlobalState.RUNNING
        assert sm.is_running()
    
    def test_valid_transition_running_to_completed(self):
        """Test RUNNING → COMPLETED transition"""
        sm = GlobalStateMachine()
        sm.start_generation()
        sm.mark_ready()
        sm.complete({'images': 5})
        assert sm.state == GlobalState.COMPLETED
        assert sm.is_terminal()
        assert sm.metadata['images'] == 5
    
    def test_valid_transition_running_to_cancelling(self):
        """Test RUNNING → CANCELLING transition"""
        sm = GlobalStateMachine()
        sm.start_generation()
        sm.mark_ready()
        sm.cancel()
        assert sm.state == GlobalState.CANCELLING
        assert sm.is_terminal()
    
    def test_valid_transition_paused_to_cancelling(self):
        """Test PAUSED → CANCELLING transition"""
        sm = GlobalStateMachine()
        sm.start_generation()
        sm.mark_ready()
        sm.pause()
        sm.cancel()
        assert sm.state == GlobalState.CANCELLING
    
    def test_valid_transition_preparing_to_error(self):
        """Test PREPARING → ERROR transition"""
        sm = GlobalStateMachine()
        sm.start_generation()
        sm.error("Model loading failed")
        assert sm.state == GlobalState.ERROR
        assert sm.error_message == "Model loading failed"
        assert sm.is_terminal()
    
    def test_valid_transition_running_to_error(self):
        """Test RUNNING → ERROR transition"""
        sm = GlobalStateMachine()
        sm.start_generation()
        sm.mark_ready()
        sm.error("CUDA out of memory")
        assert sm.state == GlobalState.ERROR
        assert sm.error_message == "CUDA out of memory"
    
    def test_valid_transition_completed_to_idle(self):
        """Test COMPLETED → IDLE transition"""
        sm = GlobalStateMachine()
        sm.start_generation()
        sm.mark_ready()
        sm.complete()
        sm.reset()
        assert sm.state == GlobalState.IDLE
        assert sm.can_start()
        assert len(sm.metadata) == 0
    
    def test_valid_transition_error_to_idle(self):
        """Test ERROR → IDLE transition"""
        sm = GlobalStateMachine()
        sm.start_generation()
        sm.error("Test error")
        sm.reset()
        assert sm.state == GlobalState.IDLE
        assert sm.error_message is None
    
    def test_valid_transition_cancelling_to_idle(self):
        """Test CANCELLING → IDLE transition"""
        sm = GlobalStateMachine()
        sm.start_generation()
        sm.mark_ready()
        sm.cancel()
        sm.reset()
        assert sm.state == GlobalState.IDLE
    
    def test_invalid_transition_idle_to_running(self):
        """Test invalid IDLE → RUNNING transition"""
        sm = GlobalStateMachine()
        with pytest.raises(StateTransitionError) as exc_info:
            sm.mark_ready()
        assert "Invalid transition" in str(exc_info.value)
        assert "idle → running" in str(exc_info.value)
    
    def test_invalid_transition_preparing_to_paused(self):
        """Test invalid PREPARING → PAUSED transition"""
        sm = GlobalStateMachine()
        sm.start_generation()
        with pytest.raises(StateTransitionError):
            sm.pause()
    
    def test_invalid_transition_running_to_preparing(self):
        """Test invalid RUNNING → PREPARING transition"""
        sm = GlobalStateMachine()
        sm.start_generation()
        sm.mark_ready()
        with pytest.raises(StateTransitionError):
            sm.start_generation()
    
    def test_invalid_transition_completed_to_running(self):
        """Test invalid COMPLETED → RUNNING transition"""
        sm = GlobalStateMachine()
        sm.start_generation()
        sm.mark_ready()
        sm.complete()
        with pytest.raises(StateTransitionError):
            sm.mark_ready()
    
    def test_full_generation_lifecycle(self):
        """Test complete generation lifecycle"""
        sm = GlobalStateMachine()
        
        # Start
        assert sm.can_start()
        sm.start_generation({'prompt': 'landscape'})
        assert sm.state == GlobalState.PREPARING
        
        # Ready
        sm.mark_ready()
        assert sm.state == GlobalState.RUNNING
        assert sm.can_pause()
        assert sm.can_cancel()
        
        # Complete
        sm.complete({'images': 10})
        assert sm.state == GlobalState.COMPLETED
        
        # Reset
        sm.reset()
        assert sm.state == GlobalState.IDLE
        assert sm.can_start()
    
    def test_pause_resume_lifecycle(self):
        """Test pause/resume lifecycle"""
        sm = GlobalStateMachine()
        sm.start_generation()
        sm.mark_ready()
        
        # Pause
        sm.pause()
        assert sm.is_paused()
        assert not sm.can_pause()
        assert sm.can_resume()
        
        # Resume
        sm.resume()
        assert sm.is_running()
        assert sm.can_pause()
        assert not sm.can_resume()
    
    def test_error_lifecycle(self):
        """Test error handling lifecycle"""
        sm = GlobalStateMachine()
        sm.start_generation()
        sm.mark_ready()
        
        # Error
        sm.error("Test error", {'code': 500})
        assert sm.state == GlobalState.ERROR
        assert sm.error_message == "Test error"
        assert sm.metadata['code'] == 500
        
        # Reset clears error
        sm.reset()
        assert sm.error_message is None
        assert 'code' not in sm.metadata
    
    def test_thread_safety(self):
        """Test thread-safe state access"""
        sm = GlobalStateMachine()
        sm.start_generation()
        sm.mark_ready()
        
        results = []
        
        def read_state():
            for _ in range(100):
                state = sm.state
                results.append(state)
                time.sleep(0.001)
        
        def write_state():
            for _ in range(50):
                if sm.can_pause():
                    sm.pause()
                if sm.can_resume():
                    sm.resume()
                time.sleep(0.002)
        
        threads = [
            threading.Thread(target=read_state),
            threading.Thread(target=read_state),
            threading.Thread(target=write_state)
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All reads should succeed
        assert len(results) == 200
        # All states should be valid
        assert all(isinstance(s, GlobalState) for s in results)
    
    def test_serialization(self):
        """Test state serialization"""
        sm = GlobalStateMachine()
        sm.start_generation({'prompt': 'test', 'steps': 30})
        sm.mark_ready()
        
        data = sm.to_dict()
        
        assert data['state'] == 'running'
        assert data['metadata']['prompt'] == 'test'
        assert data['metadata']['steps'] == 30
        assert 'timestamp' in data
        assert 'history' in data
        assert len(data['history']) > 0
    
    def test_state_history(self):
        """Test state transition history"""
        sm = GlobalStateMachine()
        sm.start_generation()
        sm.mark_ready()
        sm.pause()
        sm.resume()
        sm.complete()
        
        data = sm.to_dict()
        history = data['history']
        
        # Should have recorded all transitions
        assert len(history) >= 5
        assert history[0]['from'] == 'idle'
        assert history[0]['to'] == 'preparing'
        assert history[-1]['to'] == 'completed'
    
    def test_query_methods(self):
        """Test all query methods"""
        sm = GlobalStateMachine()
        
        # IDLE
        assert sm.is_idle()
        assert not sm.is_active()
        assert not sm.is_running()
        assert not sm.is_paused()
        assert not sm.is_terminal()
        assert sm.can_start()
        
        # PREPARING
        sm.start_generation()
        assert not sm.is_idle()
        assert sm.is_active()
        assert not sm.can_start()
        
        # RUNNING
        sm.mark_ready()
        assert sm.is_running()
        assert sm.is_active()
        assert sm.can_pause()
        assert sm.can_cancel()
        
        # PAUSED
        sm.pause()
        assert sm.is_paused()
        assert sm.is_active()
        assert sm.can_resume()
        assert sm.can_cancel()
        
        # COMPLETED
        sm.resume()
        sm.complete()
        assert sm.is_terminal()
        assert not sm.is_active()
    
    def test_metadata_isolation(self):
        """Test that metadata is properly isolated"""
        sm = GlobalStateMachine()
        sm.start_generation({'key': 'value'})
        
        # Get metadata
        meta1 = sm.metadata
        meta1['key'] = 'modified'
        
        # Original should be unchanged
        meta2 = sm.metadata
        assert meta2['key'] == 'value'
    
    def test_repr_and_str(self):
        """Test string representations"""
        sm = GlobalStateMachine()
        
        repr_str = repr(sm)
        assert 'GlobalStateMachine' in repr_str
        assert 'idle' in repr_str
        
        str_str = str(sm)
        assert 'State:' in str_str
        assert 'idle' in str_str
        
        # With error
        sm.start_generation()
        sm.error("Test error")
        str_str = str(sm)
        assert 'Error:' in str_str
        assert 'Test error' in str_str


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
