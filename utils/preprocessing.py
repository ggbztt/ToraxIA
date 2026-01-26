"""
Image Preprocessing Module
Preprocesamiento de radiografías para inferencia del modelo
"""
import numpy as np
from PIL import Image
import streamlit as st


def validate_image(file) -> bool:
    """
    Valida que el archivo sea una imagen válida (PNG/JPG/JPEG)
    
    Args:
        file: Archivo subido (UploadedFile de Streamlit o path)
    
    Returns:
        bool: True si es válido, False en caso contrario
    """
    valid_extensions = ['png', 'jpg', 'jpeg']
    
    try:
        if hasattr(file, 'name'):
            # Es un UploadedFile de Streamlit
            extension = file.name.split('.')[-1].lower()
            return extension in valid_extensions
        else:
            # Es un path
            extension = str(file).split('.')[-1].lower()
            return extension in valid_extensions
    except:
        return False


def image_to_array(image: Image.Image) -> np.ndarray:
    """
    Convierte PIL Image a numpy array
    
    Args:
        image: Imagen PIL
    
    Returns:
        np.ndarray: Array de numpy
    """
    # Asegurar que esté en RGB
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    return np.array(image)


def preprocess_image(image: Image.Image, target_size=(224, 224)) -> np.ndarray:
    """
    Preprocesa imagen para inferencia del modelo.
    
    Pipeline:
    1. Convertir a RGB
    2. Redimensionar a target_size
    3. Convertir a array numpy
    4. Normalizar a [0, 1]
    5. Agregar dimensión batch
    
    Args:
        image: Imagen PIL
        target_size: Tupla (height, width) para redimensionar
    
    Returns:
        np.ndarray: Array con shape (1, 224, 224, 3) normalizado
    """
    try:
        # 1. Asegurar RGB
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # 2. Redimensionar
        image_resized = image.resize(target_size, Image.Resampling.LANCZOS)
        
        # 3. Convertir a array
        img_array = np.array(image_resized)
        
        # 4. Normalizar a [0, 1]
        img_array = img_array.astype(np.float32) / 255.0
        
        # 5. Agregar dimensión batch: (224, 224, 3) -> (1, 224, 224, 3)
        img_array = np.expand_dims(img_array, axis=0)
        
        print(f"✅ Imagen preprocesada: {img_array.shape}, rango [{img_array.min():.3f}, {img_array.max():.3f}]")
        
        return img_array
    
    except Exception as e:
        st.error(f"❌ Error en preprocesamiento: {str(e)}")
        raise


def preprocess_for_display(image: Image.Image, target_size=(224, 224)) -> np.ndarray:
    """
    Preprocesa imagen solo para visualización (sin normalización)
    
    Args:
        image: Imagen PIL
        target_size: Tupla (height, width)
    
    Returns:
        np.ndarray: Array con shape (224, 224, 3) en rango [0, 255]
    """
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    image_resized = image.resize(target_size, Image.Resampling.LANCZOS)
    img_array = np.array(image_resized)
    
    return img_array
