"""
Unit Tests for BatchStateMachine

Tests all state transitions, validations, and error handling
to ensure the state machine behaves correctly and prevents
invalid transitions.
"""

import pytest
from modules.batch_state_machine import BatchStateMachine, EstadoBatch


class TestEstadoInicial:
    """Test initial state of BatchStateMachine"""
    
    def test_estado_inicial(self):
        """State machine should start in INACTIVO state"""
        batch = BatchStateMachine()
        assert batch.estado == EstadoBatch.INACTIVO
        assert batch.imagen_actual == 0
        assert batch.total == 0
        assert batch.error is None


class TestFlujosExitosos:
    """Test successful state transition flows"""
    
    def test_flujo_completo_batch(self):
        """Complete batch flow: INACTIVO → PREPARANDO → EJECUTANDO → COMPLETADO"""
        batch = BatchStateMachine()

        # Iniciar
        batch.iniciar(total=3)
        assert batch.estado == EstadoBatch.PREPARANDO
        assert batch.total == 3

        # Preparado
        batch.preparado()
        assert batch.estado == EstadoBatch.EJECUTANDO

        # Tick 1
        batch.tick()
        assert batch.imagen_actual == 1
        assert batch.estado == EstadoBatch.EJECUTANDO

        # Tick 2
        batch.tick()
        assert batch.imagen_actual == 2
        assert batch.estado == EstadoBatch.EJECUTANDO

        # Tick 3 (final)
        batch.tick()
        assert batch.imagen_actual == 3
        assert batch.estado == EstadoBatch.COMPLETADO
    
    def test_pausar_y_reanudar(self):
        """Pause and resume flow"""
        batch = BatchStateMachine()

        batch.iniciar(5)
        batch.preparado()

        # Pausar
        batch.pausar()
        assert batch.estado == EstadoBatch.EN_PAUSA

        # Reanudar
        batch.reanudar()
        assert batch.estado == EstadoBatch.EJECUTANDO
    
    def test_cancelar_batch(self):
        """Cancellation flow"""
        batch = BatchStateMachine()

        batch.iniciar(5)
        batch.preparado()

        batch.tick()
        assert batch.imagen_actual == 1

        # Cancelar
        batch.cancelar()
        assert batch.estado == EstadoBatch.CANCELANDO

        # Completar cancelación
        batch.cancelar_completado()
        assert batch.estado == EstadoBatch.COMPLETADO
    
    def test_error_fatal(self):
        """Error handling flow"""
        batch = BatchStateMachine()

        batch.iniciar(5)
        batch.preparado()

        # Error fatal
        batch.error_fatal("Sin VRAM disponible")
        assert batch.estado == EstadoBatch.ERROR
        assert batch.error == "Sin VRAM disponible"
    
    def test_reset_desde_completado(self):
        """Reset from COMPLETADO state"""
        batch = BatchStateMachine()

        batch.iniciar(1)
        batch.preparado()
        batch.tick()
        assert batch.estado == EstadoBatch.COMPLETADO

        # Reset
        batch.reset()
        assert batch.estado == EstadoBatch.INACTIVO
        assert batch.imagen_actual == 0
        assert batch.total == 0
    
    def test_reset_desde_error(self):
        """Reset from ERROR state"""
        batch = BatchStateMachine()

        batch.iniciar(1)
        batch.error_fatal("Test error")
        assert batch.estado == EstadoBatch.ERROR

        # Reset
        batch.reset()
        assert batch.estado == EstadoBatch.INACTIVO
        assert batch.error is None


class TestTransicionesInvalidas:
    """Test invalid state transitions raise errors"""
    
    def test_tick_sin_iniciar(self):
        """Cannot tick without starting"""
        batch = BatchStateMachine()
        
        with pytest.raises(RuntimeError, match="debe estar en EJECUTANDO"):
            batch.tick()
    
    def test_preparado_sin_iniciar(self):
        """Cannot mark as ready without starting"""
        batch = BatchStateMachine()
        
        with pytest.raises(RuntimeError, match="debe estar en PREPARANDO"):
            batch.preparado()
    
    def test_pausar_sin_ejecutar(self):
        """Cannot pause if not executing"""
        batch = BatchStateMachine()
        
        with pytest.raises(RuntimeError, match="debe estar en EJECUTANDO"):
            batch.pausar()
    
    def test_reanudar_sin_pausar(self):
        """Cannot resume if not paused"""
        batch = BatchStateMachine()
        batch.iniciar(1)
        batch.preparado()
        
        with pytest.raises(RuntimeError, match="debe estar en EN_PAUSA"):
            batch.reanudar()
    
    def test_cancelar_completado_sin_cancelar(self):
        """Cannot complete cancellation without cancelling first"""
        batch = BatchStateMachine()
        batch.iniciar(1)
        batch.preparado()
        
        with pytest.raises(RuntimeError, match="debe estar en CANCELANDO"):
            batch.cancelar_completado()
    
    def test_reset_desde_ejecutando(self):
        """Cannot reset while executing"""
        batch = BatchStateMachine()
        batch.iniciar(1)
        batch.preparado()
        
        with pytest.raises(RuntimeError, match="debe estar en COMPLETADO o ERROR"):
            batch.reset()
    
    def test_iniciar_con_total_cero(self):
        """Cannot start with total=0"""
        batch = BatchStateMachine()
        
        with pytest.raises(ValueError, match="total debe ser > 0"):
            batch.iniciar(0)
    
    def test_iniciar_con_total_negativo(self):
        """Cannot start with negative total"""
        batch = BatchStateMachine()
        
        with pytest.raises(ValueError, match="total debe ser > 0"):
            batch.iniciar(-5)


class TestCasosEspeciales:
    """Test edge cases and special scenarios"""
    
    def test_pausar_y_cancelar(self):
        """Can cancel from paused state"""
        batch = BatchStateMachine()
        batch.iniciar(5)
        batch.preparado()
        batch.pausar()
        
        # Cancelar desde EN_PAUSA
        batch.cancelar()
        assert batch.estado == EstadoBatch.CANCELANDO
    
    def test_tick_hasta_completado(self):
        """Ticking to completion transitions to COMPLETADO"""
        batch = BatchStateMachine()
        batch.iniciar(2)
        batch.preparado()
        
        batch.tick()
        assert batch.estado == EstadoBatch.EJECUTANDO
        
        batch.tick()
        assert batch.estado == EstadoBatch.COMPLETADO
    
    def test_multiples_pausas_y_reanudaciones(self):
        """Multiple pause/resume cycles"""
        batch = BatchStateMachine()
        batch.iniciar(10)
        batch.preparado()
        
        for _ in range(3):
            batch.pausar()
            assert batch.estado == EstadoBatch.EN_PAUSA
            batch.reanudar()
            assert batch.estado == EstadoBatch.EJECUTANDO
    
    def test_error_fatal_desde_cualquier_estado(self):
        """Error can occur from any state"""
        estados_iniciales = [
            (EstadoBatch.PREPARANDO, lambda b: b.iniciar(1)),
            (EstadoBatch.EJECUTANDO, lambda b: (b.iniciar(1), b.preparado())),
            (EstadoBatch.EN_PAUSA, lambda b: (b.iniciar(1), b.preparado(), b.pausar())),
        ]
        
        for estado_esperado, setup in estados_iniciales:
            batch = BatchStateMachine()
            if isinstance(setup(batch), tuple):
                pass  # Multiple calls
            
            assert batch.estado == estado_esperado
            
            batch.error_fatal("Test error")
            assert batch.estado == EstadoBatch.ERROR
