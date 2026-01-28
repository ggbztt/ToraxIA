# 🩻 ToraxIA

Sistema de análisis de radiografías torácicas con Inteligencia Artificial para detección de patologías pulmonares.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red.svg)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.15-orange.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## 📋 Descripción

ToraxIA es una aplicación web desarrollada como proyecto de tesis universitaria que utiliza un modelo de Deep Learning (DenseNet-121) entrenado con el dataset NIH ChestX-ray14 para analizar radiografías torácicas y detectar 14 patologías pulmonares.

### 🎯 Patologías Detectables

| Patología | Patología | Patología |
|-----------|-----------|-----------|
| Atelectasia | Cardiomegalia | Derrame Pleural |
| Infiltración | Masa | Nódulo |
| Neumonía | Neumotórax | Consolidación |
| Edema | Enfisema | Fibrosis |
| Engrosamiento Pleural | Hernia | |

## ✨ Características

- 🔬 **Análisis con IA**: Modelo DenseNet-121 con AUC macro de 0.80
- 🔥 **Grad-CAM**: Visualización de regiones de interés con mapas de activación
- 👥 **Sistema de usuarios**: Autenticación con roles (estudiante/admin)
- 📊 **Historial personal**: Guardado de análisis con imágenes en la nube
- 📄 **Reportes PDF**: Generación de reportes profesionales descargables
- 🔥 **Feed de actividad**: Últimos análisis de la comunidad
- 📚 **Definiciones técnicas**: Base de conocimiento editable
- 🌐 **100% Web**: Funciona desde cualquier navegador

## 🛠️ Tecnologías

- **Frontend**: Streamlit
- **Backend**: Python
- **IA/ML**: TensorFlow, Keras
- **Base de datos**: Supabase (PostgreSQL)
- **Storage**: Supabase Storage
- **Visualización**: Grad-CAM, Matplotlib

## 🚀 Instalación Local

### Prerrequisitos

- Python 3.10 o superior
- pip (gestor de paquetes)

### Pasos

1. **Clonar el repositorio**
```bash
git clone https://github.com/tu-usuario/ToraxIA.git
cd ToraxIA
```

2. **Crear entorno virtual**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**

Crear archivo `.env` en la raíz:
```env
SUPABASE_URL=tu_url_de_supabase
SUPABASE_ANON_KEY=tu_anon_key
SUPABASE_SERVICE_ROLE_KEY=tu_service_role_key
```

5. **Ejecutar la aplicación**
```bash
streamlit run app.py
```

6. **Abrir en el navegador**
```
http://localhost:8501
```

## 📁 Estructura del Proyecto

```
ToraxIA/
├── app.py                 # Aplicación principal
├── config.py              # Configuración de rutas
├── requirements.txt       # Dependencias
├── .env                   # Variables de entorno (no incluir en git)
│
├── models/
│   ├── best_model_epochs13-18.keras  # Modelo entrenado
│   ├── model_loader.py    # Cargador del modelo
│   └── THRESHOLDS.json    # Umbrales optimizados
│
├── services/
│   ├── auth.py            # Autenticación
│   ├── database.py        # Operaciones de BD
│   └── storage_service.py # Almacenamiento de imágenes
│
├── utils/
│   ├── preprocessing.py   # Preprocesamiento de imágenes
│   ├── activation_maps.py # Generación de Grad-CAM
│   ├── pdf_generator.py   # Generación de PDFs
│   ├── translations.py    # Traducciones ES/EN
│   └── connectivity.py    # Detección de conexión
│
├── views/
│   ├── analysis_page.py   # Página de análisis
│   ├── history_page.py    # Historial personal
│   └── login_page.py      # Login/Registro
│
└── assets/
    └── styles.css         # Estilos personalizados
```

## ⚠️ Disclaimer

> **IMPORTANTE**: Esta herramienta es de **apoyo educativo** y **NO sustituye** el criterio médico profesional. Los resultados deben ser interpretados por personal médico calificado. No tomar decisiones clínicas basándose únicamente en este sistema.

## 👨‍💻 Autor

Desarrollado como proyecto de tesis universitaria.

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.
