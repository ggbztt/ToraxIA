"""
Página de Panel de Administración
Gestiona usuarios y definiciones técnicas
"""
# import streamlit as st
# from services.auth import is_admin, get_supabase_client, hash_password, get_current_user
# from utils.translations import translate_pathology
# from datetime import datetime
# import secrets
# import string
# import re

# def validate_name(name):
#     """Valida que el nombre solo contenga letras, espacios y acentos"""
#     if not name or len(name.strip()) < 2:
#         return False
#     pattern = r'^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s\-]+$'
#     return re.match(pattern, name.strip()) is not None

# def render_admin_users_page():
#     """Página de gestión de usuarios (solo admin)"""
#     if not is_admin():
#         st.error("❌ No tienes permisos para acceder a esta página")
#         return
    
#     st.markdown('<div class="main-header">👥 Gestión de Usuarios</div>', unsafe_allow_html=True)
#     st.markdown('<div class="sub-header">Administrar usuarios del sistema</div>', unsafe_allow_html=True)
    
#     st.markdown("---")
    
#     # Obtener todos los usuarios
#     supabase = get_supabase_client()
    
#     try:
#         result = supabase.table('users').select('*').order('created_at', desc=True).execute()
#         users = result.data if result.data else []
#     except Exception as e:
#         st.error(f"Error al cargar usuarios: {str(e)}")
#         return
    
#     # Estadísticas
#     total_users = len(users)
#     active_users = len([u for u in users if u.get('is_active', True)])
#     admin_users = len([u for u in users if u.get('role') == 'admin'])
    
#     col1, col2, col3, col4 = st.columns(4)
#     with col1:
#         st.metric("👥 Total Usuarios", total_users)
#     with col2:
#         st.metric("✅ Activos", active_users)
#     with col3:
#         st.metric("🔒 Administradores", admin_users)
#     with col4:
#         st.metric("🎓 Estudiantes", total_users - admin_users)
    
#     st.markdown("---")
    
#     # Filtros
#     col_search, col_filter = st.columns([2, 1])
#     with col_search:
#         search_term = st.text_input("🔍 Buscar por nombre, email o CI:", key="admin_search")
#     with col_filter:
#         status_filter = st.selectbox("Estado:", ["Todos", "Activos", "Inactivos"], key="admin_status_filter")
    
#     # Filtrar usuarios
#     filtered_users = users
    
#     if search_term:
#         search_lower = search_term.lower()
#         filtered_users = [u for u in filtered_users if 
#             search_lower in u.get('nombre', '').lower() or
#             search_lower in u.get('apellido', '').lower() or
#             search_lower in u.get('email', '').lower() or
#             search_lower in u.get('ci', '').lower()
#         ]
    
#     if status_filter == "Activos":
#         filtered_users = [u for u in filtered_users if u.get('is_active', True)]
#     elif status_filter == "Inactivos":
#         filtered_users = [u for u in filtered_users if not u.get('is_active', True)]
    
#     st.caption(f"Mostrando {len(filtered_users)} de {total_users} usuarios")
    
#     # Tabla de usuarios
#     for i, user in enumerate(filtered_users):
#         render_user_admin_card(user, i, supabase)


# def render_user_admin_card(user: dict, index: int, supabase):
#     """Renderiza una card de usuario para administración con edición completa"""
    
#     user_id = user.get('id')
#     nombre = user.get('nombre', 'N/A')
#     apellido = user.get('apellido', '')
#     email = user.get('email', 'N/A')
#     ci = user.get('ci', 'N/A')
#     role = user.get('role', 'estudiante')
#     area = user.get('area_estudio', 'radiologia')
#     is_active = user.get('is_active', True)
#     last_login = user.get('last_login', 'Nunca')
    
#     # Formatear última conexión
#     if last_login and last_login != 'Nunca':
#         try:
#             dt = datetime.fromisoformat(last_login)
#             last_login = dt.strftime("%d/%m/%Y %H:%M")
#         except:
#             pass
    
#     # Colores según estado
#     status_text = "✅ Activo" if is_active else "⚫ Inactivo"
#     role_badge = "🔒 Admin" if role == 'admin' else "🎓 Estudiante"
    
#     # Card
#     with st.container():
#         col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
        
#         with col1:
#             st.markdown(f"**{nombre} {apellido}**")
#             st.caption(f"📧 {email} | 🆔 {ci}")
        
#         with col2:
#             st.caption(f"{role_badge} | 📚 {area.capitalize() if area else 'N/A'}")
#             st.caption(f"🕐 Última conexión: {last_login}")
        
#         current_user = get_current_user()
#         is_self = user_id == current_user.get('id')
        
