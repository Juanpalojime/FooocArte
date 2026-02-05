"""
UX Rules Validation Tests

Tests business logic rules that govern UI behavior.
These tests ensure the UI cannot perform illegal operations
based on the current batch state.
"""

import pytest
from modules.batch_state_machine import EstadoBatch


class UXRules:
    """Business logic rules for UI interactions"""
    
    @staticmethod
    def puede_editar_config(estado: EstadoBatch) -> bool:
        """Can edit batch configuration in this state?"""
        return estado == EstadoBatch.INACTIVO
    
    @staticmethod
    def puede_pausar(estado: EstadoBatch) -> bool:
        """Can pause batch in this state?"""
        return estado == EstadoBatch.EJECUTANDO
    
    @staticmethod
    def puede_reanudar(estado: EstadoBatch) -> bool:
        """Can resume batch in this state?"""
        return estado == EstadoBatch.EN_PAUSA
    
    @staticmethod
    def puede_cancelar(estado: EstadoBatch) -> bool:
        """Can cancel batch in this state?"""
        return estado in [EstadoBatch.EJECUTANDO, EstadoBatch.EN_PAUSA]
    
    @staticmethod
    def puede_iniciar_nuevo(estado: EstadoBatch) -> bool:
        """Can start new batch in this state?"""
        return estado in [EstadoBatch.INACTIVO, EstadoBatch.COMPLETADO, EstadoBatch.ERROR]
    
    @staticmethod
    def debe_mostrar_progreso(estado: EstadoBatch) -> bool:
        """Should show progress bar in this state?"""
        return estado in [EstadoBatch.PREPARANDO, EstadoBatch.EJECUTANDO, EstadoBatch.EN_PAUSA, EstadoBatch.CANCELANDO]
    
    @staticmethod
    def debe_bloquear_inputs(estado: EstadoBatch) -> bool:
        """Should lock input fields in this state?"""
        return estado not in [EstadoBatch.INACTIVO, EstadoBatch.COMPLETADO, EstadoBatch.ERROR]


class TestConfigurationRules:
    """Test configuration editing rules"""
    
    def test_editar_config_solo_inactivo(self):
        """Configuration can only be edited when INACTIVO"""
        assert UXRules.puede_editar_config(EstadoBatch.INACTIVO)
        assert not UXRules.puede_editar_config(EstadoBatch.PREPARANDO)
        assert not UXRules.puede_editar_config(EstadoBatch.EJECUTANDO)
        assert not UXRules.puede_editar_config(EstadoBatch.EN_PAUSA)
        assert not UXRules.puede_editar_config(EstadoBatch.CANCELANDO)
        assert not UXRules.puede_editar_config(EstadoBatch.COMPLETADO)
        assert not UXRules.puede_editar_config(EstadoBatch.ERROR)


class TestPauseResumeRules:
    """Test pause/resume button visibility rules"""
    
    def test_pausar_solo_ejecutando(self):
        """Pause button only enabled when EJECUTANDO"""
        assert UXRules.puede_pausar(EstadoBatch.EJECUTANDO)
        assert not UXRules.puede_pausar(EstadoBatch.INACTIVO)
        assert not UXRules.puede_pausar(EstadoBatch.PREPARANDO)
        assert not UXRules.puede_pausar(EstadoBatch.EN_PAUSA)
        assert not UXRules.puede_pausar(EstadoBatch.CANCELANDO)
        assert not UXRules.puede_pausar(EstadoBatch.COMPLETADO)
        assert not UXRules.puede_pausar(EstadoBatch.ERROR)
    
    def test_reanudar_solo_en_pausa(self):
        """Resume button only enabled when EN_PAUSA"""
        assert UXRules.puede_reanudar(EstadoBatch.EN_PAUSA)
        assert not UXRules.puede_reanudar(EstadoBatch.INACTIVO)
        assert not UXRules.puede_reanudar(EstadoBatch.PREPARANDO)
        assert not UXRules.puede_reanudar(EstadoBatch.EJECUTANDO)
        assert not UXRules.puede_reanudar(EstadoBatch.CANCELANDO)
        assert not UXRules.puede_reanudar(EstadoBatch.COMPLETADO)
        assert not UXRules.puede_reanudar(EstadoBatch.ERROR)


