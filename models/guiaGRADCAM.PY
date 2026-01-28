import numpy as np
import tensorflow as tf
from tensorflow import keras
import cv2
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from pathlib import Path
import os


model_path = '/kaggle/input/v3-toraxia/best_model_epochs13-18.keras'
try:
    model = keras.models.load_model(model_path)
    print("✅ Modelo cargado correctamente")
    print(f"   Capas totales: {len(model.layers)}")
except Exception as e:
    print(f"❌ Error: {e}")
    raise

# ============================================================
# 2. ACCEDER A DENSENET121 INTERNO
# ============================================================

print("\n🔍 Accediendo a DenseNet121 interno...")

densenet_layer = model.get_layer('densenet121')
print(f"✅ Capa DenseNet121 encontrada")

# Última capa convolucional
LAST_CONV_LAYER_NAME = 'conv5_block16_concat'

# Verificar que existe (sin intentar acceder a output_shape)
try:
    last_conv_layer = densenet_layer.get_layer(LAST_CONV_LAYER_NAME)
    print(f"✅ Capa '{LAST_CONV_LAYER_NAME}' encontrada")
    # No imprimir output_shape porque Concatenate no lo tiene
    print(f"   Tipo de capa: {type(last_conv_layer).__name__}")
except Exception as e:
    print(f"❌ Error: {e}")
    print("   Listando últimas capas de DenseNet121:")
    for layer in densenet_layer.layers[-10:]:
        print(f"   - {layer.name} ({type(layer).__name__})")
    raise



# ============================================================
# 3. CREAR MODELO GRAD-CAM (MÉTODO ALTERNATIVO)
# ============================================================

print("\n🏗️ Construyendo modelo Grad-CAM...")

# Obtener la capa DenseNet121
densenet_layer = model.get_layer('densenet121')

# Crear un nuevo modelo que va desde el input de DenseNet hasta la última conv
last_conv_layer_model = keras.models.Model(
    densenet_layer.input,
    densenet_layer.get_layer(LAST_CONV_LAYER_NAME).output
)

# Crear modelo para clasificador (después de DenseNet)
classifier_input = keras.Input(shape=last_conv_layer_model.output.shape[1:])
x = keras.layers.GlobalAveragePooling2D()(classifier_input)
x = model.get_layer('dropout')(x, training=False)
classifier_output = model.get_layer('predictions')(x)

classifier_model = keras.models.Model(classifier_input, classifier_output)

print("✅ Modelos Grad-CAM creados")

# ============================================================
# 4. FUNCIÓN GRAD-CAM CORREGIDA
# ============================================================

def make_gradcam_heatmap(img_array, last_conv_layer_model, classifier_model, pred_index=None):
    """
    Genera heatmap de Grad-CAM.
    
    Args:
        img_array: Imagen (1, 512, 512, 3)
        last_conv_layer_model: Modelo input → última capa conv
        classifier_model: Modelo conv → predicciones
        pred_index: Clase a visualizar
    
    Returns:
        heatmap: Array (H, W) normalizado 0-1
    """
    # Pasar por DenseNet hasta última conv con GradientTape
    with tf.GradientTape() as tape:
        # Obtener activaciones de última conv
        conv_outputs = last_conv_layer_model(img_array)
        tape.watch(conv_outputs)
        
        # Pasar por clasificador
        predictions = classifier_model(conv_outputs)
        
        if pred_index is None:
            pred_index = tf.argmax(predictions[0])
        
        class_channel = predictions[:, pred_index]
    
    # Gradientes de la clase respecto a conv_outputs
    grads = tape.gradient(class_channel, conv_outputs)
    
    # Global Average Pooling de gradientes
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
    
    # Convertir a numpy
    conv_outputs = conv_outputs[0].numpy()
    pooled_grads = pooled_grads.numpy()
    
    # Ponderar cada canal
    for i in range(pooled_grads.shape[-1]):
        conv_outputs[:, :, i] *= pooled_grads[i]
    
    # Promedio sobre canales
    heatmap = np.mean(conv_outputs, axis=-1)
    
    # Normalizar
    heatmap = np.maximum(heatmap, 0)
    if np.max(heatmap) != 0:
        heatmap /= np.max(heatmap)
    
    return heatmap

# ============================================================
# 5. FUNCIÓN DE SUPERPOSICIÓN (SIN CAMBIOS)
# ============================================================