#         with col3:
#             # Botón editar
#             if not is_self:
#                 if st.button("✏️ Editar", key=f"edit_{user_id}", type="secondary"):
#                     st.session_state[f"editing_user_{user_id}"] = True
#             else:
#                 st.caption("(Tú)")
        
#         with col4:
#             # Botón activar/desactivar
#             if not is_self:
#                 if is_active:
#                     if st.button("⚫", key=f"deactivate_{user_id}", help="Desactivar usuario"):
#                         try:
#                             supabase.table('users').update({'is_active': False}).eq('id', user_id).execute()
#                             st.success(f"Usuario desactivado")
#                             st.rerun()
#                         except Exception as e:
#                             st.error(f"Error: {str(e)}")
#                 else:
#                     if st.button("✅", key=f"activate_{user_id}", help="Activar usuario"):
#                         try:
#                             supabase.table('users').update({'is_active': True}).eq('id', user_id).execute()
#                             st.success(f"Usuario activado")
#                             st.rerun()
#                         except Exception as e:
#                             st.error(f"Error: {str(e)}")
        
#         # Formulario de edición expandible
#         if st.session_state.get(f"editing_user_{user_id}", False):
#             with st.expander("📝 Editar Usuario", expanded=True):
#                 with st.form(key=f"edit_form_{user_id}"):
#                     st.markdown(f"**Editando:** {nombre} {apellido}")
                    
#                     # Campos editables
#                     col_a, col_b = st.columns(2)
#                     with col_a:
#                         new_nombre = st.text_input("Nombre", value=nombre, key=f"name_{user_id}")
#                         new_email = st.text_input("Email", value=email, key=f"email_{user_id}", 
#                                                   help="⚠️ Cambiar email afecta el login del usuario")
#                         new_role = st.selectbox("Rol", options=["estudiante", "admin"],
#                                                index=0 if role == "estudiante" else 1,
#                                                key=f"role_{user_id}")
                    
#                     with col_b:
#                         new_apellido = st.text_input("Apellido", value=apellido, key=f"apellido_{user_id}")
#                         new_ci = st.text_input("Cédula", value=ci, key=f"ci_{user_id}")
#                         new_area = st.selectbox("Área de Estudio", 
#                                                options=["radiologia", "medicina", "enfermeria", "otro"],
#                                                index=["radiologia", "medicina", "enfermeria", "otro"].index(area) if area in ["radiologia", "medicina", "enfermeria", "otro"] else 0,
#                                                key=f"area_{user_id}")
                    
#                     st.markdown("---")
                    
#                     # Botones de acción
#                     col_save, col_reset, col_cancel = st.columns(3)
                    
#                     with col_save:
#                         save_btn = st.form_submit_button("💾 Guardar Cambios", type="primary")
                    
#                     with col_reset:
#                         reset_btn = st.form_submit_button("🔑 Resetear Contraseña")
                    
#                     with col_cancel:
#                         cancel_btn = st.form_submit_button("❌ Cancelar")
                    
#                     if save_btn:
#                         # Validaciones
#                         import re
                        
#                         def validate_email(email):
#                             pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
#                             return re.match(pattern, email) is not None
                            
#                         def validate_ci(ci):
#                             return ci.isdigit() and 7 <= len(ci) <= 8
                        
#                         errors = []
#                         if not validate_name(new_nombre):
#                             errors.append("Nombre inválido (solo letras, sin números ni caracteres especiales)")
                        
#                         if not validate_name(new_apellido):
#                             errors.append("Apellido inválido (solo letras, sin números ni caracteres especiales)")
                            
#                         if not validate_email(new_email):
#                             errors.append("Email inválido (formato incorrecto)")
                            
#                         if not validate_ci(new_ci):
#                             errors.append("Cédula inválida (solo números, 7-8 dígitos)")
                            
#                         if errors:
#                             for error in errors:
#                                 st.error(f"❌ {error}")
#                         else:
#                             try:
#                                 # Actualizar datos
#                                 updates = {
#                                     'nombre': new_nombre.strip(),
#                                     'apellido': new_apellido.strip(),
#                                     'email': new_email.strip(),
#                                     'ci': new_ci.strip(),
#                                     'area_estudio': new_area,
#                                     'role': new_role
#                                 }
#                                 supabase.table('users').update(updates).eq('id', user_id).execute()
#                                 st.success(f"✅ Usuario actualizado correctamente")
#                                 del st.session_state[f"editing_user_{user_id}"]
#                                 st.rerun()
#                             except Exception as e:
#                                 st.error(f"❌ Error al actualizar: {str(e)}")
                    
#                     if reset_btn:
#                         try:
#                             # Generar contraseña temporal
#                             temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(10))
#                             password_hash = hash_password(temp_password)
                            
#                             supabase.table('users').update({'password_hash': password_hash}).eq('id', user_id).execute()
                            