class TestCancellationRules:
    """Test cancellation rules"""
    
    def test_cancelar_solo_ejecutando_o_pausado(self):
        """Can cancel when EJECUTANDO or EN_PAUSA"""
        assert UXRules.puede_cancelar(EstadoBatch.EJECUTANDO)
        assert UXRules.puede_cancelar(EstadoBatch.EN_PAUSA)
        assert not UXRules.puede_cancelar(EstadoBatch.INACTIVO)
        assert not UXRules.puede_cancelar(EstadoBatch.PREPARANDO)
        assert not UXRules.puede_cancelar(EstadoBatch.CANCELANDO)
        assert not UXRules.puede_cancelar(EstadoBatch.COMPLETADO)
        assert not UXRules.puede_cancelar(EstadoBatch.ERROR)


class TestBatchStartRules:
    """Test rules for starting new batches"""
    
    def test_iniciar_nuevo_solo_estados_finales(self):
        """Can only start new batch from final states"""
        assert UXRules.puede_iniciar_nuevo(EstadoBatch.INACTIVO)
        assert UXRules.puede_iniciar_nuevo(EstadoBatch.COMPLETADO)
        assert UXRules.puede_iniciar_nuevo(EstadoBatch.ERROR)
        assert not UXRules.puede_iniciar_nuevo(EstadoBatch.PREPARANDO)
        assert not UXRules.puede_iniciar_nuevo(EstadoBatch.EJECUTANDO)
        assert not UXRules.puede_iniciar_nuevo(EstadoBatch.EN_PAUSA)
        assert not UXRules.puede_iniciar_nuevo(EstadoBatch.CANCELANDO)


class TestUIVisibilityRules:
    """Test UI element visibility rules"""
    
    def test_mostrar_progreso_estados_activos(self):
        """Progress bar visible during active states"""
        assert UXRules.debe_mostrar_progreso(EstadoBatch.PREPARANDO)
        assert UXRules.debe_mostrar_progreso(EstadoBatch.EJECUTANDO)
        assert UXRules.debe_mostrar_progreso(EstadoBatch.EN_PAUSA)
        assert UXRules.debe_mostrar_progreso(EstadoBatch.CANCELANDO)
        assert not UXRules.debe_mostrar_progreso(EstadoBatch.INACTIVO)
        assert not UXRules.debe_mostrar_progreso(EstadoBatch.COMPLETADO)
        assert not UXRules.debe_mostrar_progreso(EstadoBatch.ERROR)
    
    def test_bloquear_inputs_durante_procesamiento(self):
        """Input fields locked during processing"""
        assert UXRules.debe_bloquear_inputs(EstadoBatch.PREPARANDO)
        assert UXRules.debe_bloquear_inputs(EstadoBatch.EJECUTANDO)
        assert UXRules.debe_bloquear_inputs(EstadoBatch.EN_PAUSA)
        assert UXRules.debe_bloquear_inputs(EstadoBatch.CANCELANDO)
        assert not UXRules.debe_bloquear_inputs(EstadoBatch.INACTIVO)
        assert not UXRules.debe_bloquear_inputs(EstadoBatch.COMPLETADO)
        assert not UXRules.debe_bloquear_inputs(EstadoBatch.ERROR)


class TestCombinedRules:
    """Test combinations of rules"""
    
    def test_estado_inactivo_permite_configuracion(self):
        """INACTIVO state allows configuration and starting"""
        estado = EstadoBatch.INACTIVO
        assert UXRules.puede_editar_config(estado)
        assert UXRules.puede_iniciar_nuevo(estado)
        assert not UXRules.debe_bloquear_inputs(estado)
        assert not UXRules.debe_mostrar_progreso(estado)
    
    def test_estado_ejecutando_bloquea_configuracion(self):
        """EJECUTANDO state blocks configuration"""
        estado = EstadoBatch.EJECUTANDO
        assert not UXRules.puede_editar_config(estado)
        assert not UXRules.puede_iniciar_nuevo(estado)
        assert UXRules.debe_bloquear_inputs(estado)
        assert UXRules.debe_mostrar_progreso(estado)
        assert UXRules.puede_pausar(estado)
        assert UXRules.puede_cancelar(estado)
    
    def test_estado_en_pausa_permite_reanudar_y_cancelar(self):
        """EN_PAUSA state allows resume and cancel"""
        estado = EstadoBatch.EN_PAUSA
        assert UXRules.puede_reanudar(estado)
        assert UXRules.puede_cancelar(estado)
        assert not UXRules.puede_pausar(estado)
        assert UXRules.debe_mostrar_progreso(estado)
