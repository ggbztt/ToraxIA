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

from services.auth import (
    is_authenticated, get_current_user, is_admin,
    logout_with_persistence, restore_session_from_cookie
)


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
    
    # RESTAURAR SESIÓN DESDE COOKIE (si existe)
    restore_session_from_cookie()
    
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
                st.session_state.model_config = config  # Incluye thresholds y gradcam_layer
                st.session_state.model_loaded = True
                
            except Exception as e:
                st.error(f"❌ Error cargando el modelo: {str(e)}")
                st.info("💡 Asegúrate de que `best_model.keras` esté en la carpeta `models/`")
                st.stop()
    
    # Obtener usuario actual
    user = get_current_user()
    user_role = user.get('role')
    
    # Sidebar - Navegación
    with st.sidebar:
        # Logo de ToraxIA
        st.image("toraxia_logo/toraxia-high-resolution-logo-transparent.png", use_container_width=True)
        st.markdown("---")
        
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
                ["🏠 Inicio", "📤 Nuevo Análisis", "📊 Mi Historial", "🔥 Actividad Reciente", "👥 Gestión de Usuarios", "📚 Definiciones", "📜 Bitácora"],
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
        if st.button("🚪 Cerrar Sesión", width="content"):
            logout_with_persistence()
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
    elif page == "📜 Bitácora":
        from views.audit_page import render_audit_page
        render_audit_page()


