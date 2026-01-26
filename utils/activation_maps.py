"""
Activation Maps Module
Generación de Saliency Maps usando gradientes (Simonyan et al., 2013)

Método científicamente validado usado en:
- Simonyan et al. (2013) "Deep Inside Convolutional Networks"
- Springenberg et al. (2015) "Striving for Simplicity"

Nota: Se usa Saliency Maps en lugar de Grad-CAM debido a problemas
de BatchNormalization en modo training vs inference.
"""
import tensorflow as tf
import cv2
import numpy as np
from pathlib import Path
import streamlit as st


def generate_saliency_map(model, img_array, class_idx):
    """
    Genera Saliency Map con visualización estilo Grad-CAM.
    
    Algoritmo:
    1. Convertir imagen a tf.Variable
    2. Usar tf.GradientTape para calcular gradientes
    3. Calcular magnitud absoluta de gradientes
    4. Reducir dimensión de color con max()
    5. Normalizar a [0, 1]
    6. Aplicar Gaussian blur para suavizar
    
    Args:
        model: Modelo Keras cargado
        img_array: Array de imagen preprocesada (1, 224, 224, 3)
        class_idx: Índice de la clase a visualizar
    
    Returns:
        np.ndarray: Saliency map normalizada (224, 224)
    """
    try:
        # 1. Convertir a Variable para que TensorFlow pueda calcular gradientes
        img_tensor = tf.Variable(img_array, dtype=tf.float32)
        
        # 2. Calcular gradientes
        with tf.GradientTape() as tape:
            tape.watch(img_tensor)
            predictions = model(img_tensor, training=False)
            target_class = predictions[:, class_idx]
        
        # 3. Gradientes respecto a la imagen de entrada
        gradients = tape.gradient(target_class, img_tensor)
        
        # 4. Convertir a saliency map
        saliency = tf.abs(gradients)
        saliency = tf.reduce_max(saliency, axis=-1)[0]  # Max across RGB channels
        
        # 5. Suavizar con Gaussian blur (estándar en papers científicos)
        saliency_np = saliency.numpy()
        saliency_smooth = cv2.GaussianBlur(saliency_np, (11, 11), 0)
        
        # 6. Normalizar a [0, 1]
        saliency_smooth = saliency_smooth / (saliency_smooth.max() + 1e-10)
        
        print(f"✅ Saliency Map generado - Min: {saliency_smooth.min():.4f}, "
              f"Max: {saliency_smooth.max():.4f}, Mean: {saliency_smooth.mean():.4f}")
        
        return saliency_smooth
    
    except Exception as e:
        st.error(f"❌ Error generando Saliency Map: {str(e)}")
        raise


def create_overlay(original_img, saliency_map, alpha=0.5):
    """
    Crea overlay con colormap JET (igual que Grad-CAM).
    
    Args:
        original_img: Imagen original (224, 224, 3) normalizada [0, 1]
        saliency_map: Mapa de saliency (224, 224) normalizado [0, 1]
        alpha: Peso del heatmap en el overlay (0.5 = 50/50)
    
    Returns:
        np.ndarray: Imagen overlay en formato uint8 RGB (224, 224, 3)
    """
    try:
        # Resize si es necesario
        if saliency_map.shape != (224, 224):
            saliency_map = cv2.resize(saliency_map, (224, 224))
        
        # Convertir saliency a heatmap con colormap JET
        saliency_uint8 = np.uint8(255 * saliency_map)
        heatmap = cv2.applyColorMap(saliency_uint8, cv2.COLORMAP_JET)
        heatmap = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)
        
        # Preparar imagen original
        if len(original_img.shape) == 2:
            # Si es escala de grises, convertir a RGB
            img_rgb = np.stack([original_img] * 3, axis=-1)
        else:
            img_rgb = original_img
        
        # Asegurar que esté en rango [0, 255]
        if img_rgb.max() <= 1.0:
            img_rgb = img_rgb * 255
        
        img_uint8 = np.uint8(img_rgb)
        
        # Crear overlay: heatmap * alpha + imagen * (1 - alpha)
        overlay = heatmap * alpha + img_uint8 * (1 - alpha)
        
        return np.uint8(overlay)
    
    except Exception as e:
        st.error(f"❌ Error creando overlay: {str(e)}")
        raise


def save_overlay(overlay, output_path: str):
    """
    Guarda imagen overlay en disco.
    
    Args:
        overlay: Imagen overlay (numpy array)
        output_path: Path donde guardar (str o Path)
    """
    try:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # OpenCV usa BGR, convertir de RGB
        overlay_bgr = cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR)
        cv2.imwrite(str(output_path), overlay_bgr)
        
        print(f"✅ Overlay guardado en: {output_path}")
    
    except Exception as e:
        st.error(f"❌ Error guardando overlay: {str(e)}")
        raise


def generate_activation_map_for_top_prediction(model, img_array, predictions, class_names):
    """
    Genera mapa de activación para la predicción con mayor probabilidad.
    
    Args:
        model: Modelo Keras
        img_array: Imagen preprocesada (1, 224, 224, 3)
        predictions: Array de predicciones (14,)
        class_names: Lista de nombres de clases
    
    Returns:
        tuple: (saliency_map, overlay, top_class_name, top_prob)
    """
    # Encontrar clase con mayor probabilidad
    top_class_idx = np.argmax(predictions)
    top_prob = predictions[top_class_idx]
    top_class_name = class_names[top_class_idx]
    
    print(f"\n🔍 Generando mapa para: {top_class_name} (prob: {top_prob:.3f})")
    
    # Generar saliency map
    saliency_map = generate_saliency_map(model, img_array, top_class_idx)
    
    # Crear overlay
    original_img = img_array[0]  # Remover dimensión batch
    overlay = create_overlay(original_img, saliency_map, alpha=0.5)
    
    return saliency_map, overlay, top_class_name, top_prob
