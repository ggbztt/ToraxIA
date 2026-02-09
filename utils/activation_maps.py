"""
Activation Maps Module - Grad-CAM Implementation
Generación de mapas de activación usando Grad-CAM (Selvaraju et al., 2017)

Método científicamente validado:
- Selvaraju et al. (2017) "Grad-CAM: Visual Explanations from Deep Networks"
- Usado extensivamente en interpretabilidad de modelos médicos

Reemplaza Saliency Maps por Grad-CAM para mejor visualización de regiones relevantes.
"""
import tensorflow as tf
import cv2
import numpy as np
from pathlib import Path
import streamlit as st


def make_gradcam_heatmap(img_array, model, last_conv_layer_name, pred_index=None):
    try:
        if 'densenet121' in [layer.name for layer in model.layers]:
            densenet_layer = model.get_layer('densenet121')
            inner_model = densenet_layer
            last_conv_layer = inner_model.get_layer(last_conv_layer_name)
            grad_model = tf.keras.Model(
                inputs=model.input,
                outputs=[
                    densenet_layer(model.input),
                    model.output
                ]
            )
            activation_model = tf.keras.Model(
                inputs=inner_model.input,
                outputs=inner_model.get_layer(last_conv_layer_name).output
            )
        else:
            last_conv_layer = model.get_layer(last_conv_layer_name)
            grad_model = tf.keras.Model(
                inputs=model.input,
                outputs=[last_conv_layer.output, model.output]
            )
        
        with tf.GradientTape() as tape:
            if 'densenet121' in [layer.name for layer in model.layers]:
                densenet_layer = model.get_layer('densenet121')
                conv_output_model = tf.keras.Model(
                    inputs=densenet_layer.input,
                    outputs=densenet_layer.get_layer(last_conv_layer_name).output
                )
                img_tensor = tf.cast(img_array, tf.float32)
                tape.watch(img_tensor)
                preds = model(img_tensor, training=False)
                conv_outputs = conv_output_model(img_tensor, training=False)
            else:
                img_tensor = tf.cast(img_array, tf.float32)
                tape.watch(img_tensor)
                conv_outputs, preds = grad_model(img_tensor, training=False)
            
            if pred_index is None:
                pred_index = tf.argmax(preds[0])
            
            class_channel = preds[:, pred_index]
        
        grads = tape.gradient(class_channel, conv_outputs)
        
        if grads is None:
            print("⚠️ No se pudieron calcular gradientes, usando método alternativo")
            return _fallback_activation_map(img_array, model, pred_index)
        
        # Promediar gradientes sobre canales (Global Average Pooling de gradientes)
        pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
        
        # Multiplicar cada canal por su importancia
        conv_outputs = conv_outputs[0]
        heatmap = conv_outputs @ pooled_grads[..., tf.newaxis]
        heatmap = tf.squeeze(heatmap)
        
        # Aplicar ReLU y normalizar
        heatmap = tf.maximum(heatmap, 0)
        heatmap = heatmap / (tf.reduce_max(heatmap) + 1e-10)
        
        return heatmap.numpy()
    
    except Exception as e:
        print(f"⚠️ Error en Grad-CAM: {str(e)}, usando método alternativo")
        return _fallback_activation_map(img_array, model, pred_index)


def _fallback_activation_map(img_array, model, class_idx):
    try:
        img_tensor = tf.Variable(img_array, dtype=tf.float32)
        
        with tf.GradientTape() as tape:
            tape.watch(img_tensor)
            predictions = model(img_tensor, training=False)
            if isinstance(class_idx, tf.Tensor):
                class_idx = class_idx.numpy()
            target_class = predictions[:, int(class_idx)]
        
        gradients = tape.gradient(target_class, img_tensor)
        
        # Convertir a saliency map
        saliency = tf.abs(gradients)
        saliency = tf.reduce_max(saliency, axis=-1)[0]
        
        # Suavizar
        saliency_np = saliency.numpy()
        saliency_smooth = cv2.GaussianBlur(saliency_np, (11, 11), 0)
        
        # Normalizar
        saliency_smooth = saliency_smooth / (saliency_smooth.max() + 1e-10)
        
        return saliency_smooth
    
    except Exception as e:
        print(f"❌ Error en fallback: {str(e)}")
        # Retornar mapa vacío como último recurso
        return np.zeros((224, 224))


def create_overlay(original_img, heatmap, alpha=0.4):
    try:
        # Resize heatmap al tamaño de la imagen original
        heatmap_resized = cv2.resize(heatmap, (512, 512))
        
        # Convertir heatmap a colormap JET
        heatmap_uint8 = np.uint8(255 * heatmap_resized)
        heatmap_colored = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
        heatmap_colored = cv2.cvtColor(heatmap_colored, cv2.COLOR_BGR2RGB)
        
        # Preparar imagen original
        if len(original_img.shape) == 2:
            # Si es escala de grises, convertir a RGB
            img_rgb = np.stack([original_img] * 3, axis=-1)
        else:
            img_rgb = original_img.copy()
        
        # Asegurar que esté en rango [0, 255]
        if img_rgb.max() <= 1.0:
            img_rgb = img_rgb * 255
        
        img_uint8 = np.uint8(img_rgb)
        
        # Crear overlay: heatmap * alpha + imagen * (1 - alpha)
        overlay = heatmap_colored * alpha + img_uint8 * (1 - alpha)
        
        return np.uint8(overlay)
    
    except Exception as e:
        st.error(f"❌ Error creando overlay: {str(e)}")
        raise


def save_overlay(overlay, output_path: str):
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


def generate_activation_map_for_top_prediction(model, img_array, predictions, class_names, gradcam_layer=None):
    from config import GRADCAM_LAYER_NAME
    
    # Usar capa configurada si no se especifica
    if gradcam_layer is None:
        gradcam_layer = GRADCAM_LAYER_NAME
    
    # Encontrar clase con mayor probabilidad
    top_class_idx = np.argmax(predictions)
    top_prob = predictions[top_class_idx]
    top_class_name = class_names[top_class_idx]
    
    print(f"\n🔍 Generando Grad-CAM para: {top_class_name} (prob: {top_prob:.3f})")
    
    # Generar heatmap Grad-CAM
    heatmap = make_gradcam_heatmap(
        img_array, 
        model, 
        gradcam_layer,
        pred_index=top_class_idx
    )
    
    print(f"✅ Grad-CAM generado - Min: {heatmap.min():.4f}, "
          f"Max: {heatmap.max():.4f}, Mean: {heatmap.mean():.4f}")
    
    # Crear overlay
    original_img = img_array[0]  # Remover dimensión batch
    overlay = create_overlay(original_img, heatmap, alpha=0.4)
    
    return heatmap, overlay, top_class_name, top_prob


def generate_gradcam_for_class(model, img_array, class_idx, class_names, gradcam_layer=None):
    from config import GRADCAM_LAYER_NAME
    
    if gradcam_layer is None:
        gradcam_layer = GRADCAM_LAYER_NAME
    
    class_name = class_names[class_idx]
    
    print(f"🔍 Generando Grad-CAM para: {class_name}")
    
    # Generar heatmap
    heatmap = make_gradcam_heatmap(
        img_array,
        model,
        gradcam_layer,
        pred_index=class_idx
    )
    
    # Crear overlay
    original_img = img_array[0]
    overlay = create_overlay(original_img, heatmap, alpha=0.4)
    
    return heatmap, overlay, class_name
