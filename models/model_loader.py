"""
Model Loader Module
Carga segura del modelo DenseNet-121 pre-entrenado con caché de Streamlit
Incluye carga de thresholds optimizados por patología
"""
import streamlit as st
from tensorflow.keras.models import load_model
import json
from pathlib import Path
from config import MODEL_PATH, MODEL_CONFIG_PATH, THRESHOLDS_PATH, GRADCAM_LAYER_NAME


@st.cache_resource
def load_chestxray_model():
    try:
        # Verificar existencia
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Modelo no encontrado en: {MODEL_PATH}\n"
                f"Por favor, coloca 'best_model_epochs13-18.keras' en la carpeta 'models/'"
            )
        
        model = load_model(str(MODEL_PATH))
        print(f"✅ Modelo cargado exitosamente desde {MODEL_PATH}")
        print(f"   Output shape: {model.output_shape}")
        
        config = load_model_config()
        
        thresholds = load_thresholds()
        config['thresholds'] = thresholds
        
        config['gradcam_layer'] = GRADCAM_LAYER_NAME
        
        return model, config
    
    except Exception as e:
        st.error(f"❌ Error al cargar el modelo: {str(e)}")
        raise

def load_model_config():
    try:
        with open(MODEL_CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print(f"✅ Configuración cargada: {len(config.get('pathologies', []))} patologías")
        return config
    
    except FileNotFoundError:
        print("⚠️ model_config.json no encontrado, usando configuración por defecto")
        return {
            "pathologies": [
                "Atelectasis", "Cardiomegaly", "Effusion", "Infiltration",
                "Mass", "Nodule", "Pneumonia", "Pneumothorax",
                "Consolidation", "Edema", "Emphysema", "Fibrosis",
                "Pleural_Thickening", "Hernia"
            ],
            "input_shape": [224, 224, 3],
            "architecture": "DenseNet121"
        }
    
    except Exception as e:
        st.error(f"❌ Error al cargar configuración: {str(e)}")
        raise


def load_thresholds():
    try:
        with open(THRESHOLDS_PATH, 'r', encoding='utf-8') as f:
            thresholds = json.load(f)
        
        print(f"✅ Thresholds cargados: {len(thresholds)} patologías")
        return thresholds
    
    except FileNotFoundError:
        print("⚠️ THRESHOLDS.json no encontrado, usando 0.5 por defecto")
        return {
            "Atelectasis": 0.5, "Cardiomegaly": 0.5, "Effusion": 0.5, 
            "Infiltration": 0.5, "Mass": 0.5, "Nodule": 0.5, "Pneumonia": 0.5, 
            "Pneumothorax": 0.5, "Consolidation": 0.5, "Edema": 0.5, 
            "Emphysema": 0.5, "Fibrosis": 0.5, "Pleural_Thickening": 0.5, "Hernia": 0.5
        }
    
    except Exception as e:
        st.error(f"❌ Error al cargar thresholds: {str(e)}")
        raise


def get_class_names():
    config = load_model_config()
    return config.get('pathologies', [])


def get_thresholds():
    return load_thresholds()

