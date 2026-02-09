"""
Página de Login y Registro
"""
import streamlit as st
from services.auth import register_user, login_with_persistence
import re


def validate_email(email: str) -> bool:
    """Valida formato de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_ci(ci: str) -> bool:
    """Valida formato de cédula (solo números, 7-8 dígitos)"""
    return ci.isdigit() and 7 <= len(ci) <= 8


def validate_name(name: str) -> bool:
    """
    Valida que el nombre solo contenga letras, espacios y acentos.
    No permite números ni caracteres especiales como !@#$%
    """
    if not name or len(name.strip()) < 2:
        return False
    # Permite letras (incluyendo acentos), espacios y guiones
    pattern = r'^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s\-]+$'
    return re.match(pattern, name.strip()) is not None


def render_login_page():
    """Renderiza la página de login/registro"""
    
    # Logo centrado
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("toraxia_logo/toraxia-high-resolution-logo-transparent.png", use_container_width=True)
    
    st.markdown('<div class="sub-header">Sistema de Diagnóstico Asistido por IA</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Tabs para Login y Registro
    tab1, tab2 = st.tabs(["🔐 Iniciar Sesión", "📝 Registrarse"])
    
    # ============================================
    # TAB 1: LOGIN
    # ============================================
    with tab1:
        st.markdown("### Iniciar Sesión")
        
        with st.form("login_form"):
            email = st.text_input("📧 Email", placeholder="tu@email.com")
            password = st.text_input("🔒 Contraseña", type="password")
            
            submit = st.form_submit_button("Iniciar Sesión", type="primary", use_container_width=True)
            
            if submit:
                if not email or not password:
                    st.error("❌ Por favor completa todos los campos")
                elif not validate_email(email):
                    st.error("❌ Email inválido")
                else:
                    with st.spinner("🔄 Verificando credenciales..."):
                        # Usar login_with_persistence para guardar cookie
                        success, user, message = login_with_persistence(email, password)
                        
                        if success:
                            st.success(f"✅ {message}")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
    
    # ============================================
    # TAB 2: REGISTRO
    # ============================================
    with tab2:
        st.markdown("### Crear Cuenta Nueva")
        
        with st.form("register_form"):
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("👤 Nombre", placeholder="Juan")
            with col2:
                apellido = st.text_input("👤 Apellido", placeholder="Pérez")
            
            # Fila 2: Email y Cédula
            col1, col2 = st.columns(2)
            with col1:
                email = st.text_input("📧 Email", placeholder="tu@email.com")
            with col2:
                ci = st.text_input("🆔 Cédula de Identidad", placeholder="12345678")
            
            # Fila 3: Contraseñas
            col1, col2 = st.columns(2)
            with col1:
                password = st.text_input("🔒 Contraseña", type="password", help="Mínimo 8 caracteres")
            with col2:
                password_confirm = st.text_input("🔒 Confirmar Contraseña", type="password")
            
            # Área de estudio
            area_estudio = st.selectbox(
                "🎓 Área de Estudio",
                options=["radiologia", "medicina", "enfermeria", "otro"],
                format_func=lambda x: {
                    "radiologia": "Radiología",
                    "medicina": "Medicina",
                    "enfermeria": "Enfermería",
                    "otro": "Otro"
                }[x]
            )
            
            st.markdown("---")
            
            submit = st.form_submit_button("Registrarse", type="primary", use_container_width=True)
            
            if submit:
                # Validaciones
                errors = []
                
                if not all([nombre, apellido, email, password, password_confirm, ci]):
                    errors.append("Por favor completa todos los campos")
                
                if not validate_name(nombre):
                    errors.append("Nombre inválido (solo letras, sin números ni caracteres especiales)")
                
                if not validate_name(apellido):
                    errors.append("Apellido inválido (solo letras, sin números ni caracteres especiales)")
                
                if not validate_email(email):
                    errors.append("Email inválido")
                
                if not validate_ci(ci):
                    errors.append("Cédula inválida (debe contener solo números, 7-8 dígitos)")
                
                if len(password) < 8:
                    errors.append("La contraseña debe tener al menos 8 caracteres")
                
                if password != password_confirm:
                    errors.append("Las contraseñas no coinciden")
                
                if errors:
                    for error in errors:
                        st.error(f"❌ {error}")
                else:
                    with st.spinner("🔄 Creando cuenta..."):
                        success, message = register_user(
                            email=email,
                            password=password,
                            nombre=nombre,
                            apellido=apellido,
                            ci=ci,
                            area_estudio=area_estudio,
                            role="estudiante"
                        )
                        
                        if success:
                            st.success(f"✅ {message}")
                            st.info("👉 Ahora puedes iniciar sesión en la pestaña 'Iniciar Sesión'")
                            st.balloons()
                        else:
                            st.error(f"❌ {message}")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
        <p>ToraxIA v2.0 - Sistema de Diagnóstico Asistido por IA</p>
        <p>Desarrollado para uso académico</p>
    </div>
    """, unsafe_allow_html=True)
