"""
Servicio para guardar análisis en Supabase
"""
import streamlit as st
from datetime import datetime
from typing import Dict, Tuple, Optional
import json

from services.auth import get_supabase_client, get_current_user
from utils.connectivity import check_internet_connection


def save_analysis_to_database(analysis_results: Dict, form_data: Dict) -> Tuple[bool, str]:
    """
    Guarda un análisis completo en la base de datos Supabase
    
    Args:
        analysis_results: Resultados del análisis (predicciones, imágenes, etc.)
        form_data: Datos del formulario pre-diagnóstico
    
    Returns:
        Tuple[bool, str]: (éxito, mensaje)
    """
    
    # Verificar conexión a internet
    if not check_internet_connection():
        return False, "No hay conexión a internet. El análisis no se guardó en la base de datos."
    
    try:
        # Obtener cliente de Supabase
        supabase = get_supabase_client()
        
        # Obtener usuario actual
        user = get_current_user()
        user_id = user['id']
        
        # Preparar predicciones como JSON
        predictions = analysis_results['predictions']
        class_names = analysis_results['class_names']
        
        # Crear diccionario de predicciones
        predictions_dict = {
            class_names[i]: float(predictions[i]) 
            for i in range(len(class_names))
        }
        
        # Calcular si ToraxIA acertó
        acerto_toraxia = None
        if form_data.get('pronostico_real'):
            acerto_toraxia = calculate_accuracy(
                form_data['pronostico_real'],
                analysis_results['top_class']
            )
        
        # Preparar datos para insertar
        analysis_data = {
            'user_id': user_id,
            'timestamp': datetime.now().isoformat(),
            'is_public': True,  # Por defecto público para "Actividad Reciente"
            
            # Datos del paciente
            'paciente_nombre': form_data['paciente_nombre'],
            'paciente_apellido': form_data['paciente_apellido'],
            'paciente_ci': form_data['paciente_ci'],
            'paciente_edad': form_data['paciente_edad'],
            'paciente_sexo': form_data['paciente_sexo'],
            'paciente_peso': form_data.get('paciente_peso'),
            
            # Datos académicos
            'academico_nombre': form_data['academico_nombre'],
            'academico_apellido': form_data['academico_apellido'],
            'academico_ci': form_data['academico_ci'],
            'academico_area': form_data['academico_area'],
            
            # Comentarios
            'comentario_sospecha': form_data.get('comentario_sospecha'),
            'pronostico_real': form_data.get('pronostico_real'),
            'acerto_toraxia': acerto_toraxia,
            
            # Resultados del modelo
            'top_prediction': analysis_results['top_class'],
            'top_probability': float(analysis_results['top_prob']),
            'predictions_json': predictions_dict,
            
            # URLs de archivos (por ahora None, se implementará con Google Drive)
            'original_image_url': None,
            'overlay_image_url': None,
            'pdf_report_url': None
        }
        
        # Insertar en la base de datos
        result = supabase.table('analyses').insert(analysis_data).execute()
        
        if result.data:
            return True, f"✅ Análisis guardado exitosamente en la base de datos (ID: {result.data[0]['id'][:8]}...)"
        else:
            return False, "Error al guardar el análisis en la base de datos"
            
    except Exception as e:
        return False, f"Error al guardar: {str(e)}"


def calculate_accuracy(pronostico_real: str, top_prediction: str) -> bool:
    """
    Calcula si ToraxIA acertó el pronóstico
    
    Args:
        pronostico_real: Pronóstico real ingresado por el usuario
        top_prediction: Predicción principal del modelo
    
    Returns:
        True si acertó, False si no
    """
    import unicodedata
    from utils.translations import translate_pathology
    
    def normalize_text(text):
        """Normaliza texto: quita acentos, minúsculas, espacios"""
        text = unicodedata.normalize('NFD', text)
        text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
        text = text.lower().replace(' ', '').replace('_', '').replace('-', '')
        return text
    
    # Normalizar pronóstico real
    pronostico_norm = normalize_text(pronostico_real)
    
    # Normalizar predicción en inglés y español
    top_pred_en_norm = normalize_text(top_prediction)
    top_pred_es_norm = normalize_text(translate_pathology(top_prediction))
    
    # Verificar coincidencia
    return (pronostico_norm in top_pred_en_norm or 
            top_pred_en_norm in pronostico_norm or
            pronostico_norm in top_pred_es_norm or 
            top_pred_es_norm in pronostico_norm)


def get_user_analyses(user_id: str, limit: int = 20) -> list:
    """
    Obtiene los análisis de un usuario específico
    
    Args:
        user_id: ID del usuario
        limit: Número máximo de análisis a retornar
    
    Returns:
        Lista de análisis ordenados por fecha (más reciente primero)
    """
    try:
        supabase = get_supabase_client()
        
        result = supabase.table('analyses')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('timestamp', desc=True)\
            .limit(limit)\
            .execute()
        
        return result.data if result.data else []
        
    except Exception as e:
        st.error(f"Error al obtener análisis: {str(e)}")
        return []


def get_recent_public_analyses(limit: int = 20) -> list:
    """
    Obtiene los análisis públicos más recientes (para Actividad Reciente)
    
    Args:
        limit: Número máximo de análisis a retornar
    
    Returns:
        Lista de análisis públicos ordenados por fecha
    """
    try:
        supabase = get_supabase_client()
        
        result = supabase.table('analyses')\
            .select('*')\
            .eq('is_public', True)\
            .order('timestamp', desc=True)\
            .limit(limit)\
            .execute()
        
        return result.data if result.data else []
        
    except Exception as e:
        st.error(f"Error al obtener análisis públicos: {str(e)}")
        return []
