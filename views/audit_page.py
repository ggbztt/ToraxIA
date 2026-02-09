"""
Audit Page - Página de Bitácora del Sistema
Muestra todos los eventos registrados con filtros y exportación
"""
import streamlit as st
from datetime import datetime, timedelta
from services.audit_logger import get_audit_logs, get_audit_logs_count
from utils.audit_export import export_audit_to_csv, export_audit_to_pdf
from services.database import get_all_users


def render_audit_page():
    """Renderiza la página de bitácora del sistema (solo admin)"""
    
    st.markdown("## 📜 Bitácora del Sistema")
    st.markdown("Registro completo de eventos y acciones de todos los usuarios")
    st.markdown("---")
    
    # Sección de filtros
    st.markdown("### 🔍 Filtros")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Filtro por usuario
        users = get_all_users()
        user_options = [{"label": "Todos los usuarios", "value": None}]
        user_options += [
            {"label": f"{u['nombre']} {u['apellido']} ({u['email']})", "value": u['id']}
            for u in users
        ]
        
        selected_user_idx = st.selectbox(
            "👤 Usuario",
            range(len(user_options)),
            format_func=lambda i: user_options[i]["label"]
        )
        selected_user_id = user_options[selected_user_idx]["value"]
    
    with col2:
        # Filtro por fecha inicio
        start_date = st.date_input(
            "📅 Fecha Inicio",
            value=datetime.now() - timedelta(days=90),
            max_value=datetime.now()
        )
    
    with col3:
        # Filtro por fecha fin
        end_date = st.date_input(
            "📅 Fecha Fin",
            value=datetime.now() + timedelta(days=1),  # Incluir el día completo de hoy
            max_value=datetime.now() + timedelta(days=1)
        )
    
    with col4:
        # Filtro por tipo de evento
        event_types = {
            "Todos": None,
            "🔐 Autenticación": "auth",
            "👥 Gestión de Usuarios": "user_management",
            "📤 Análisis": "analysis",
            "📚 Definiciones": "definition",
            "⚙️ Sistema": "system"
        }
        
        selected_event_label = st.selectbox(
            "📂 Tipo de Evento",
            list(event_types.keys())
        )
        selected_event_type = event_types[selected_event_label]
    
    # Botones de acción
    col_filter, col_clear = st.columns([1, 1])
    
    with col_filter:
        if st.button("🔍 Aplicar Filtros", type="primary"):
            st.session_state.audit_filters_applied = True
    
    with col_clear:
        if st.button("🔄 Limpiar Filtros"):
            st.session_state.audit_filters_applied = False
            st.rerun()
    
    st.markdown("---")
    
    # Obtener logs con filtros
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    # Paginación
    items_per_page = 50
    if 'audit_page' not in st.session_state:
        st.session_state.audit_page = 0
    
    offset = st.session_state.audit_page * items_per_page
    
    logs = get_audit_logs(
        user_id=selected_user_id,
        start_date=start_datetime,
        end_date=end_datetime,
        event_type=selected_event_type,
        limit=items_per_page,
        offset=offset
    )
    
    # Contar total de logs
    total_logs = get_audit_logs_count(
        user_id=selected_user_id,
        start_date=start_datetime,
        end_date=end_datetime,
        event_type=selected_event_type
    )
    
    # Información de resultados
    st.markdown(f"**Mostrando {offset + 1}-{min(offset + len(logs), total_logs)} de {total_logs} eventos**")
    
    # Botones de exportación
    col_csv, col_pdf, col_space = st.columns([1, 1, 3])
    
    with col_csv:
        if st.button("📥 Exportar CSV", use_container_width=True):
            # Obtener TODOS los logs con los filtros aplicados (sin límite)
            all_logs = get_audit_logs(
                user_id=selected_user_id,
                start_date=start_datetime,
                end_date=end_datetime,
                event_type=selected_event_type,
                limit=10000  # Límite alto para exportar todo
            )
            
            csv_data = export_audit_to_csv(all_logs)
            if csv_data:
                st.download_button(
                    label="⬇️ Descargar CSV",
                    data=csv_data,
                    file_name=f"bitacora_toraxia_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    key="download_csv"
                )
            else:
                st.error("❌ Error al generar CSV")
    
    with col_pdf:
        if st.button("📄 Exportar PDF", use_container_width=True):
            # Obtener TODOS los logs con los filtros aplicados (sin límite)
            all_logs = get_audit_logs(
                user_id=selected_user_id,
                start_date=start_datetime,
                end_date=end_datetime,
                event_type=selected_event_type,
                limit=10000  # Límite alto para exportar todo
            )
            
            pdf_data = export_audit_to_pdf(all_logs)
            if pdf_data:
                st.download_button(
                    label="⬇️ Descargar PDF",
                    data=pdf_data,
                    file_name=f"bitacora_toraxia_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    key="download_pdf"
                )
            else:
                st.error("❌ Error al generar PDF")
    
    st.markdown("---")
    
    # Tabla de logs
    if len(logs) == 0:
        st.info("📭 No hay eventos que coincidan con los filtros seleccionados")
    else:
        # Mapas de traducción
        event_type_map = {
            'auth': '🔐 Autenticación',
            'user_management': '👥 Gestión Usuarios',
            'analysis': '📤 Análisis',
            'definition': '📚 Definiciones',
            'system': '⚙️ Sistema'
        }
        
        action_map = {
            'login': 'Inicio sesión',
            'logout': 'Cierre sesión',
            'login_failed': 'Login fallido',
            'register': 'Registro',
            'create_user': 'Crear usuario',
            'update_user': 'Actualizar usuario',
            'activate_user': 'Activar usuario',
            'deactivate_user': 'Desactivar usuario',
            'reset_password': 'Reset contraseña',
            'change_role': 'Cambiar rol',
            'create_analysis': 'Crear análisis',
            'view_analysis': 'Ver análisis',
            'delete_analysis': 'Eliminar análisis',
            'download_pdf': 'Descargar PDF',
            'update_definition': 'Actualizar definición',
            'create_definition': 'Crear definición',
            'error': 'Error',
            'model_load': 'Cargar modelo',
            'model_load_failed': 'Error cargar modelo'
        }
        
        # Mostrar logs en cards
        for log in logs:
            # Formatear timestamp
            try:
                ts = datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00'))
                formatted_ts = ts.strftime('%d/%m/%Y %H:%M:%S')
            except:
                formatted_ts = log.get('timestamp', 'N/A')
            
            # Obtener valores traducidos
            event_type = event_type_map.get(log.get('event_type', ''), log.get('event_type', 'N/A'))
            action = action_map.get(log.get('action', ''), log.get('action', 'N/A'))
            status = log.get('status', 'success')
            
            # Color según status
            if status == 'success':
                border_color = "#27ae60"  # Verde
                status_emoji = "✅"
            else:
                border_color = "#e74c3c"  # Rojo
                status_emoji = "❌"
            
            # Card HTML
            st.markdown(f"""
            <div style="background-color: #f0f2f6; padding: 1rem; border-radius: 8px; border-left: 4px solid {border_color}; margin-bottom: 0.5rem;">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div style="flex-grow: 1;">
                        <div style="font-size: 0.85rem; color: #666; margin-bottom: 0.25rem;">
                            <strong>📅 {formatted_ts}</strong>
                        </div>
                        <div style="font-size: 0.95rem; margin-bottom: 0.25rem;">
                            <strong>👤 {log.get('user_name', 'N/A')}</strong> <span style="color: #666;">({log.get('user_email', 'N/A')})</span>
                        </div>
                        <div style="font-size: 0.9rem; color: #444;">
                            {event_type} → <strong>{action}</strong>
                        </div>
                    </div>
                    <div style="font-size: 1.5rem; margin-left: 1rem;">
                        {status_emoji}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Paginación
        st.markdown("---")
        total_pages = (total_logs + items_per_page - 1) // items_per_page
        
        col_prev, col_info, col_next = st.columns([1, 2, 1])
        
        with col_prev:
            if st.button("⬅️ Anterior", disabled=st.session_state.audit_page == 0):
                st.session_state.audit_page -= 1
                st.rerun()
        
        with col_info:
            st.markdown(f"<div style='text-align: center;'>Página {st.session_state.audit_page + 1} de {total_pages}</div>", unsafe_allow_html=True)
        
        with col_next:
            if st.button("Siguiente ➡️", disabled=st.session_state.audit_page >= total_pages - 1):
                st.session_state.audit_page += 1
                st.rerun()
