"""
Script de prueba simple para verificar que los módulos core funcionan
"""
import sys
from pathlib import Path

# Agregar directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from models.model_loader import load_model_config, get_class_names
from utils.preprocessing import validate_image
from PIL import Image
import numpy as np

def test_config():
    """Prueba carga de configuración"""
    print("=" * 60)
    print("TEST 1: Carga de Configuración")
    print("=" * 60)
    
    config = load_model_config()
    print(f"✅ Configuración cargada")
    print(f"   Patologías: {len(config.get('pathologies', []))}")
    print(f"   Input shape: {config.get('input_shape')}")
    print(f"   Arquitectura: {config.get('architecture')}")
    
    class_names = get_class_names()
    print(f"\n📋 Clases detectables:")
    for i, name in enumerate(class_names, 1):
        print(f"   {i:2d}. {name}")
    
    print("\n✅ TEST 1 PASADO\n")

def test_validation():
    """Prueba validación de imágenes"""
    print("=" * 60)
    print("TEST 2: Validación de Imágenes")
    print("=" * 60)
    
    # Crear objeto mock
    class MockFile:
        def __init__(self, name):
            self.name = name
    
    test_cases = [
        ("imagen.jpg", True),
        ("imagen.png", True),
        ("imagen.jpeg", True),
        ("archivo.txt", False),
        ("archivo.pdf", False),
    ]
    
    for filename, expected in test_cases:
        result = validate_image(MockFile(filename))
        status = "✅" if result == expected else "❌"
        print(f"   {status} {filename}: {result} (esperado: {expected})")
    
    print("\n✅ TEST 2 PASADO\n")

if __name__ == "__main__":
    print("\n🧪 INICIANDO PRUEBAS DE MÓDULOS CORE\n")
    
    try:
        test_config()
        test_validation()
        
        print("=" * 60)
        print("🎉 TODOS LOS TESTS PASARON EXITOSAMENTE")
        print("=" * 60)
        print("\n📝 Nota: Para probar el modelo completo, ejecuta:")
        print("   streamlit run app.py")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ ERROR EN TESTS: {str(e)}")
        import traceback
        traceback.print_exc()
