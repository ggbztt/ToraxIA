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
        
        # Generar ID único para el análisis
        import uuid
        analysis_id = uuid.uuid4().hex
        
        # Subir imágenes a Supabase Storage
        original_url = None
        overlay_url = None
        pdf_url = None
        
        # Intentar subir imágenes si existen
        if 'original_image' in analysis_results and 'overlay' in analysis_results:
            try:
                from services.storage_service import upload_analysis_images
                
                original_url, overlay_url, pdf_url = upload_analysis_images(
                    analysis_id=analysis_id,
                    original_image=analysis_results['original_image'],
                    overlay_image=analysis_results['overlay'],
                    pdf_bytes=None  # PDF se puede generar después si se necesita
                )
                
                if original_url and overlay_url:
                    print(f"✅ Imágenes subidas a Supabase Storage")
                else:
                    print("⚠️ No se pudieron subir las imágenes, continuando sin ellas")
                    
            except Exception as img_error:
                print(f"⚠️ Error subiendo imágenes: {str(img_error)}")
                # Continuar sin imágenes, no es crítico
        
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
            
            # URLs de archivos (de Supabase Storage)
            'original_image_url': original_url,
            'overlay_image_url': overlay_url,
            'pdf_report_url': pdf_url
        }
        
        # Insertar en la base de datos
        result = supabase.table('analyses').insert(analysis_data).execute()
        
        if result.data:
            # Registrar evento de creación de análisis
            from services.audit_logger import log_event
            log_event(
                user_id=user_id,
                user_email=user['email'],
                user_name=f"{user['nombre']} {user['apellido']}",
                event_type='analysis',
                action='create_analysis',
                entity_type='analysis',
                entity_id=result.data[0]['id'],
                details={
                    'paciente': f"{form_data['paciente_nombre']} {form_data['paciente_apellido']}",
                    'top_prediction': analysis_results['top_class'],
                    'top_probability': float(analysis_results['top_prob'])
                },
                status='success'
            )
            
            images_msg = " con imágenes 📷" if original_url else " (sin imágenes)"
            return True, f"✅ Análisis guardado exitosamente{images_msg} (ID: {result.data[0]['id'][:8]}...)"
        else:
            return False, "Error al guardar el análisis en la base de datos"
            
    except Exception as e:
        return False, f"Error al guardar: {str(e)}"


def calculate_accuracy(pronostico_real: str, top_prediction: str) -> bool:
    import unicodedata
    from utils.translations import translate_pathology
    
    def normalize_text(text):
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


def get_all_users() -> list:
    """
    Obtiene todos los usuarios del sistema (para admin).
    
    Returns:
        list: Lista de usuarios con sus datos básicos
    """
    try:
        supabase = get_supabase_client()
        
        result = supabase.table('users')\
            .select('id, nombre, apellido, email, role, is_active, area_estudio')\
            .order('nombre', desc=False)\
            .execute()
        
        return result.data if result.data else []
        
    except Exception as e:
        print(f"Error al obtener usuarios: {str(e)}")
        return []
