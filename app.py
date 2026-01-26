"""
ToraxIA - Sistema de Diagnóstico Asistido por IA
Aplicación principal Streamlit con autenticación
"""
import streamlit as st
from config import APP_TITLE, APP_ICON
import sys
from pathlib import Path

# Agregar directorio raíz al path para imports
sys.path.insert(0, str(Path(__file__).parent))

from services.auth import is_authenticated, get_current_user, logout_user, is_admin


def main():
    """Función principal de la aplicación"""
    
    # Configuración de página
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon=APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # CSS personalizado
    st.markdown("""
        <style>
        .main-header {
            font-size: 3rem;
            font-weight: bold;
            color: #1f77b4;
            text-align: center;
            margin-bottom: 0.5rem;
        }
        .sub-header {
            font-size: 1.2rem;
            color: #666;
            text-align: center;
            margin-bottom: 2rem;
        }
        .info-card {
            background-color: #f0f2f6;
            padding: 1.5rem;
            border-radius: 10px;
            border-left: 5px solid #1f77b4;
        }
        .stButton>button {
            width: 100%;
            background-color: #1f77b4;
            color: white;
            font-weight: bold;
            border-radius: 5px;
            padding: 0.5rem 1rem;
        }
        .stButton>button:hover {
            background-color: #1557a0;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # VERIFICAR AUTENTICACIÓN
    if not is_authenticated():
        # Mostrar página de login
        from views.login_page import render_login_page
        render_login_page()
        return
    
    # Usuario autenticado - Cargar modelo
    if 'model_loaded' not in st.session_state:
        with st.spinner("🔄 Inicializando modelo de IA... (solo la primera vez, ~10-20 segundos)"):
            try:
                from models.model_loader import load_chestxray_model, get_class_names
                model, config = load_chestxray_model()
                class_names = get_class_names()
                
                st.session_state.model = model
                st.session_state.class_names = class_names
                st.session_state.model_loaded = True
                
            except Exception as e:
                st.error(f"❌ Error cargando el modelo: {str(e)}")
                st.info("💡 Asegúrate de que `modelo_final.keras` esté en la carpeta `models/`")
                st.stop()
    
    # Obtener usuario actual
    user = get_current_user()
    user_role = user.get('role')
    
    # Sidebar - Navegación
    with st.sidebar:
        # Info del usuario
        st.markdown(f"### 👤 {user['nombre']} {user['apellido']}")
        st.caption(f"**Rol:** {user_role.capitalize()}")
        if user_role == 'estudiante':
            st.caption(f"**Área:** {user['area_estudio'].capitalize()}")
        
        st.markdown("---")
        
        # Navegación según rol
        if user_role == 'admin':
            page = st.radio(
                "**Navegación**",
                ["🏠 Inicio", "📤 Nuevo Análisis", "📊 Mi Historial", "🔥 Actividad Reciente", "👥 Gestión de Usuarios", "📚 Definiciones"],
                label_visibility="collapsed"
            )
        else:  # estudiante
            page = st.radio(
                "**Navegación**",
                ["🏠 Inicio", "📤 Nuevo Análisis", "📊 Mi Historial", "🔥 Actividad Reciente", "👤 Mi Perfil"],
                label_visibility="collapsed"
            )
        
        st.markdown("---")
        
        # Botón de logout
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            logout_user()
            st.rerun()
        
        st.markdown("---")
        st.caption("**ToraxIA v2.0**")
        st.caption("Sistema Web con IA")
    
    # Renderizar página seleccionada
    if page == "🏠 Inicio":
        render_home_page()
    elif page == "📤 Nuevo Análisis":
        render_analysis_page()
    elif page == "📊 Mi Historial":
        render_history_page()
    elif page == "🔥 Actividad Reciente":
        render_activity_feed()
    elif page == "👤 Mi Perfil":
        render_profile_page()
    elif page == "👥 Gestión de Usuarios":
        render_admin_users_page()
    elif page == "📚 Definiciones":
        render_admin_definitions_page()


def render_home_page():
    """Página de inicio - Dashboard personalizado"""
    
    user = get_current_user()
    
    st.markdown('<div class="main-header">🩻 ToraxIA</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-header">Bienvenido/a, {user["nombre"]}!</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Estadísticas del usuario (placeholder)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📊 Análisis Realizados", "0", help="Total de análisis que has realizado")
    
    with col2:
        st.metric("🎯 Precisión Promedio", "N/A", help="Precisión promedio de tus diagnósticos")
    
    with col3:
        st.metric("📅 Último Análisis", "Nunca", help="Fecha de tu último análisis")
    
    st.markdown("---")
    
    # Cards informativos
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🎯 Patologías Detectables")
        st.markdown("""
        <div class="info-card">
        El sistema puede identificar <strong>14 patologías</strong> pulmonares:
        <ul style="margin-top: 0.5rem; font-size: 0.9rem;">
            <li>Atelectasia</li>
            <li>Cardiomegalia</li>
            <li>Derrame Pleural</li>
            <li>Infiltración</li>
            <li>Masa</li>
            <li>Nódulo</li>
            <li>Neumonía</li>
            <li>Neumotórax</li>
            <li>Consolidación</li>
            <li>Edema</li>
            <li>Enfisema</li>
            <li>Fibrosis</li>
            <li>Engrosamiento Pleural</li>
            <li>Hernia</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### 🤖 Tecnología")
        st.markdown("""
        <div class="info-card">
        <strong>Modelo:</strong> DenseNet-121<br>
        <strong>Dataset:</strong> NIH ChestX-ray14<br>
        <strong>Imágenes de entrenamiento:</strong> 100,000<br>
        <strong>AUC Macro:</strong> 0.802<br>
        <strong>Interpretabilidad:</strong> Saliency Maps<br><br>
        El modelo utiliza mapas de activación por gradientes para visualizar las regiones de interés.
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("### ⚠️ Uso Responsable")
        st.markdown("""
        <div class="info-card">
        <strong style="color: #d32f2f;">IMPORTANTE:</strong><br><br>
        Esta herramienta es de <strong>apoyo educativo</strong> y <strong>NO sustituye</strong> el criterio médico profesional.<br><br>
        Los resultados deben ser interpretados por personal médico calificado.<br><br>
        No tomar decisiones clínicas basándose únicamente en este sistema.
        </div>
        """, unsafe_allow_html=True)


def render_analysis_page():
    """Página de nuevo análisis"""
    from views.analysis_page import render_analysis_page as render_page
    render_page()


def render_history_page():
    """Página de historial personal"""
    from views.history_page import render_history_page as render_page
    render_page()


def render_activity_feed():
    """Página de actividad reciente (últimos 20 análisis públicos)"""
    st.markdown('<div class="main-header">🔥 Actividad Reciente</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Últimos 20 análisis realizados por la comunidad</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.info("🚧 **En desarrollo**: Esta página mostrará los últimos 20 análisis públicos.")


def render_profile_page():
    """Página de perfil del usuario"""
    st.markdown('<div class="main-header">👤 Mi Perfil</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Información personal</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    user = get_current_user()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input("Nombre", value=user['nombre'], disabled=True)
        st.text_input("Email", value=user['email'], disabled=True)
        st.text_input("Área de Estudio", value=user['area_estudio'].capitalize(), disabled=True)
    
    with col2:
        st.text_input("Apellido", value=user['apellido'], disabled=True)
        st.text_input("Cédula", value=user['ci'], disabled=True)
        st.text_input("Rol", value=user['role'].capitalize(), disabled=True)
    
    st.info("💡 Para modificar tus datos, contacta al administrador")


def render_admin_users_page():
    """Página de gestión de usuarios (solo admin)"""
    if not is_admin():
        st.error("❌ No tienes permisos para acceder a esta página")
        return
    
    st.markdown('<div class="main-header">👥 Gestión de Usuarios</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Administrar usuarios del sistema</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.info("🚧 **En desarrollo**: Esta página permitirá gestionar usuarios.")


def render_admin_definitions_page():
    """Página de gestión de definiciones técnicas (solo admin)"""
    if not is_admin():
        st.error("❌ No tienes permisos para acceder a esta página")
        return
    
    st.markdown('<div class="main-header">📚 Definiciones Técnicas</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Editar definiciones de patologías</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.info("🚧 **En desarrollo**: Esta página permitirá editar las definiciones técnicas de las patologías.")


if __name__ == "__main__":
    main()