#                             st.success(f"✅ Contraseña reseteada")
#                             st.info(f"🔑 **Nueva contraseña temporal:** `{temp_password}`")
#                             st.warning("⚠️ Comparte esta contraseña con el usuario de forma segura. Solo se muestra una vez.")
#                         except Exception as e:
#                             st.error(f"❌ Error al resetear contraseña: {str(e)}")
                    
#                     if cancel_btn:
#                         del st.session_state[f"editing_user_{user_id}"]
#                         st.rerun()
        
#         st.markdown("---")


# def render_admin_definitions_page():
#     """Página de gestión de definiciones técnicas (solo admin)"""
#     if not is_admin():
#         st.error("❌ No tienes permisos para acceder a esta página")
#         return
    
#     st.markdown('<div class="main-header">📚 Definiciones Técnicas</div>', unsafe_allow_html=True)
#     st.markdown('<div class="sub-header">Editar definiciones de patologías</div>', unsafe_allow_html=True)
    
#     st.markdown("---")
    
#     supabase = get_supabase_client()
    
#     # Lista de patologías
#     pathologies = [
#         "Atelectasis", "Cardiomegaly", "Effusion", "Infiltration", 
#         "Mass", "Nodule", "Pneumonia", "Pneumothorax", 
#         "Consolidation", "Edema", "Emphysema", "Fibrosis", 
#         "Pleural_Thickening", "Hernia"
#     ]
    
#     # Obtener definiciones existentes
#     try:
#         result = supabase.table('pathology_definitions').select('*').execute()
#         definitions = {d['pathology_name']: d for d in result.data} if result.data else {}
#     except Exception as e:
#         st.error(f"Error al cargar definiciones: {str(e)}")
#         definitions = {}
    
#     # Estadísticas
#     defined_count = len(definitions)
#     pending_count = len(pathologies) - defined_count
    
#     col1, col2 = st.columns(2)
#     with col1:
#         st.metric("✅ Definidas", defined_count)
#     with col2:
#         st.metric("⏳ Pendientes", pending_count)
    
#     st.markdown("---")
    
#     # Selector de patología
#     selected_pathology = st.selectbox(
#         "Selecciona una patología para editar:",
#         pathologies,
#         format_func=lambda x: f"{translate_pathology(x)} ({x})" + (" ✅" if x in definitions else " ⚠️")
#     )
    
#     st.markdown("---")
    
#     # Formulario de edición
#     st.subheader(f"📝 {translate_pathology(selected_pathology)}")
    
#     current_def = definitions.get(selected_pathology, {})
    
#     with st.form(key=f"def_form_{selected_pathology}"):
#         # Definición técnica
#         technical_definition = st.text_area(
#             "Definición técnica (se muestra en resultados):",
#             value=current_def.get('technical_definition', ''),
#             height=150,
#             placeholder="Describe la patología de forma técnica pero comprensible..."
#         )
        
#         # Descripción extendida (opcional)
#         extended_description = st.text_area(
#             "Descripción extendida (opcional):",
#             value=current_def.get('extended_description', ''),
#             height=100,
#             placeholder="Información adicional, síntomas, causas..."
#         )
        
#         # Referencias (opcional)
#         references = st.text_input(
#             "Referencias (URLs separadas por coma):",
#             value=current_def.get('references', ''),
#             placeholder="https://ejemplo.com, https://otro.com"
#         )
        
#         col_save, col_clear = st.columns(2)
        
#         with col_save:
#             submit = st.form_submit_button("💾 Guardar Definición", type="primary", width="content")
        
#         with col_clear:
#             clear = st.form_submit_button("🗑️ Limpiar", width="content")
        
#         if submit and technical_definition.strip():
#             try:
#                 # Preparar datos
#                 definition_data = {
#                     'pathology_name': selected_pathology,
#                     'technical_definition': technical_definition.strip(),
#                     'extended_description': extended_description.strip() if extended_description else None,
#                     'references': references.strip() if references else None
#                 }
                
#                 # Upsert (insertar o actualizar)
#                 if selected_pathology in definitions:
#                     # Actualizar
#                     supabase.table('pathology_definitions')\
#                         .update(definition_data)\
#                         .eq('pathology_name', selected_pathology)\
#                         .execute()
#                     st.success(f"✅ Definición de '{translate_pathology(selected_pathology)}' actualizada")
#                 else:
#                     # Insertar
#                     supabase.table('pathology_definitions')\
#                         .insert(definition_data)\
#                         .execute()
#                     st.success(f"✅ Definición de '{translate_pathology(selected_pathology)}' creada")
                
#                 st.rerun()
                
#             except Exception as e:
#                 st.error(f"Error al guardar: {str(e)}")
        
#         elif submit:
#             st.warning("⚠️ La definición técnica no puede estar vacía")
