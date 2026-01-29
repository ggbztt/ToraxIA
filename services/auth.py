"""
Servicio de Autenticación con Supabase
Maneja registro, login, y gestión de sesiones
"""
import os
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv
import hashlib
from typing import Optional, Dict, Tuple

# Cargar variables de entorno locales
load_dotenv()


def get_env_var(key: str) -> str:
    """
    Obtiene una variable de entorno.
    Soporta tanto .env local como Streamlit Cloud secrets.
    """
    # Primero intentar Streamlit secrets (para Streamlit Cloud)
    try:
        if key in st.secrets:
            return st.secrets[key]
    except:
        pass
    
    # Fallback a variables de entorno locales (.env)
    return os.getenv(key)


# Cliente de Supabase
def get_supabase_client() -> Client:
    """Obtiene el cliente de Supabase (anon key - sujeto a RLS)"""
    url = get_env_var("SUPABASE_URL")
    key = get_env_var("SUPABASE_ANON_KEY")
    return create_client(url, key)


def get_supabase_admin_client() -> Client:
    """
    Obtiene el cliente de Supabase con service_role key.
    Este cliente bypasea RLS y debe usarse solo para operaciones de backend.
    """
    url = get_env_var("SUPABASE_URL")
    key = get_env_var("SUPABASE_SERVICE_ROLE_KEY")
    
    if not key:
        # Fallback a anon key si no hay service role
        print("⚠️ SUPABASE_SERVICE_ROLE_KEY no encontrada, usando ANON_KEY")
        key = get_env_var("SUPABASE_ANON_KEY")
    
    return create_client(url, key)