def render_home_page():
    """Página de inicio - Dashboard personalizado"""
    
    user = get_current_user()
    
    
    st.markdown(f'<div class="main-header">Bienvenido/a, {user["nombre"]}!</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Obtener estadísticas reales del usuario
    from services.database import get_user_analyses
    from datetime import datetime
    
    user_analyses = get_user_analyses(user['id'], limit=100)
    
    # Calcular estadísticas
    total_analyses = len(user_analyses)
    
    # Precisión promedio (solo de los que tienen verificación)
    verified_analyses = [a for a in user_analyses if a.get('acerto_toraxia') is not None]
    if verified_analyses:
        correct_count = len([a for a in verified_analyses if a.get('acerto_toraxia') == True])
        precision = (correct_count / len(verified_analyses)) * 100
        precision_text = f"{precision:.1f}%"
    else:
        precision_text = "N/A"
    
    # Último análisis
    if user_analyses:
        try:
            last_timestamp = user_analyses[0].get('timestamp', '')
            dt = datetime.fromisoformat(last_timestamp)
            last_analysis = dt.strftime("%d/%m/%Y")
        except:
            last_analysis = "Reciente"
    else:
        last_analysis = "Nunca"
    
    # Mostrar estadísticas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📊 Análisis Realizados", total_analyses, help="Total de análisis que has realizado")
    
    with col2:
        st.metric("🎯 Precisión Promedio", precision_text, help="% de aciertos cuando tu pronóstico coincide con la predicción Top 1 de ToraxIA. 0% = Ninguna coincidencia. N/A = Sin verificaciones.")
    
    with col3:
        st.metric("📅 Último Análisis", last_analysis, help="Fecha de tu último análisis")
    
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
        <strong>AUC Macro:</strong> 0.80<br>
        <strong>Interpretabilidad:</strong> Grad-CAM <br><br>
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
    
    # Filtro por área de estudio
    from services.database import get_recent_public_analyses
    from utils.translations import translate_pathology
    
    col_filter, col_refresh = st.columns([3, 1])
    
    with col_filter:
        area_filter = st.selectbox(
            "Filtrar por área de estudio:",
            ["Todas", "Medicina", "Enfermería", "Imagenología", "Otras"],
            key="activity_area_filter"
        )
    
    with col_refresh:
        st.markdown("<br>", unsafe_allow_html=True)  # Espaciador para alinear
        if st.button("🔄 Actualizar", width="content"):
            st.rerun()
    
    st.markdown("---")
    
    # Obtener análisis públicos
    analyses = get_recent_public_analyses(limit=20)
    
    if not analyses:
        st.info("📭 No hay análisis públicos disponibles todavía.")
        st.write("Los análisis se mostrarán aquí cuando los usuarios guarden sus resultados.")
        return
    
    # Filtrar por área si es necesario
    if area_filter != "Todas":
        analyses = [a for a in analyses if a.get('academico_area', '').lower() == area_filter.lower()]
    
    if not analyses:
        st.info(f"📭 No hay análisis del área '{area_filter}' disponibles.")
        return
    
    st.caption(f"Mostrando {len(analyses)} análisis")
    
    # Renderizar cards de actividad
    for i, analysis in enumerate(analyses):
        render_activity_card(analysis, i)


def render_activity_card(analysis: dict, index: int):
    """Renderiza una card de actividad (datos anonimizados)"""
    from utils.translations import translate_pathology
    from datetime import datetime
    
    # Datos básicos
    top_prediction = analysis.get('top_prediction', 'N/A')
    top_probability = analysis.get('top_probability', 0)
    timestamp = analysis.get('timestamp', '')
    academico_area = analysis.get('academico_area', 'N/A')
    acerto = analysis.get('acerto_toraxia')
    overlay_url = analysis.get('overlay_image_url')
    
    # Traducir patología
    pathology_es = translate_pathology(top_prediction)
    
    # Formatear fecha
    try:
        dt = datetime.fromisoformat(timestamp)
        time_ago = get_time_ago(dt)
    except:
        time_ago = "Hace un momento"
    
    # Color según probabilidad
    if top_probability >= 0.7:
        color = "#e74c3c"  # Rojo
    elif top_probability >= 0.4:
        color = "#f39c12"  # Naranja
    else:
        color = "#27ae60"  # Verde
    
    # Verificación emoji
    if acerto is True:
        verificacion = "✅ Verificado"
    elif acerto is False:
        verificacion = "❌ No coincidió"
    else:
        verificacion = "⏳ Pendiente"
    
    # Card HTML
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%); 
                padding: 1rem; border-radius: 12px; margin-bottom: 1rem;
                border-left: 4px solid {color}; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
            <div>
                <span style="font-size: 1.2rem; font-weight: bold; color: {color};">{pathology_es}</span>
                <span style="color: #666; font-size: 0.85rem;"> ({top_prediction})</span>
            </div>
            <span style="background: {color}; color: white; padding: 0.25rem 0.75rem; 
                         border-radius: 20px; font-weight: bold; font-size: 0.9rem;">
                {top_probability*100:.1f}%
            </span>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div style="color: #666; font-size: 0.85rem;">
                📚 {academico_area.capitalize()} • ⏰ {time_ago} • {verificacion}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Expander con más detalles
    with st.expander(f"🔍 Ver detalles", expanded=False):
        col1, col2 = st.columns([1, 2])
        
        with col1:
            if overlay_url:
                st.image(overlay_url, caption="Mapa de Activación", width="content")
            else:
                st.info("📷 Sin imagen")
        
        with col2:
            st.markdown("**Top 5 Predicciones:**")
            predictions_dict = analysis.get('predictions_json', {})
            if predictions_dict:
                sorted_preds = sorted(predictions_dict.items(), key=lambda x: x[1], reverse=True)[:5]
                for rank, (pathology, prob) in enumerate(sorted_preds, 1):
                    emoji = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][rank-1]
                    pathology_translated = translate_pathology(pathology)
                    st.write(f"{emoji} **{pathology_translated}**: {prob*100:.1f}%")


