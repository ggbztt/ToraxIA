"""
Script para crear el primer usuario administrador
Ejecutar solo una vez al inicio del proyecto
"""
import os
import sys
from pathlib import Path

# Agregar directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from services.auth import register_user


def create_admin():
    """Crea el usuario administrador inicial"""
    
    print("=" * 50)
    print("CREAR USUARIO ADMINISTRADOR INICIAL")
    print("=" * 50)
    print()
    
    # Solicitar datos
    nombre = input("Nombre: ").strip()
    apellido = input("Apellido: ").strip()
    email = input("Email: ").strip()
    ci = input("Cédula: ").strip()
    password = input("Contraseña (mínimo 8 caracteres): ").strip()
    
    print()
    print("Creando administrador...")
    
    # Crear admin (sin área de estudio)
    success, message = register_user(
        email=email,
        password=password,
        nombre=nombre,
        apellido=apellido,
        ci=ci,
        area_estudio=None,  # Admin no tiene área de estudio
        role="admin"
    )
    
    print()
    if success:
        print("✅ " + message)
        print()
        print("Credenciales del administrador:")
        print(f"  Email: {email}")
        print(f"  Contraseña: {password}")
        print()
        print("⚠️  IMPORTANTE: Guarda estas credenciales en un lugar seguro")
    else:
        print("❌ " + message)
    
    print("=" * 50)


if __name__ == "__main__":
    create_admin()
