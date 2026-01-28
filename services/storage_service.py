"""
Supabase Storage Service
Servicio para subir y obtener imágenes de análisis desde Supabase Storage
"""
import streamlit as st
from typing import Optional, Tuple
import io
import numpy as np
from PIL import Image
import cv2

from services.auth import get_supabase_admin_client  # Usa admin client para bypass RLS
from utils.connectivity import check_internet_connection


# Nombre del bucket en Supabase Storage
BUCKET_NAME = "ToraxIA-images"


def ensure_bucket_exists() -> bool:
    """
    Verifica que el bucket exista, si no lo crea.
    
    Returns:
        bool: True si el bucket existe o se creó correctamente
    """
    try:
        supabase = get_supabase_admin_client()
        
        # Listar buckets existentes
        buckets = supabase.storage.list_buckets()
        bucket_names = [b.name for b in buckets]
        
        if BUCKET_NAME not in bucket_names:
            # Crear bucket público para imágenes
            supabase.storage.create_bucket(
                BUCKET_NAME,
                options={
                    "public": True,  # Acceso público para mostrar imágenes
                    "file_size_limit": 5242880  # 5MB máximo por archivo
                }
            )
            print(f"✅ Bucket '{BUCKET_NAME}' creado correctamente")
        
        return True
        
    except Exception as e:
        print(f"⚠️ Error con bucket: {str(e)}")
        return False


def upload_image_to_storage(
    image_data: np.ndarray,
    filename: str,
    folder: str = "originals"
) -> Optional[str]:
    """
    Sube una imagen a Supabase Storage.
    
    Args:
        image_data: Imagen como numpy array (RGB o grayscale)
        filename: Nombre del archivo (sin extensión)
        folder: Carpeta dentro del bucket ("originals" o "overlays")
    
    Returns:
        str: URL pública de la imagen, o None si falla
    """
    if not check_internet_connection():
        print("⚠️ Sin conexión a internet, no se puede subir imagen")
        return None
    
    try:
        supabase = get_supabase_admin_client()
        
        # Asegurar que el bucket existe
        ensure_bucket_exists()
        
        # Convertir numpy array a bytes JPEG
        if len(image_data.shape) == 2:
            # Grayscale a RGB
            image_data = cv2.cvtColor(image_data, cv2.COLOR_GRAY2RGB)
        elif image_data.shape[2] == 4:
            # RGBA a RGB
            image_data = cv2.cvtColor(image_data, cv2.COLOR_RGBA2RGB)
        
        # Si la imagen está normalizada (0-1), escalar a 0-255
        if image_data.max() <= 1.0:
            image_data = (image_data * 255).astype(np.uint8)
        else:
            image_data = image_data.astype(np.uint8)
        
        # Convertir a PIL Image y luego a bytes
        pil_image = Image.fromarray(image_data)
        
        # Comprimir como JPEG para ahorrar espacio
        buffer = io.BytesIO()
        pil_image.save(buffer, format="JPEG", quality=85, optimize=True)
        image_bytes = buffer.getvalue()
        
        # Path completo en el bucket
        file_path = f"{folder}/{filename}.jpg"
        
        # Subir a Supabase Storage
        result = supabase.storage.from_(BUCKET_NAME).upload(
            path=file_path,
            file=image_bytes,
            file_options={"content-type": "image/jpeg", "upsert": "true"}
        )
        
        # Obtener URL pública
        public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(file_path)
        
        print(f"✅ Imagen subida: {file_path}")
        return public_url
        
    except Exception as e:
        print(f"❌ Error subiendo imagen: {str(e)}")
        return None


def upload_pdf_to_storage(
    pdf_bytes: bytes,
    filename: str
) -> Optional[str]:
    """
    Sube un PDF a Supabase Storage.
    
    Args:
        pdf_bytes: PDF como bytes
        filename: Nombre del archivo (sin extensión)
    
    Returns:
        str: URL pública del PDF, o None si falla
    """
    if not check_internet_connection():
        print("⚠️ Sin conexión a internet, no se puede subir PDF")
        return None
    
    try:
        supabase = get_supabase_admin_client()
        
        # Asegurar que el bucket existe
        ensure_bucket_exists()
        
        # Path completo en el bucket
        file_path = f"reports/{filename}.pdf"
        
        # Subir a Supabase Storage
        result = supabase.storage.from_(BUCKET_NAME).upload(
            path=file_path,
            file=pdf_bytes,
            file_options={"content-type": "application/pdf", "upsert": "true"}
        )
        
        # Obtener URL pública
        public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(file_path)
        
        print(f"✅ PDF subido: {file_path}")
        return public_url
        
    except Exception as e:
        print(f"❌ Error subiendo PDF: {str(e)}")
        return None


def upload_analysis_images(
    analysis_id: str,
    original_image: np.ndarray,
    overlay_image: np.ndarray,
    pdf_bytes: Optional[bytes] = None
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Sube todas las imágenes de un análisis a Supabase Storage.
    
    Args:
        analysis_id: ID único del análisis (usado como nombre de archivo)
        original_image: Radiografía original preprocesada
        overlay_image: Overlay con Grad-CAM
        pdf_bytes: PDF del reporte (opcional)
    
    Returns:
        Tuple[str, str, str]: (original_url, overlay_url, pdf_url), None para cada si falla
    """
    if not check_internet_connection():
        print("⚠️ Sin conexión a internet, no se pueden subir imágenes")
        return None, None, None
    
    original_url = None
    overlay_url = None
    pdf_url = None
    
    # Subir imagen original
    original_url = upload_image_to_storage(
        original_image,
        f"{analysis_id}_original",
        folder="originals"
    )
    
    # Subir overlay
    overlay_url = upload_image_to_storage(
        overlay_image,
        f"{analysis_id}_overlay",
        folder="overlays"
    )
    
    # Subir PDF si existe
    if pdf_bytes:
        pdf_url = upload_pdf_to_storage(pdf_bytes, analysis_id)
    
    return original_url, overlay_url, pdf_url


def delete_analysis_images(analysis_id: str) -> bool:
    """
    Elimina las imágenes de un análisis de Supabase Storage.
    
    Args:
        analysis_id: ID del análisis
    
    Returns:
        bool: True si se eliminaron correctamente
    """
    try:
        supabase = get_supabase_admin_client()
        
        # Eliminar archivos
        files_to_delete = [
            f"originals/{analysis_id}_original.jpg",
            f"overlays/{analysis_id}_overlay.jpg",
            f"reports/{analysis_id}.pdf"
        ]
        
        for file_path in files_to_delete:
            try:
                supabase.storage.from_(BUCKET_NAME).remove([file_path])
            except:
                pass  # Ignorar si el archivo no existe
        
        print(f"✅ Imágenes del análisis {analysis_id} eliminadas")
        return True
        
    except Exception as e:
        print(f"❌ Error eliminando imágenes: {str(e)}")
        return False
