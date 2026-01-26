"""
Página de Historial Personal
Muestra los análisis guardados del usuario actual
"""
import streamlit as st
from datetime import datetime
from services.database import get_user_analyses
from services.auth import get_current_user
from utils.translations import translate_pathology


def render_history_page():
    """Renderiza la página de historial personal"""
    
    st.markdown('<div class="main-header">📊 Mi Historial</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Mis análisis guardados</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Obtener usuario actual
    user = get_current_user()
    user_id = user['id']
    
    # Filtro por cédula del paciente
    st.markdown("### 🔍 Buscar por Paciente")
    
    search_ci = st.text_input(
        "Cédula del Paciente",
        placeholder="Ingresa la CI para filtrar...",
        help="Busca análisis por cédula del paciente",
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # Obtener análisis del usuario
    with st.spinner("📥 Cargando historial..."):
        analyses = get_user_analyses(user_id, limit=100)
    
    if not analyses:
        st.info("📭 No tienes análisis guardados aún.")
        st.markdown("💡 Realiza un análisis y guárdalo para verlo aquí.")
        return
    
    # Filtrar por cédula si se ingresó
    if search_ci:
        analyses = [a for a in analyses if search_ci in a.get('paciente_ci', '')]
        
        if not analyses:
            st.warning(f"⚠️ No se encontraron análisis para la cédula: {search_ci}")
            return
    
    # Mostrar total de análisis
    st.markdown(f"### 📋 Total de Análisis: **{len(analyses)}**")
    
    if search_ci:
        st.caption(f"Mostrando resultados para CI: {search_ci}")
    
    st.markdown("---")
    
    # Mostrar análisis en cards expandibles
    for i, analysis in enumerate(analyses):
        render_analysis_card(analysis, i)


def render_analysis_card(analysis: dict, index: int):
    """Renderiza una tarjeta de análisis"""
    
    # Extraer datos
    timestamp = analysis.get('timestamp', '')
    paciente_nombre = analysis.get('paciente_nombre', 'N/A')
    paciente_apellido = analysis.get('paciente_apellido', 'N/A')
    paciente_ci = analysis.get('paciente_ci', 'N/A')
    paciente_edad = analysis.get('paciente_edad', 'N/A')
    paciente_sexo = analysis.get('paciente_sexo', 'N/A')
    
    top_prediction_en = analysis.get('top_prediction', 'N/A')
    top_prediction_es = translate_pathology(top_prediction_en)
    top_probability = analysis.get('top_probability', 0)
    
    acerto_toraxia = analysis.get('acerto_toraxia')
    pronostico_real = analysis.get('pronostico_real')
    
    # Formatear fecha
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        fecha_str = dt.strftime("%d/%m/%Y %H:%M")
    except:
        fecha_str = timestamp
    
    # Determinar color según probabilidad
    if top_probability >= 0.7:
        prob_color = "#d32f2f"  # Rojo (alta probabilidad)
    elif top_probability >= 0.4:
        prob_color = "#f57c00"  # Naranja (media)
    else:
        prob_color = "#388e3c"  # Verde (baja)
    
    # Emoji de verificación
    if acerto_toraxia is True:
        verificacion_emoji = "✅"
        verificacion_text = "ToraxIA acertó"
    elif acerto_toraxia is False:
        verificacion_emoji = "❌"
        verificacion_text = "ToraxIA no acertó"
    else:
        verificacion_emoji = "➖"
        verificacion_text = "Sin verificación"
    
    # Título del expander
    expander_title = f"📋 {fecha_str} | {paciente_nombre} {paciente_apellido} (CI: {paciente_ci}) | **{top_prediction_es}** ({top_probability*100:.1f}%)"
    
    if acerto_toraxia is not None:
        expander_title += f" | {verificacion_emoji}"
    
    with st.expander(expander_title, expanded=False):
        
        # Información del paciente
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 👤 Datos del Paciente")
            st.write(f"**Nombre:** {paciente_nombre} {paciente_apellido}")
            st.write(f"**CI:** {paciente_ci}")
            st.write(f"**Edad:** {paciente_edad} años")
            st.write(f"**Sexo:** {paciente_sexo}")
            
            if analysis.get('paciente_peso'):
                st.write(f"**Peso:** {analysis['paciente_peso']} kg")
        
        with col2:
            st.markdown("#### 🎓 Datos Académicos")
            st.write(f"**Estudiante:** {analysis.get('academico_nombre')} {analysis.get('academico_apellido')}")
            st.write(f"**CI:** {analysis.get('academico_ci')}")
            st.write(f"**Área:** {analysis.get('academico_area', 'N/A').capitalize()}")
        
        st.markdown("---")
        
        # Predicción principal
        st.markdown("#### 🎯 Predicción Principal")
        st.markdown(f"""
        <div style="background-color: #e3f2fd; padding: 1rem; border-radius: 10px; border-left: 5px solid {prob_color};">
            <div style="font-size: 1.3rem; font-weight: bold;">{top_prediction_es}</div>
            <div style="font-size: 0.9rem; color: #666;">{top_prediction_en}</div>
            <div style="font-size: 1.8rem; color: {prob_color}; font-weight: bold; margin-top: 0.5rem;">{top_probability*100:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Verificación de pronóstico
        if pronostico_real:
            st.markdown("#### ✅ Verificación de Pronóstico")
            st.write(f"**Pronóstico Real:** {pronostico_real}")
            
            if acerto_toraxia is True:
                st.success(f"{verificacion_emoji} {verificacion_text}")
            elif acerto_toraxia is False:
                st.error(f"{verificacion_emoji} {verificacion_text}")
        
        # Comentarios
        if analysis.get('comentario_sospecha'):
            st.markdown("#### 💬 Sospecha Diagnóstica")
            st.info(analysis['comentario_sospecha'])
        
        st.markdown("---")
        
        # Top 5 predicciones
        if analysis.get('predictions_json'):
            st.markdown("#### 📊 Top 5 Predicciones")
            
            predictions_dict = analysis['predictions_json']
            
            # Ordenar por probabilidad
            sorted_predictions = sorted(
                predictions_dict.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            for rank, (pathology_en, prob) in enumerate(sorted_predictions, 1):
                pathology_es = translate_pathology(pathology_en)
                emoji = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][rank-1]
                
                st.markdown(f"""
                <div style="background-color: #f0f2f6; padding: 0.5rem 1rem; border-radius: 5px; margin-bottom: 0.3rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <span style="font-size: 1.2rem; margin-right: 0.5rem;">{emoji}</span>
                            <span style="font-weight: bold;">{pathology_es}</span>
                            <span style="color: #666; font-size: 0.85rem;"> ({pathology_en})</span>
                        </div>
                        <div style="font-size: 1.1rem; font-weight: bold; color: #1f77b4;">{prob*100:.1f}%</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Acciones
        col1, col2 = st.columns(2)
        
        with col1:
            # Generar y descargar PDF simple
            if st.button("📥 Descargar PDF", key=f"pdf_{index}"):
                st.info("🚧 La descarga de PDF con imágenes estará disponible próximamente.")
                st.write("Por ahora puedes ver todos los detalles aquí en el historial.")
        
        with col2:
            # Eliminar con confirmación
            if f"confirm_delete_{index}" not in st.session_state:
                st.session_state[f"confirm_delete_{index}"] = False
            
            if not st.session_state[f"confirm_delete_{index}"]:
                if st.button("🗑️ Eliminar", key=f"delete_{index}"):
                    st.session_state[f"confirm_delete_{index}"] = True
                    st.rerun()
            else:
                st.warning("⚠️ ¿Estás seguro?")
                col_yes, col_no = st.columns(2)
                
                with col_yes:
                    if st.button("✅ Sí", key=f"confirm_yes_{index}"):
                        # Eliminar de la base de datos
                        success = delete_analysis(analysis.get('id'))
                        if success:
                            st.success("✅ Análisis eliminado")
                            st.session_state[f"confirm_delete_{index}"] = False
                            st.rerun()
                        else:
                            st.error("❌ Error al eliminar")
                
                with col_no:
                    if st.button("❌ No", key=f"confirm_no_{index}"):
                        st.session_state[f"confirm_delete_{index}"] = False
                        st.rerun()


def delete_analysis(analysis_id: str) -> bool:
    """Elimina un análisis de la base de datos"""
    try:
        from services.auth import get_supabase_client
        supabase = get_supabase_client()
        
        result = supabase.table('analyses').delete().eq('id', analysis_id).execute()
        return True
        
    except Exception as e:
        st.error(f"Error al eliminar: {str(e)}")
        return False

