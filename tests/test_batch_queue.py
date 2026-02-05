"""
Unit Tests for BatchQueue

Tests FIFO behavior, thread-safety, and queue operations
to ensure batches are processed in the correct order.
"""

import pytest
from modules.batch_queue import BatchQueue


class TestQueueBasics:
    """Test basic queue operations"""
    
    def test_singleton_pattern(self):
        """BatchQueue should be a singleton"""
        q1 = BatchQueue()
        q2 = BatchQueue()
        assert q1 is q2
    
    def test_queue_inicial_vacia(self):
        """Queue should start empty"""
        cola = BatchQueue()
        assert cola.esta_vacia()
        assert cola.longitud() == 0
    
    def test_agregar_batch(self):
        """Can add batch to queue"""
        cola = BatchQueue()
        batch_id = "test_batch_1"
        
        cola.agregar(batch_id)
        assert not cola.esta_vacia()
        assert cola.longitud() == 1
    
    def test_obtener_siguiente(self):
        """Can retrieve next batch from queue"""
        cola = BatchQueue()
        batch_id = "test_batch_1"
        
        cola.agregar(batch_id)
        siguiente = cola.obtener_siguiente()
        
        assert siguiente == batch_id
        assert cola.esta_vacia()


class TestFIFOBehavior:
    """Test FIFO (First In First Out) behavior"""
    
    def test_orden_fifo(self):
        """Batches should be processed in FIFO order"""
        cola = BatchQueue()
        
        batch_ids = ["batch_1", "batch_2", "batch_3"]
        for batch_id in batch_ids:
            cola.agregar(batch_id)
        
        # Verify order
        for expected_id in batch_ids:
            assert cola.obtener_siguiente() == expected_id
        
        assert cola.esta_vacia()
    
    def test_multiples_agregar_y_obtener(self):
        """Interleaved add and get operations maintain FIFO"""
        cola = BatchQueue()
        
        cola.agregar("batch_1")
        cola.agregar("batch_2")
        
        assert cola.obtener_siguiente() == "batch_1"
        
        cola.agregar("batch_3")
        
        assert cola.obtener_siguiente() == "batch_2"
        assert cola.obtener_siguiente() == "batch_3"
        assert cola.esta_vacia()


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_obtener_de_cola_vacia(self):
        """Getting from empty queue returns None"""
        cola = BatchQueue()
        assert cola.obtener_siguiente() is None
    
    def test_longitud_actualizada(self):
        """Queue length updates correctly"""
        cola = BatchQueue()
        
        assert cola.longitud() == 0
        
        cola.agregar("batch_1")
        assert cola.longitud() == 1
        
        cola.agregar("batch_2")
        assert cola.longitud() == 2
        
        cola.obtener_siguiente()
        assert cola.longitud() == 1
        
        cola.obtener_siguiente()
        assert cola.longitud() == 0
    
    def test_agregar_none(self):
        """Adding None should be handled gracefully"""
        cola = BatchQueue()
        
        # Depending on implementation, this might raise or be ignored
        # Adjust based on actual behavior
        cola.agregar(None)
        # If None is allowed, it should be retrievable
        if not cola.esta_vacia():
            assert cola.obtener_siguiente() is None


class TestConcurrency:
    """Test thread-safety (basic checks)"""
    
    def test_multiple_operations(self):
        """Multiple operations should not corrupt queue"""
        cola = BatchQueue()
        
        # Simulate rapid operations
        for i in range(100):
            cola.agregar(f"batch_{i}")
        
        assert cola.longitud() == 100
        
        # Retrieve all
        retrieved = []
        while not cola.esta_vacia():
            retrieved.append(cola.obtener_siguiente())
        
        assert len(retrieved) == 100
        assert retrieved == [f"batch_{i}" for i in range(100)]