def get_time_ago(dt):
    """Calcula tiempo transcurrido en formato legible"""
    from datetime import datetime, timezone
    
    now = datetime.now()
    diff = now - dt.replace(tzinfo=None)
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "Hace un momento"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        return f"Hace {minutes} min"
    elif seconds < 86400:
        hours = int(seconds // 3600)
        return f"Hace {hours} h"
    elif seconds < 604800:
        days = int(seconds // 86400)
        return f"Hace {days} días"
    else:
        return dt.strftime("%d/%m/%Y")


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
    
    # Botón de contacto por Telegram
    telegram_url = "https://t.me/ggbztt?text=Hola,%20necesito%20ayuda%20con%20mi%20cuenta%20de%20ToraxIA"
    st.link_button("📱 Contactar por Telegram", telegram_url, width=True)



def render_admin_users_page():
    """Página de gestión de usuarios (solo admin)"""
    if not is_admin():
        st.error("❌ No tienes permisos para acceder a esta página")
        return
    
    st.markdown('<div class="main-header">👥 Gestión de Usuarios</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Administrar usuarios del sistema</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Obtener todos los usuarios
    from services.auth import get_supabase_client
    supabase = get_supabase_client()
    
    try:
        result = supabase.table('users').select('*').order('created_at', desc=True).execute()
        users = result.data if result.data else []
    except Exception as e:
        st.error(f"Error al cargar usuarios: {str(e)}")
        return
    
    # Estadísticas
    total_users = len(users)
    active_users = len([u for u in users if u.get('is_active', True)])
    admin_users = len([u for u in users if u.get('role') == 'admin'])
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("👥 Total Usuarios", total_users)
    with col2:
        st.metric("✅ Activos", active_users)
    with col3:
        st.metric("🔒 Administradores", admin_users)
    with col4:
        st.metric("🎓 Estudiantes", total_users - admin_users)
    
    st.markdown("---")
    
    # Filtros
    col_search, col_filter = st.columns([2, 1])
    with col_search:
        search_term = st.text_input("� Buscar por nombre, email o CI:", key="admin_search")
    with col_filter:
        status_filter = st.selectbox("Estado:", ["Todos", "Activos", "Inactivos"], key="admin_status_filter")
    
    # Filtrar usuarios
    filtered_users = users
    
    if search_term:
        search_lower = search_term.lower()
        filtered_users = [u for u in filtered_users if 
            search_lower in u.get('nombre', '').lower() or
            search_lower in u.get('apellido', '').lower() or
            search_lower in u.get('email', '').lower() or
            search_lower in u.get('ci', '').lower()
        ]
    
    if status_filter == "Activos":
        filtered_users = [u for u in filtered_users if u.get('is_active', True)]
    elif status_filter == "Inactivos":
        filtered_users = [u for u in filtered_users if not u.get('is_active', True)]
    
    st.caption(f"Mostrando {len(filtered_users)} de {total_users} usuarios")
    
    # Tabla de usuarios
    for i, user in enumerate(filtered_users):
        render_user_admin_card(user, i, supabase)


def render_user_admin_card(user: dict, index: int, supabase):
    """Renderiza una card de usuario para administración con edición completa"""
    from datetime import datetime
    from services.auth import hash_password
    import secrets
    import string
    
    user_id = user.get('id')
    nombre = user.get('nombre', 'N/A')
    apellido = user.get('apellido', '')
    email = user.get('email', 'N/A')
    ci = user.get('ci', 'N/A')
    role = user.get('role', 'estudiante')
    area = user.get('area_estudio', 'radiologia')
    is_active = user.get('is_active', True)
    last_login = user.get('last_login', 'Nunca')
    
    # Formatear última conexión
    if last_login and last_login != 'Nunca':
        try:
            dt = datetime.fromisoformat(last_login)
            last_login = dt.strftime("%d/%m/%Y %H:%M")
        except:
            pass
    
    # Colores según estado
    status_text = "✅ Activo" if is_active else "⚫ Inactivo"
    role_badge = "🔒 Admin" if role == 'admin' else "🎓 Estudiante"
    
    # Card
    with st.container():
        col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
        
        with col1:
            st.markdown(f"**{nombre} {apellido}**")
            st.caption(f"📧 {email} | 🆔 {ci}")
        
        with col2:
            st.caption(f"{role_badge} | 📚 {area.capitalize() if area else 'N/A'}")
            st.caption(f"🕐 Última conexión: {last_login}")
        
        current_user = get_current_user()
        is_self = user_id == current_user.get('id')
        
        with col3:
            # Botón editar
            if not is_self:
                if st.button("✏️ Editar", key=f"edit_{user_id}", type="secondary"):
                    st.session_state[f"editing_user_{user_id}"] = True
            else:
                st.caption("(Tú)")
        
        with col4:
            # Botón activar/desactivar
            if not is_self:
                if is_active:
                    if st.button("⚫", key=f"deactivate_{user_id}", help="Desactivar usuario"):
                        try:
                            supabase.table('users').update({'is_active': False}).eq('id', user_id).execute()
                            st.success(f"Usuario desactivado")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                else:
                    if st.button("✅", key=f"activate_{user_id}", help="Activar usuario"):
                        try:
                            supabase.table('users').update({'is_active': True}).eq('id', user_id).execute()
                            st.success(f"Usuario activado")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
        
        # Formulario de edición expandible
        if st.session_state.get(f"editing_user_{user_id}", False):
            with st.expander("📝 Editar Usuario", expanded=True):
                with st.form(key=f"edit_form_{user_id}"):
                    st.markdown(f"**Editando:** {nombre} {apellido}")
                    
                    # Campos editables
                    col_a, col_b = st.columns(2)
                    with col_a:
                        new_nombre = st.text_input("Nombre", value=nombre, key=f"name_{user_id}")
                        new_email = st.text_input("Email", value=email, key=f"email_{user_id}", 
                                                  help="⚠️ Cambiar email afecta el login del usuario")
                        new_role = st.selectbox("Rol", options=["estudiante", "admin"],
                                               index=0 if role == "estudiante" else 1,
                                               key=f"role_{user_id}")
                    
                    with col_b:
                        new_apellido = st.text_input("Apellido", value=apellido, key=f"apellido_{user_id}")
                        new_ci = st.text_input("Cédula", value=ci, key=f"ci_{user_id}")
                        new_area = st.selectbox("Área de Estudio", 
                                               options=["radiologia", "medicina", "enfermeria", "otro"],
                                               index=["radiologia", "medicina", "enfermeria", "otro"].index(area) if area in ["radiologia", "medicina", "enfermeria", "otro"] else 0,
                                               key=f"area_{user_id}")
                    
                    st.markdown("---")
                    
                    # Botones de acción
                    col_save, col_reset, col_cancel = st.columns(3)
                    
                    with col_save:
                        save_btn = st.form_submit_button("💾 Guardar Cambios", type="primary")
                    
                    with col_reset:
                        reset_btn = st.form_submit_button("🔑 Resetear Contraseña")
                    
                    with col_cancel:
                        cancel_btn = st.form_submit_button("❌ Cancelar")
                    
                    if save_btn:
                        # Validaciones
                        import re
                        
                        def validate_name(name):
                            if not name or len(name.strip()) < 2:
                                return False
                            pattern = r'^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s\-]+$'
                            return re.match(pattern, name.strip()) is not None
                            
                        def validate_email(email):
                            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                            return re.match(pattern, email) is not None
                            
                        def validate_ci(ci):
                            return ci.isdigit() and 7 <= len(ci) <= 8
                        
                        errors = []
                        if not validate_name(new_nombre):
                            errors.append("Nombre inválido (solo letras, sin números ni caracteres especiales)")
                        
                        if not validate_name(new_apellido):
                            errors.append("Apellido inválido (solo letras, sin números ni caracteres especiales)")
                        
                        if not validate_email(new_email):
                            errors.append("Email inválido (formato incorrecto)")
                            
                        if not validate_ci(new_ci):
                            errors.append("Cédula inválida (solo números, 7-8 dígitos)")
                            
                        if errors:
                            for error in errors:
                                st.error(f"❌ {error}")
                        else:
                            try:
                                # Actualizar datos
                                updates = {
                                    'nombre': new_nombre.strip(),
                                    'apellido': new_apellido.strip(),
                                    'email': new_email.strip(),
                                    'ci': new_ci.strip(),
                                    'area_estudio': new_area,
                                    'role': new_role
                                }
                                supabase.table('users').update(updates).eq('id', user_id).execute()
                                st.success(f"✅ Usuario actualizado correctamente")
                                del st.session_state[f"editing_user_{user_id}"]
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error al actualizar: {str(e)}")
                    
                    if reset_btn:
                        try:
                            # Generar contraseña temporal
                            temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(10))
                            password_hash = hash_password(temp_password)
                            
                            supabase.table('users').update({'password_hash': password_hash}).eq('id', user_id).execute()
                            
                            st.success(f"✅ Contraseña reseteada")
                            st.info(f"🔑 **Nueva contraseña temporal:** `{temp_password}`")
                            st.warning("⚠️ Comparte esta contraseña con el usuario de forma segura. Solo se muestra una vez.")
                        except Exception as e:
                            st.error(f"❌ Error al resetear contraseña: {str(e)}")
                    
                    if cancel_btn:
                        del st.session_state[f"editing_user_{user_id}"]
                        st.rerun()
        
        st.markdown("---")


def render_admin_definitions_page():
    """Página de gestión de definiciones técnicas (solo admin)"""
    if not is_admin():
        st.error("❌ No tienes permisos para acceder a esta página")
        return
    
    st.markdown('<div class="main-header">📚 Definiciones Técnicas</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Editar definiciones de patologías</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    from services.auth import get_supabase_client
    from utils.translations import translate_pathology
    
    supabase = get_supabase_client()
    
    # Lista de patologías
    pathologies = [
        "Atelectasis", "Cardiomegaly", "Effusion", "Infiltration", 
        "Mass", "Nodule", "Pneumonia", "Pneumothorax", 
        "Consolidation", "Edema", "Emphysema", "Fibrosis", 
        "Pleural_Thickening", "Hernia"
    ]
    
    # Obtener definiciones existentes
    try:
        result = supabase.table('pathology_definitions').select('*').execute()
        definitions = {d['pathology_name']: d for d in result.data} if result.data else {}
    except Exception as e:
        st.error(f"Error al cargar definiciones: {str(e)}")
        definitions = {}
    
    # Estadísticas
    defined_count = len(definitions)
    pending_count = len(pathologies) - defined_count
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("✅ Definidas", defined_count)
    with col2:
        st.metric("⏳ Pendientes", pending_count)
    
    st.markdown("---")
    
    # Selector de patología
    selected_pathology = st.selectbox(
        "Selecciona una patología para editar:",
        pathologies,
        format_func=lambda x: f"{translate_pathology(x)} ({x})" + (" ✅" if x in definitions else " ⚠️")
    )
    
    st.markdown("---")
    
    # Formulario de edición
    st.subheader(f"📝 {translate_pathology(selected_pathology)}")
    
    current_def = definitions.get(selected_pathology, {})
    
    with st.form(key=f"def_form_{selected_pathology}"):
        # Definición técnica
        technical_definition = st.text_area(
            "Definición técnica (se muestra en resultados):",
            value=current_def.get('technical_definition', ''),
            height=150,
            placeholder="Describe la patología de forma técnica pero comprensible..."
        )
        
        # Descripción extendida (opcional)
        extended_description = st.text_area(
            "Descripción extendida (opcional):",
            value=current_def.get('extended_description', ''),
            height=100,
            placeholder="Información adicional, síntomas, causas..."
        )
        
        # Referencias (opcional)
        references = st.text_input(
            "Referencias (URLs separadas por coma):",
            value=current_def.get('references', ''),
            placeholder="https://ejemplo.com, https://otro.com"
        )
        
        col_save, col_clear = st.columns(2)
        
        with col_save:
            submit = st.form_submit_button("💾 Guardar Definición", type="primary", width="content")
        
        with col_clear:
            clear = st.form_submit_button("🗑️ Limpiar", width="content")
        
        if submit and technical_definition.strip():
            try:
                # Preparar datos
                definition_data = {
                    'pathology_name': selected_pathology,
                    'technical_definition': technical_definition.strip(),
                    'extended_description': extended_description.strip() if extended_description else None,
                    'references': references.strip() if references else None
                }
                
                # Upsert (insertar o actualizar)
                if selected_pathology in definitions:
                    # Actualizar
                    supabase.table('pathology_definitions')\
                        .update(definition_data)\
                        .eq('pathology_name', selected_pathology)\
                        .execute()
                    st.success(f"✅ Definición de '{translate_pathology(selected_pathology)}' actualizada")
                else:
                    # Insertar
                    supabase.table('pathology_definitions')\
                        .insert(definition_data)\
                        .execute()
                    st.success(f"✅ Definición de '{translate_pathology(selected_pathology)}' creada")
                
                st.rerun()
                
            except Exception as e:
                st.error(f"Error al guardar: {str(e)}")
        
        elif submit:
            st.warning("⚠️ La definición técnica no puede estar vacía")
    
    # Vista previa
    if selected_pathology in definitions:
        st.markdown("---")
        st.subheader("👁️ Vista Previa")
        
        with st.container():
            st.markdown(f"""
            <div style="background: #f0f2f6; padding: 1rem; border-radius: 10px; border-left: 4px solid #1f77b4;">
                <h4 style="color: #1f77b4; margin-bottom: 0.5rem;">{translate_pathology(selected_pathology)}</h4>
                <p style="color: #333;">{definitions[selected_pathology].get('technical_definition', 'Sin definición')}</p>
            </div>
            """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