def hash_password(password: str) -> str:
    """Hashea una contraseña usando SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def register_user(
    email: str,
    password: str,
    nombre: str,
    apellido: str,
    ci: str,
    area_estudio: str,
    role: str = "estudiante"
) -> Tuple[bool, str]:
    """
    Registra un nuevo usuario en la base de datos
    
    Returns:
        Tuple[bool, str]: (éxito, mensaje)
    """
    try:
        supabase = get_supabase_client()
        
        # Verificar si el email ya existe
        existing_email = supabase.table('users').select('email').eq('email', email).execute()
        if existing_email.data:
            return False, "Este email ya está registrado"
        
        # Verificar si la CI ya existe
        existing_ci = supabase.table('users').select('ci').eq('ci', ci).execute()
        if existing_ci.data:
            return False, "Esta cédula ya está registrada"
        
        # Hashear contraseña
        password_hash = hash_password(password)
        
        # Insertar usuario
        data = {
            'email': email,
            'password_hash': password_hash,
            'nombre': nombre,
            'apellido': apellido,
            'ci': ci,
            'role': role,
            'area_estudio': area_estudio if role == 'estudiante' else None,
            'is_active': True
        }
        
        result = supabase.table('users').insert(data).execute()
        
        if result.data:
            return True, "Usuario registrado exitosamente"
        else:
            return False, "Error al registrar usuario"
            
    except Exception as e:
        return False, f"Error: {str(e)}"


def login_user(email: str, password: str) -> Tuple[bool, Optional[Dict], str]:
    """
    Autentica un usuario
    
    Returns:
        Tuple[bool, Optional[Dict], str]: (éxito, datos_usuario, mensaje)
    """
    try:
        supabase = get_supabase_client()
        
        # Buscar usuario por email
        result = supabase.table('users').select('*').eq('email', email).execute()
        
        if not result.data:
            return False, None, "Email no encontrado"
        
        user = result.data[0]
        
        # Verificar si está activo
        if not user.get('is_active', True):
            return False, None, "Usuario desactivado. Contacta al administrador"
        
        # Verificar contraseña
        password_hash = hash_password(password)
        if user['password_hash'] != password_hash:
            return False, None, "Contraseña incorrecta"
        
        # Actualizar last_login
        from datetime import datetime
        supabase.table('users').update({
            'last_login': datetime.now().isoformat()
        }).eq('id', user['id']).execute()
        
        # Remover password_hash antes de retornar
        user.pop('password_hash', None)
        
        return True, user, "Login exitoso"
        
    except Exception as e:
        return False, None, f"Error: {str(e)}"


def logout_user():
    """Cierra la sesión del usuario"""
    # Limpiar todas las variables de sesión relacionadas con autenticación
    keys_to_remove = ['authenticated', 'user', 'user_id', 'user_role', 'user_name']
    for key in keys_to_remove:
        if key in st.session_state:
            del st.session_state[key]


def is_authenticated() -> bool:
    """Verifica si hay un usuario autenticado"""
    return st.session_state.get('authenticated', False)


def get_current_user() -> Optional[Dict]:
    """Obtiene los datos del usuario actual"""
    return st.session_state.get('user', None)


def is_admin() -> bool:
    """Verifica si el usuario actual es administrador"""
    user = get_current_user()
    return user and user.get('role') == 'admin'


def require_auth(func):
    """Decorador para requerir autenticación"""
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            st.warning("⚠️ Debes iniciar sesión para acceder a esta página")
            st.stop()
        return func(*args, **kwargs)
    return wrapper


def require_admin(func):
    """Decorador para requerir rol de administrador"""
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            st.warning("⚠️ Debes iniciar sesión para acceder a esta página")
            st.stop()
        if not is_admin():
            st.error("❌ No tienes permisos de administrador para acceder a esta página")
            st.stop()
        return func(*args, **kwargs)
    return wrapper


def get_user_by_id(user_id: str) -> Optional[Dict]:
    """Obtiene un usuario por su ID"""
    try:
        supabase = get_supabase_client()
        result = supabase.table('users').select('*').eq('id', user_id).execute()
        
        if result.data:
            user = result.data[0]
            user.pop('password_hash', None)
            return user
        return None
        
    except Exception as e:
        st.error(f"Error al obtener usuario: {str(e)}")
        return None


def update_user_profile(user_id: str, updates: Dict) -> Tuple[bool, str]:
    """
    Actualiza el perfil de un usuario
    
    Args:
        user_id: ID del usuario
        updates: Diccionario con campos a actualizar
    
    Returns:
        Tuple[bool, str]: (éxito, mensaje)
    """
    try:
        supabase = get_supabase_client()
        
        # No permitir actualizar ciertos campos
        forbidden_fields = ['id', 'password_hash', 'role', 'created_at']
        for field in forbidden_fields:
            updates.pop(field, None)
        
        result = supabase.table('users').update(updates).eq('id', user_id).execute()
        
        if result.data:
            # Actualizar session_state si es el usuario actual
            if st.session_state.get('user_id') == user_id:
                current_user = st.session_state.get('user', {})
                current_user.update(updates)
                st.session_state.user = current_user
            
            return True, "Perfil actualizado exitosamente"
        else:
            return False, "Error al actualizar perfil"
            
    except Exception as e:
        return False, f"Error: {str(e)}"


# ============================================
# PERSISTENCIA DE SESIÓN CON QUERY PARAMS
# ============================================

import base64
from datetime import datetime, timedelta

# Clave para el parámetro de sesión
SESSION_PARAM_KEY = "session"
SESSION_TIMEOUT_MINUTES = 10# Timeout de sesión en minutos


def _encode_session(user_id: str) -> str:
    """Codifica el user_id + timestamp para almacenamiento seguro"""
    timestamp = datetime.now().isoformat()
    data = f"{user_id}|{timestamp}"
    return base64.b64encode(data.encode()).decode()


def _decode_session(encoded: str) -> Tuple[Optional[str], Optional[datetime]]:
    """Decodifica el user_id y timestamp"""
    try:
        data = base64.b64decode(encoded.encode()).decode()
        parts = data.split("|")
        if len(parts) >= 2:
            user_id = parts[0]
            timestamp = datetime.fromisoformat(parts[1])
            return user_id, timestamp
        return None, None
    except:
        return None, None


def _is_session_expired(timestamp: datetime) -> bool:
    """Verifica si la sesión ha expirado (más de 12 minutos)"""
    if timestamp is None:
        return True
    elapsed = datetime.now() - timestamp
    return elapsed > timedelta(minutes=SESSION_TIMEOUT_MINUTES)


def restore_session_from_cookie() -> bool:
    """
    Intenta restaurar la sesión usando query params.
    Esta función verifica si hay un session token en la URL y si no ha expirado.
    Retorna True si se restauró exitosamente.
    """
    # Si ya está autenticado, no hacer nada
    if is_authenticated():
        return True
    
    # Verificar query params
    try:
        params = st.query_params
        if SESSION_PARAM_KEY in params:
            encoded_session = params[SESSION_PARAM_KEY]
            user_id, timestamp = _decode_session(encoded_session)
            
            if user_id and timestamp:
                # Verificar si la sesión ha expirado
                if _is_session_expired(timestamp):
                    # Sesión expirada, limpiar
                    del st.query_params[SESSION_PARAM_KEY]
                    st.warning(f"⏰ Tu sesión ha expirado después de {SESSION_TIMEOUT_MINUTES} minutos de inactividad. Por favor inicia sesión nuevamente.")
                    return False
                
                user = get_user_by_id(user_id)
                
                if user and user.get('is_active', True):
                    # Restaurar sesión y renovar timestamp
                    st.session_state.authenticated = True
                    st.session_state.user = user
                    st.session_state.user_id = user['id']
                    st.session_state.user_role = user.get('role', 'estudiante')
                    st.session_state.user_name = f"{user['nombre']} {user['apellido']}"
                    
                    # Renovar el timestamp para extender la sesión
                    new_encoded = _encode_session(user_id)
                    st.query_params[SESSION_PARAM_KEY] = new_encoded
                    
                    return True
    except Exception as e:
        print(f"Error restaurando sesión: {e}")
    
    return False


def login_with_persistence(email: str, password: str) -> Tuple[bool, Optional[Dict], str]:
    """
    Login que también guarda el token en query params para persistencia.
    """
    success, user, message = login_user(email, password)
    
    if success and user:
        # Guardar sesión en session_state
        st.session_state.authenticated = True
        st.session_state.user = user
        st.session_state.user_id = user['id']
        st.session_state.user_role = user.get('role', 'estudiante')
        st.session_state.user_name = f"{user['nombre']} {user['apellido']}"
        
        # Guardar en query params para persistencia (con timestamp)
        try:
            encoded = _encode_session(user['id'])
            st.query_params[SESSION_PARAM_KEY] = encoded
        except Exception as e:
            print(f"Advertencia: No se pudo guardar sesión en URL: {e}")
    
    return success, user, message


def logout_with_persistence():
    """
    Logout que también elimina el token de query params.
    """
    # Limpiar query params
    try:
        if SESSION_PARAM_KEY in st.query_params:
            del st.query_params[SESSION_PARAM_KEY]
    except Exception as e:
        print(f"Advertencia: No se pudo limpiar query params: {e}")
    
    # Limpiar session_state
    logout_user()


