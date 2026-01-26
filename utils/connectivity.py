"""
Utilidades para detección de conectividad a internet
"""
import socket


def check_internet_connection(timeout=3) -> bool:
    """
    Verifica si hay conexión a internet
    
    Args:
        timeout: Tiempo de espera en segundos
    
    Returns:
        True si hay internet, False si no
    """
    try:
        # Intentar conectar a Google DNS
        socket.create_connection(("8.8.8.8", 53), timeout=timeout)
        return True
    except OSError:
        return False


def get_connection_status() -> dict:
    """
    Obtiene el estado de conexión con más detalles
    
    Returns:
        Dict con 'online' (bool) y 'message' (str)
    """
    is_online = check_internet_connection()
    
    if is_online:
        return {
            'online': True,
            'message': '🌐 Conectado a internet'
        }
    else:
        return {
            'online': False,
            'message': '📡 Sin conexión a internet'
        }