def save_and_display_gradcam(img_path, heatmap, cam_path, alpha=0.4):
    """Superpone heatmap sobre imagen original."""
    img = cv2.imread(img_path)
    if img is None:
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    
    img = cv2.resize(img, (512, 512))
    heatmap_resized = cv2.resize(heatmap, (512, 512))
    heatmap_uint8 = np.uint8(255 * heatmap_resized)
    heatmap_colored = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
    superimposed_img = cv2.addWeighted(img, 1-alpha, heatmap_colored, alpha, 0)
    cv2.imwrite(cam_path, superimposed_img)
    
    return superimposed_img

# ============================================================
# 6. ANÁLISIS COMPLETO CORREGIDO
# ============================================================

def analyze_image_with_gradcam(image_path, model, last_conv_layer_model, 
                                classifier_model, pathologies, thresholds, 
                                output_dir='gradcam_results'):
    """Análisis completo: predicción + Grad-CAM."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Preprocesar
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print(f"❌ No se pudo cargar: {image_path}")
        return
    
    img_resized = cv2.resize(img, (512, 512))
    img_preprocessed = img_resized.astype(np.float32) / 255.0
    img_preprocessed = np.stack([img_preprocessed] * 3, axis=-1)
    img_array = np.expand_dims(img_preprocessed, axis=0)
    
    # Predicción
    predictions = model.predict(img_array, verbose=0)[0]
    
    print(f"\n{'='*70}")
    print(f"📸 Imagen: {os.path.basename(image_path)}")
    print(f"\n🔮 PREDICCIONES:")
    
    detected = []
    for i, pathology in enumerate(pathologies):
        prob = predictions[i]
        threshold = thresholds[pathology]
        
        if prob >= threshold:
            detected.append((pathology, prob, i))
            print(f"   ✓ {pathology:20s} {prob:.3f} (threshold: {threshold:.3f})")
    
    if not detected:
        print("   ✗ No se detectaron patologías")
        top_3_idx = np.argsort(predictions)[-3:][::-1]
        print("\n   Top 3 probabilidades:")
        for idx in top_3_idx:
            print(f"   - {pathologies[idx]:20s} {predictions[idx]:.3f}")
        return
    
    print(f"\n🔬 Generando Grad-CAM para {len(detected)} patología(s)...")
    
    # Visualización
    n_detected = len(detected)
    fig, axes = plt.subplots(n_detected, 3, figsize=(15, 5*n_detected))
    
    if n_detected == 1:
        axes = axes.reshape(1, -1)
    
    for idx, (pathology, prob, class_idx) in enumerate(detected):
        print(f"   → {pathology}...")
        
        # Generar heatmap
        heatmap = make_gradcam_heatmap(
            img_array, last_conv_layer_model, classifier_model, pred_index=class_idx
        )
        
        # Guardar
        cam_path = os.path.join(output_dir, f"{pathology}_gradcam.jpg")
        superimposed = save_and_display_gradcam(image_path, heatmap, cam_path, alpha=0.4)
        
        # Plot original
        axes[idx, 0].imshow(img_resized, cmap='gray')
        axes[idx, 0].set_title('Rayos X Original', fontsize=12, fontweight='bold')
        axes[idx, 0].axis('off')
        
        # Plot heatmap
        im = axes[idx, 1].imshow(heatmap, cmap='jet')
        axes[idx, 1].set_title('Grad-CAM Heatmap', fontsize=12, fontweight='bold')
        axes[idx, 1].axis('off')
        plt.colorbar(im, ax=axes[idx, 1], fraction=0.046, pad=0.04)
        
        # Plot superposición
        axes[idx, 2].imshow(cv2.cvtColor(superimposed, cv2.COLOR_BGR2RGB))
        axes[idx, 2].set_title(f'{pathology}\nProbabilidad: {prob:.3f}', 
                              fontsize=12, fontweight='bold')
        axes[idx, 2].axis('off')
    
    plt.tight_layout()
    summary_path = os.path.join(output_dir, 'gradcam_summary.png')
    plt.savefig(summary_path, dpi=150, bbox_inches='tight')
    print(f"✅ Guardado: {summary_path}")
    plt.show()

# ============================================================
# 7. CONFIGURACIÓN
# ============================================================

ls_pat = [
    'Atelectasis', 'Cardiomegaly', 'Effusion', 'Infiltration',
    'Mass', 'Nodule', 'Pneumonia', 'Pneumothorax',
    'Consolidation', 'Edema', 'Emphysema', 'Fibrosis',
    'Pleural_Thickening', 'Hernia'
]

optimal_thresholds = {
    "Atelectasis": 0.10,
    "Cardiomegaly": 0.10,
    "Effusion": 0.171,
    "Infiltration": 0.10,
    "Mass": 0.122,
    "Nodule": 0.10,
    "Pneumonia": 0.15,
    "Pneumothorax": 0.10,
    "Consolidation": 0.10,
    "Edema": 0.10,
    "Emphysema": 0.10,
    "Fibrosis": 0.20,
    "Pleural_Thickening": 0.10,
    "Hernia": 0.35
}

# ============================================================
# 8. EJECUTAR ANÁLISIS
# ============================================================

print("\n" + "="*70)
print("🚀 EJECUTANDO ANÁLISIS GRAD-CAM")
print("="*70)

dataset_path = '/kaggle/input/data'

def find_image_path(image_name, base_path):
    """Busca imagen en las carpetas del dataset."""
    for i in range(1, 13):
        folder_name = f"images_{i:03d}"
        full_path = os.path.join(base_path, folder_name, "images", image_name)
        if os.path.exists(full_path):
            return full_path
    return None

# Analizar casos del test set
from sklearn.model_selection import train_test_split
import pandas as pd

print("\n📊 Cargando test set...")

csv_path = '/kaggle/input/data/Data_Entry_2017.csv'
df = pd.read_csv(csv_path)

def create_multilabel_vector(finding_labels, pathologies):
    label_vector = np.zeros(len(pathologies), dtype=np.float32)
    if finding_labels != "No Finding":
        diseases = finding_labels.split('|')
        for disease in diseases:
            if disease in pathologies:
                idx = pathologies.index(disease)
                label_vector[idx] = 1.0
    return label_vector

df['multilabel'] = df['Finding Labels'].apply(lambda x: create_multilabel_vector(x, ls_pat))

SAMPLE_SIZE = 112120
sample_df = df.sample(n=SAMPLE_SIZE, random_state=42).reset_index(drop=True)

train_df, temp_df = train_test_split(sample_df, test_size=0.3, random_state=42)
val_df, test_df = train_test_split(temp_df, test_size=0.5, random_state=42)

print(f"✅ Test set: {len(test_df):,} imágenes")

# Seleccionar casos interesantes
print("\n🔍 Seleccionando casos con patologías...")

selected_images = []

# 1. Casos con múltiples patologías
multi_cases = test_df[test_df['Finding Labels'].str.contains(r"\|", regex=True)]
if len(multi_cases) > 0:
    multi_sample = multi_cases.sample(min(3, len(multi_cases)), random_state=42)
    selected_images.extend(multi_sample['Image Index'].tolist())
    print(f"   ✓ {len(multi_sample)} casos con múltiples patologías")

# 2. Casos con patologías individuales interesantes
interesting_pathologies = ['Effusion', 'Pneumothorax', 'Cardiomegaly', 'Mass', 'Emphysema']

for pathology in interesting_pathologies:
    cases = test_df[test_df['Finding Labels'] == pathology]
    if len(cases) > 0:
        sample_case = cases.sample(1, random_state=42)
        img_name = sample_case['Image Index'].values[0]
        if img_name not in selected_images:
            selected_images.append(img_name)
            print(f"   ✓ 1 caso con {pathology}")

print(f"\n✅ Total: {len(selected_images)} casos seleccionados para análisis")

# Analizar cada caso
for img_name in selected_images:
    case_info = test_df[test_df['Image Index'] == img_name]
    if len(case_info) == 0:
        continue
    
    findings = case_info['Finding Labels'].values[0]
    
    print(f"\n{'='*70}")
    print(f"📋 DIAGNÓSTICO REAL: {findings}")
    
    img_path = find_image_path(img_name, dataset_path)
    
    if img_path:
        analyze_image_with_gradcam(
            img_path, model, last_conv_layer_model, classifier_model,
            ls_pat, optimal_thresholds,
            output_dir=f'gradcam_results/{img_name.split(".")[0]}'
        )
    else:
        print(f"⚠️  Imagen no encontrada: {img_name}")

print("\n" + "="*70)
print("🎉 ANÁLISIS GRAD-CAM COMPLETADO")
print("="*70)
print("\n💾 Resultados guardados en: gradcam_results/")
