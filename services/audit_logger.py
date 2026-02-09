"""
Audit Logger Service
Sistema centralizado de registro de eventos (bitácora)
"""
from datetime import datetime
from typing import Optional, Dict
import json


def log_event(
    user_id: str,
    user_email: str,
    user_name: str,
    event_type: str,
    action: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    details: Optional[Dict] = None,
    status: str = 'success'
):
    """
    Registra un evento en la bitácora del sistema.
    
    Args:
        user_id: UUID del usuario que realiza la acción
        user_email: Email del usuario
        user_name: Nombre completo del usuario
        event_type: Categoría del evento ('auth', 'user_management', 'analysis', 'definition', 'system')
        action: Acción específica ('login', 'logout', 'create_user', etc.)
        entity_type: Tipo de entidad afectada ('user', 'analysis', 'definition')
        entity_id: ID de la entidad afectada
        details: Diccionario con detalles adicionales
        status: 'success' o 'error'
    
    Returns:
        bool: True si se registró exitosamente, False en caso contrario
    """
    try:
        from services.auth import get_supabase_client
        supabase = get_supabase_client()
        
        # Preparar datos para insertar
        log_data = {
            'user_id': user_id,
            'user_email': user_email,
            'user_name': user_name,
            'event_type': event_type,
            'action': action,
            'status': status
        }
        
        # Agregar campos opcionales si existen
        if entity_type:
            log_data['entity_type'] = entity_type
        
        if entity_id:
            log_data['entity_id'] = entity_id
        
        if details:
            log_data['details'] = json.dumps(details) if isinstance(details, dict) else details
        
        # Insertar en Supabase
        response = supabase.table('audit_logs').insert(log_data).execute()
        
        return True
        
    except Exception as e:
        # Si falla el logging, no queremos que rompa la aplicación
        # Solo registramos el error en consola
        print(f"❌ Error al registrar evento en bitácora: {e}")
        return False


def get_audit_logs(
    user_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    event_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    Obtiene logs de la bitácora con filtros opcionales.
    
    Args:
        user_id: Filtrar por ID de usuario
        start_date: Fecha de inicio (inclusive)
        end_date: Fecha de fin (inclusive)
        event_type: Filtrar por tipo de evento
        limit: Número máximo de resultados
        offset: Offset para paginación
    
    Returns:
        list: Lista de logs que cumplen los filtros
    """
    try:
        from services.auth import get_supabase_client
        supabase = get_supabase_client()
        
        # Comenzar query
        query = supabase.table('audit_logs').select('*')
        
        # Aplicar filtros
        if user_id:
            query = query.eq('user_id', user_id)
        
        if start_date:
            query = query.gte('timestamp', start_date.isoformat())
        
        if end_date:
            query = query.lte('timestamp', end_date.isoformat())
        
        if event_type:
            query = query.eq('event_type', event_type)
        
        # Ordenar por fecha descendente (más recientes primero)
        query = query.order('timestamp', desc=True)
        
        # Limitar resultados
        query = query.limit(limit).offset(offset)
        
        # Ejecutar query
        response = query.execute()
        
        return response.data if response.data else []
        
    except Exception as e:
        print(f"❌ Error al obtener logs de bitácora: {e}")
        return []


def get_audit_logs_count(
    user_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    event_type: Optional[str] = None
):
    """
    Cuenta el número total de logs que cumplen los filtros.
    
    Returns:
        int: Número total de logs
    """
    try:
        from services.auth import get_supabase_client
        supabase = get_supabase_client()
        
        # Comenzar query
        query = supabase.table('audit_logs').select('*', count='exact')
        
        # Aplicar filtros
        if user_id:
            query = query.eq('user_id', user_id)
        
        if start_date:
            query = query.gte('timestamp', start_date.isoformat())
        
        if end_date:
            query = query.lte('timestamp', end_date.isoformat())
        
        if event_type:
            query = query.eq('event_type', event_type)
        
        # Ejecutar query
        response = query.execute()
        
        return response.count if hasattr(response, 'count') else 0
        
    except Exception as e:
        print(f"❌ Error al contar logs: {e}")
        return 0
