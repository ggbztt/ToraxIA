"""
Página de Nuevo Análisis con Formulario Pre-Diagnóstico
Maneja el flujo completo: Formulario → Upload → Análisis → Resultados → Guardar
"""
import streamlit as st
from PIL import Image
import numpy as np
import uuid
from datetime import datetime
import unicodedata

from models.model_loader import load_chestxray_model, get_class_names
from utils.preprocessing import validate_image, preprocess_image, preprocess_for_display
from utils.activation_maps import generate_activation_map_for_top_prediction
from utils.translations import translate_pathology
from services.auth import get_current_user


def render_analysis_page():
    """Página de nuevo análisis con formulario pre-diagnóstico"""
    
    st.markdown('<div class="main-header">📤 Nuevo Análisis</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Completa el formulario y sube una radiografía</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Obtener usuario actual
    user = get_current_user()
    
    # PASO 1: FORMULARIO PRE-DIAGNÓSTICO
    if 'form_completed' not in st.session_state:
        render_pre_diagnosis_form(user)
        return
    
    # PASO 2: UPLOAD Y ANÁLISIS
    st.success("✅ Formulario completado")
    
    # Mostrar resumen del formulario
    with st.expander("📋 Ver datos del formulario", expanded=False):
        form_data = st.session_state.form_data
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Datos del Paciente:**")
            st.write(f"- Nombre: {form_data['paciente_nombre']}")
            st.write(f"- CI: {form_data['paciente_ci']}")
            st.write(f"- Apellido: {form_data['paciente_apellido']}")
            st.write(f"- Edad: {form_data['paciente_edad']} años")
            st.write(f"- Sexo: {form_data['paciente_sexo']}")
            if form_data['paciente_peso']:
                st.write(f"- Peso: {form_data['paciente_peso']} kg")
        
        with col2:
            st.markdown("**Datos Académicos:**")
            st.write(f"- Estudiante: {form_data['academico_nombre']}")
            st.write(f"- CI: {form_data['academico_ci']}")
            st.write(f"- Apellido: {form_data['academico_apellido']}")
            st.write(f"- Área: {form_data['academico_area'].capitalize()}")
            
        if form_data['comentario_sospecha']:
            st.markdown("**Sospecha:**")
            st.write(form_data['comentario_sospecha'])
        
        if form_data['pronostico_real']:
            st.markdown("**Pronóstico Real:**")
            st.write(form_data['pronostico_real'])
    
    # Botón para editar formulario
    if st.button("✏️ Editar Formulario"):
        del st.session_state.form_completed
        st.rerun()
    
    st.markdown("---")
    
    # Upload de imagen
    uploaded_file = st.file_uploader(
        "**Selecciona una radiografía torácica**",
        type=['png', 'jpg', 'jpeg'],
        help="Formatos soportados: PNG, JPG, JPEG"
    )
    
    if uploaded_file is None:
        st.info("👆 Sube una imagen para comenzar el análisis")
        return
    
    # Validar imagen
    if not validate_image(uploaded_file):
        st.error("❌ Formato de archivo no válido. Por favor sube una imagen PNG, JPG o JPEG.")
        return
    
    # Cargar imagen
    try:
        image = Image.open(uploaded_file)
    except Exception as e:
        st.error(f"❌ Error al cargar la imagen: {str(e)}")
        return
    
    # Mostrar preview
    st.success("✅ Imagen cargada correctamente")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### 📷 Vista Previa")
        st.image(image, use_container_width=True)
    
    with col2:
        st.markdown("#### ℹ️ Información")
        st.write(f"**Formato:** {image.format}")
        st.write(f"**Tamaño:** {image.size[0]} x {image.size[1]} px")
        st.write(f"**Modo:** {image.mode}")
    
    st.markdown("---")
    
    # Botón de análisis
    if st.button("🔬 Analizar Radiografía", type="primary", use_container_width=True):
        
        # Obtener modelo precargado
        model = st.session_state.model
        class_names = st.session_state.class_names
        config = st.session_state.get('model_config', {})
        thresholds = config.get('thresholds', {})
        
        # Contenedor de progreso
        progress_container = st.empty()
        
        try:
            # Paso 1: Preprocesar
            progress_container.info("⏳ **Paso 1/2**: Preprocesando imagen...")
            
            img_array = preprocess_image(image)
            img_display = preprocess_for_display(image)
            
            progress_container.success("✅ Imagen preprocesada")
            
            # Paso 2: Predicción + Grad-CAM
            progress_container.info("⏳ **Paso 2/2**: Generando predicciones y Grad-CAM...")
            
            predictions = model.predict(img_array, verbose=0)[0]
            
            heatmap, overlay, top_class_name, top_prob = generate_activation_map_for_top_prediction(
                model, img_array, predictions, class_names
            )
            
            # Guardar en session_state (incluir thresholds e img_array para Grad-CAM adicional)
            st.session_state.analysis_results = {
                'predictions': predictions,
                'class_names': class_names,
                'top_class': top_class_name,
                'top_prob': top_prob,
                'overlay': overlay,
                'original_image': img_display,
                'timestamp': datetime.now().isoformat(),
                'analysis_id': uuid.uuid4().hex,
                'form_data': st.session_state.form_data,  # Incluir datos del formulario
                'thresholds': thresholds,  # Thresholds optimizados
                'img_array': img_array  # Para generar Grad-CAM de otras clases
            }
            
            progress_container.success("✅ ¡Análisis completado exitosamente!")
            
        except Exception as e:
            progress_container.error(f"❌ Error durante el análisis: {str(e)}")
            st.code(f"Detalles del error:\n{str(e)}")
            import traceback
            with st.expander("Ver traceback completo"):
                st.code(traceback.format_exc())
            return
    
    # Mostrar resultados si existen
    if 'analysis_results' in st.session_state:
        show_results(st.session_state.analysis_results)


def render_pre_diagnosis_form(user):
    """Renderiza el formulario pre-diagnóstico"""
    
    st.markdown("### 📝 Formulario Pre-Diagnóstico")
    st.info("💡 Completa estos datos antes de realizar el análisis")
    
    with st.form("pre_diagnosis_form"):
        
        # ============================================
        # SECCIÓN 1: DATOS DEL PACIENTE
        # ============================================
        st.markdown("#### 👤 Datos del Paciente")
        
        # Fila 1: Nombre y Apellido
        col1, col2 = st.columns(2)
        with col1:
            paciente_nombre = st.text_input(
                "Nombre *",
                placeholder="Juan",
                help="Nombre del paciente"
            )
        with col2:
            paciente_apellido = st.text_input(
                "Apellido *",
                placeholder="Pérez",
                help="Apellido del paciente"
            )
        
        # Fila 2: Cédula y Edad
        col1, col2 = st.columns(2)
        with col1:
            paciente_ci = st.text_input(
                "Cédula de Identidad *",
                placeholder="12345678",
                help="CI del paciente"
            )
        with col2:
            paciente_edad = st.text_input(
                "Edad (años) *",
                placeholder="30",
                help="Edad del paciente en años"
            )
        
        # Fila 3: Sexo y Peso
        col1, col2 = st.columns(2)
        with col1:
            paciente_sexo = st.selectbox(
                "Sexo *",
                options=["M", "F", "Otro"],
                format_func=lambda x: {"M": "Masculino", "F": "Femenino", "Otro": "Otro"}[x]
            )
        with col2:
            paciente_peso = st.text_input(
                "Peso (kg) - Opcional",
                placeholder="70",
                help="Peso del paciente en kilogramos (opcional)"
            )
        
        st.markdown("---")
        
        # ============================================
        # SECCIÓN 2: DATOS ACADÉMICOS
        # ============================================
        st.markdown("#### 🎓 Datos Académicos")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Autocompletar con datos del usuario logueado
            academico_nombre = st.text_input(
                "Nombre del Estudiante *",
                value=user['nombre'],
                disabled=True,
                help="Autocompletado desde tu perfil"
            )
            academico_apellido = st.text_input(
                "Apellido del Estudiante *",
                value=user['apellido'],
                disabled=True,
                help="Autocompletado desde tu perfil"
            )
        
        with col2:
            academico_ci = st.text_input(
                "CI del Estudiante *",
                value=user['ci'],
                disabled=True,
                help="Autocompletado desde tu perfil"
            )
            academico_area = st.selectbox(
                "Área de Estudio *",
                options=["radiologia", "medicina", "enfermeria", "otro"],
                index=["radiologia", "medicina", "enfermeria", "otro"].index(user['area_estudio']) if user['area_estudio'] in ["radiologia", "medicina", "enfermeria", "otro"] else 0,
                format_func=lambda x: {
                    "radiologia": "Radiología",
                    "medicina": "Medicina",
                    "enfermeria": "Enfermería",
                    "otro": "Otro"
                }[x],
                disabled=True,
                help="Autocompletado desde tu perfil"
            )
        
        st.markdown("---")
        
        # ============================================
        # SECCIÓN 3: COMENTARIOS
        # ============================================
        st.markdown("#### 💬 Comentarios y Pronóstico")
        
        comentario_sospecha = st.text_area(
            "Sospecha de Pronóstico",
            placeholder="Describe tu sospecha diagnóstica basada en la observación de la radiografía...",
            help="Escribe tu impresión diagnóstica inicial",
            height=100
        )
        
        pronostico_real = st.text_input(
            "Pronóstico Real - Opcional",
            placeholder="Ej: Neumonía",
            help="Si ya conoces el diagnóstico confirmado, ingrésalo aquí"
        )
        
        st.markdown("---")
        
        # Botón de envío
        submitted = st.form_submit_button(
            "✅ Continuar con el Análisis",
            type="primary",
            use_container_width=True
        )
        
        if submitted:
            # Validaciones
            errors = []
            
            # Función para validar nombres (letras, espacios, acentos, guiones)
            import re
            def validate_name(name):
                if not name or len(name.strip()) < 2:
                    return False
                pattern = r'^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s\-]+$'
                return re.match(pattern, name.strip()) is not None
            
            # Validar nombres (solo letras, espacios, acentos y guiones)
            if not paciente_nombre or not paciente_apellido:
                errors.append("El nombre y apellido del paciente son obligatorios")
            else:
                if not validate_name(paciente_nombre):
                    errors.append("El nombre del paciente solo puede contener letras (sin números ni caracteres especiales)")
                if not validate_name(paciente_apellido):
                    errors.append("El apellido del paciente solo puede contener letras (sin números ni caracteres especiales)")
            
            # Validar cédula (solo números, 7-8 dígitos)
            if not paciente_ci:
                errors.append("La cédula del paciente es obligatoria")
            elif not paciente_ci.isdigit():
                errors.append("La cédula del paciente debe contener solo números")
            elif len(paciente_ci) < 7 or len(paciente_ci) > 8:
                errors.append("La cédula debe tener entre 7 y 8 dígitos")
            
            # Validar edad (ahora es text_input)
            if not paciente_edad:
                errors.append("La edad es obligatoria")
            elif not paciente_edad.isdigit():
                errors.append("La edad debe ser un número")
            else:
                edad_num = int(paciente_edad)
                if edad_num < 8 or edad_num > 120:
                    errors.append("La edad debe estar entre 1 y 120 años")
            
            # Validar peso (opcional, pero si se ingresa debe ser válido)
            if paciente_peso:
                try:
                    peso_num = float(paciente_peso)
                    if peso_num < 30 or peso_num > 350:
                        errors.append("El peso debe estar entre 30 y 350 kg")
                except ValueError:
                    errors.append("El peso debe ser un número válido")
            
            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
            else:
                # Guardar datos del formulario en session_state
                st.session_state.form_data = {
                    'paciente_nombre': paciente_nombre,
                    'paciente_apellido': paciente_apellido,
                    'paciente_ci': paciente_ci,
                    'paciente_edad': int(paciente_edad),  # Convertir a int
                    'paciente_sexo': paciente_sexo,
                    'paciente_peso': float(paciente_peso) if paciente_peso else None,  # Convertir a float
                    'academico_nombre': academico_nombre,
                    'academico_apellido': academico_apellido,
                    'academico_ci': academico_ci,
                    'academico_area': academico_area,
                    'comentario_sospecha': comentario_sospecha,
                    'pronostico_real': pronostico_real if pronostico_real else None
                }
                
                st.session_state.form_completed = True
                st.success("✅ Formulario guardado correctamente")
                st.rerun()


def show_results(results):
    """Muestra los resultados del análisis"""
    
    st.markdown("---")
    st.markdown("## 📊 Resultados del Análisis")
    
    # Visualización: Original vs Overlay
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📷 Radiografía Original")
        st.image(results['original_image'], use_container_width=True)
    
    with col2:
        st.markdown("#### 🔥 Mapa de Activación (Grad-CAM)")
        st.image(results['overlay'], use_container_width=True, caption="Regiones de mayor activación del modelo")
    
    st.markdown("---")
    
    # Obtener thresholds
    thresholds = results.get('thresholds', {})
    
    # Top 5 hallazgos con thresholds
    st.markdown("### 🎯 Top 5 Predicciones")
    
    # Ordenar predicciones
    predictions = results['predictions']
    class_names = results['class_names']
    
    sorted_indices = np.argsort(predictions)[::-1]
    top_5_indices = sorted_indices[:5]
    
    # Función para determinar nivel de riesgo
    def get_risk_level(probability):
        """Retorna emoji, texto y color según el porcentaje"""
        prob_pct = probability * 100
        if prob_pct < 25:
            return "🟢", "BAJO", "#27ae60"
        elif prob_pct < 50:
            return "🟡", "MODERADO", "#f1c40f"
        elif prob_pct < 75:
            return "🟠", "ALTO", "#e67e22"
        else:
            return "🔴", "MUY ALTO", "#e74c3c"
    
    # Mostrar top 5 en cards (lógica de thresholds se mantiene para uso interno)
    for i, idx in enumerate(top_5_indices):
        prob = predictions[idx]
        name_en = class_names[idx]  # Nombre en inglés (del modelo)
        name_es = translate_pathology(name_en)  # Traducir a español
        
        # Lógica de detección (para uso interno/comparativas, no se muestra en UI)
        threshold = thresholds.get(name_en, 0.5)
        is_detected = prob >= threshold  # Se guarda para comparativas
        
        # Emoji según ranking
        emojis = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        emoji = emojis[i]
        
        # Obtener nivel de riesgo
        risk_emoji, risk_text, risk_color = get_risk_level(prob)
        
        # Card con definición técnica para el #1
        if i == 0:
            # Card destacada para Top 1
            st.markdown(f"""
            <div style="background-color: #e3f2fd; padding: 1.5rem; border-radius: 10px; border-left: 5px solid #1f77b4; margin-bottom: 1rem;">
                <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                    <div style="font-size: 2rem; margin-right: 1rem;">{emoji}</div>
                    <div style="flex-grow: 1;">
                        <div style="font-size: 1.5rem; font-weight: bold;">{name_es}</div>
                        <div style="display: flex; align-items: center; gap: 1rem;">
                            <span style="font-size: 2rem; color: #1f77b4; font-weight: bold;">{prob*100:.1f}%</span>
                            <span style="background-color: {risk_color}; color: white; padding: 0.25rem 0.75rem; border-radius: 20px; font-weight: bold; font-size: 0.9rem;">{risk_emoji} {risk_text}</span>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Obtener y mostrar definición técnica (usar nombre en inglés para buscar)
            definition = get_technical_definition(name_en)
            if definition:
                st.info(f"📚 **Definición Técnica:** {definition}")
        else:
            # Cards normales para Top 2-5
            st.markdown(f"""
            <div style="background-color: #f0f2f6; padding: 1rem; border-radius: 10px; margin-bottom: 0.5rem;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="display: flex; align-items: center;">
                        <div style="font-size: 1.5rem; margin-right: 1rem;">{emoji}</div>
                        <div style="font-size: 1.1rem; font-weight: bold;">{name_es}</div>
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.75rem;">
                        <span style="font-size: 1.5rem; color: #1f77b4; font-weight: bold;">{prob*100:.1f}%</span>
                        <span style="background-color: {risk_color}; color: white; padding: 0.2rem 0.5rem; border-radius: 15px; font-weight: bold; font-size: 0.8rem;">{risk_emoji} {risk_text}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Botón para ver Grad-CAM de otras predicciones
    st.markdown("---")
    with st.expander("🔍 Ver Grad-CAM de otras predicciones (Top 2-5)"):
        st.info("💡 Genera mapas de activación para las otras predicciones del Top 5")
        
        # Solo mostrar si hay imagen preprocesada guardada
        if 'img_array' in results:
            img_array = results['img_array']
            model = st.session_state.get('model')
            
            if model is not None:
                from utils.activation_maps import generate_gradcam_for_class
                
                for i, idx in enumerate(top_5_indices[1:5], start=2):  # Top 2-5
                    name_en = class_names[idx]
                    name_es = translate_pathology(name_en)
                    prob = predictions[idx]
                    
                    if st.button(f"Generar Grad-CAM para {name_es} ({prob*100:.1f}%)", key=f"gradcam_{idx}"):
                        with st.spinner(f"Generando Grad-CAM para {name_es}..."):
                            try:
                                heatmap, overlay, _ = generate_gradcam_for_class(
                                    model, img_array, idx, class_names
                                )
                                st.image(overlay, caption=f"Grad-CAM: {name_es}", use_container_width=True)
                            except Exception as e:
                                st.error(f"Error generando Grad-CAM: {str(e)}")
            else:
                st.warning("⚠️ El modelo no está disponible para generar Grad-CAM adicionales")
        else:
            st.warning("⚠️ Los datos de imagen no están disponibles. Realiza un nuevo análisis para usar esta función.")
    
    st.markdown("---")
    
    # Verificación de pronóstico (si existe)
    if results.get('form_data', {}).get('pronostico_real'):
        pronostico_real = results['form_data']['pronostico_real']
        top_class_en = results['top_class']  # Nombre en inglés del modelo
        top_class_es = translate_pathology(top_class_en)  # Traducir a español
        
        st.markdown("### ✅ Verificación de Pronóstico")
        
        # Función para normalizar texto (quitar acentos, minúsculas, espacios)
        def normalize_text(text):
            """Normaliza texto: quita acentos, convierte a minúsculas, quita espacios"""
            # Quitar acentos
            text = unicodedata.normalize('NFD', text)
            text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
            # Minúsculas y quitar espacios/guiones
            text = text.lower().replace(' ', '').replace('_', '').replace('-', '')
            return text
        
        # Normalizar el pronóstico ingresado por el usuario
        pronostico_normalizado = normalize_text(pronostico_real)
        
        # Normalizar el top 1 en ambos idiomas
        top_class_en_norm = normalize_text(top_class_en)
        top_class_es_norm = normalize_text(top_class_es)
        
        # Verificar si coincide (comparar con inglés Y español)
        acerto = (pronostico_normalizado in top_class_en_norm or 
                  top_class_en_norm in pronostico_normalizado or
                  pronostico_normalizado in top_class_es_norm or 
                  top_class_es_norm in pronostico_normalizado)
        
        if acerto:
            st.success(f"🎯 **¡ToraxIA acertó!** El pronóstico real '{pronostico_real}' coincide con la predicción principal: **{top_class_es}** ({top_class_en}).")
        else:
            # Verificar si está en top 5
            predictions = results['predictions']
            class_names = results['class_names']
            sorted_indices = np.argsort(predictions)[::-1]
            top_5_indices = sorted_indices[:5]
            
            top_5_names_en = [class_names[idx] for idx in top_5_indices]
            top_5_names_es = [translate_pathology(name) for name in top_5_names_en]
            
            # Verificar con top 5 (tanto inglés como español)
            en_top_5 = False
            for name_en, name_es in zip(top_5_names_en, top_5_names_es):
                name_en_norm = normalize_text(name_en)
                name_es_norm = normalize_text(name_es)
                if (pronostico_normalizado in name_en_norm or 
                    name_en_norm in pronostico_normalizado or
                    pronostico_normalizado in name_es_norm or 
                    name_es_norm in pronostico_normalizado):
                    en_top_5 = True
                    break
            
            if en_top_5:
                st.warning(f"⚠️ El pronóstico real '{pronostico_real}' está en el Top 5, pero no es la predicción principal (que es **{top_class_es}**).")
            else:
                st.error(f"❌ El pronóstico real '{pronostico_real}' no coincide con las predicciones principales. ToraxIA predice: **{top_class_es}** ({top_class_en}).")
        
        st.markdown("---")
    
    # Tabla completa de probabilidades
    st.markdown("### 📋 Tabla Completa de Probabilidades")
    
    import pandas as pd
    
    # Traducir nombres de patologías a español
    class_names_es = [translate_pathology(name) for name in class_names]
    
    # Crear lista de niveles de riesgo
    niveles = [get_risk_level(prob)[1] for prob in predictions]  # [1] es el texto del nivel
    
    df = pd.DataFrame({
        'Patología': class_names_es,  # Usar nombres en español
        'Probabilidad': predictions,
        'Nivel': niveles
    })
    
    df = df.sort_values('Probabilidad', ascending=False).reset_index(drop=True)
    df['Probabilidad'] = df['Probabilidad'].apply(lambda x: f"{x*100:.2f}%")
    
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=False,
        column_config={
            "Patología": st.column_config.TextColumn("Patología", width="medium"),
            "Probabilidad": st.column_config.TextColumn("Probabilidad", width="small"),
            "Nivel": st.column_config.TextColumn("Nivel", width="small"),
        }
    )
    
    st.markdown("---")
    
    # Disclaimer
    st.warning("""
    ⚠️ **IMPORTANTE - Disclaimer Médico**
    
    Esta herramienta es de **apoyo educativo** y **NO sustituye** el criterio médico profesional.
    Los resultados deben ser interpretados por personal médico calificado.
    No tomar decisiones clínicas basándose únicamente en este sistema.
    """)
    
    st.markdown("---")
    
    # Acciones
    st.markdown("### 🎬 Acciones")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        try:
            from utils.pdf_generator import generate_report
            from config import REPORTS_DIR
            
            # Generar nombre único para el PDF
            pdf_filename = f"{results['analysis_id']}_report.pdf"
            pdf_path = REPORTS_DIR / pdf_filename
            
            # Generar PDF
            pdf_bytes = generate_report(results, pdf_path)
            
            # Botón de descarga directo
            st.download_button(
                label="📄 Descargar Reporte PDF",
                data=pdf_bytes,
                file_name=pdf_filename,
                mime="application/pdf",
                type="primary"
            )
            
        except Exception as e:
            st.error(f"❌ Error generando PDF: {str(e)}")
    
    with col2:
        if st.button("💾 Guardar en Historial"):
            save_to_database(results)
    
    with col3:
        if st.button("🔄 Nuevo Análisis"):
            # Limpiar resultados y formulario
            if 'analysis_results' in st.session_state:
                del st.session_state.analysis_results
            if 'form_completed' in st.session_state:
                del st.session_state.form_completed
            if 'form_data' in st.session_state:
                del st.session_state.form_data
            st.rerun()


def get_technical_definition(pathology_name: str) -> str:
    """Obtiene la definición técnica de una patología desde Supabase"""
    try:
        from services.auth import get_supabase_client
        supabase = get_supabase_client()
        
        # Buscar definición
        result = supabase.table('pathology_definitions').select('technical_definition').eq('pathology_name', pathology_name).execute()
        
        if result.data:
            return result.data[0]['technical_definition']
        return None
        
    except Exception as e:
        st.error(f"Error obteniendo definición: {str(e)}")
        return None


def save_to_database(results):
    """Guarda el análisis en Supabase (solo si hay internet)"""
    from services.database import save_analysis_to_database
    from utils.connectivity import check_internet_connection
    
    # Verificar conexión primero
    if not check_internet_connection():
        st.error("❌ No hay conexión a internet. No se puede guardar el análisis en la base de datos.")
        st.info("💡 El análisis se puede descargar como PDF, pero no se guardará en tu historial hasta que tengas conexión.")
        return
    
    # Obtener datos del formulario
    form_data = results.get('form_data', {})
    
    if not form_data:
        st.error("❌ No se encontraron datos del formulario. No se puede guardar el análisis.")
        return
    
    # Mostrar spinner mientras se guarda
    with st.spinner("💾 Guardando análisis en la base de datos..."):
        success, message = save_analysis_to_database(results, form_data)
    
    if success:
        st.success(message)
        st.balloons()
        st.info("📊 El análisis ahora aparecerá en tu historial personal y en la actividad reciente.")
    else:
        st.error(message)
        st.warning("⚠️ El análisis no se guardó. Puedes intentar de nuevo o descargar el PDF como respaldo.")
