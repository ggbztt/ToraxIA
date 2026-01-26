"""
Script de prueba para verificar la conexión con Supabase
"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Cargar variables de entorno
load_dotenv()

def test_connection():
    """Prueba la conexión con Supabase"""
    
    print("🔄 Probando conexión con Supabase...\n")
    
    # Obtener credenciales
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    
    if not url or not key:
        print("❌ Error: No se encontraron las variables de entorno")
        print("   Asegúrate de tener un archivo .env con:")
        print("   - SUPABASE_URL")
        print("   - SUPABASE_ANON_KEY")
        return False
    
    try:
        # Crear cliente
        supabase: Client = create_client(url, key)
        print("✅ Cliente de Supabase creado correctamente")
        
        # Probar consulta a pathology_definitions
        print("\n🔍 Probando consulta a pathology_definitions...")
        response = supabase.table('pathology_definitions').select('*').limit(3).execute()
        
        if response.data:
            print(f"✅ Consulta exitosa. Se encontraron {len(response.data)} definiciones:")
            for item in response.data:
                print(f"   - {item['pathology_name']}")
        else:
            print("⚠️  La tabla está vacía o no se pudo consultar")
        
        # Probar consulta a users (debería estar vacía)
        print("\n🔍 Probando consulta a users...")
        response = supabase.table('users').select('count').execute()
        print(f"✅ Tabla 'users' accesible (usuarios registrados: {len(response.data)})")
        
        # Probar consulta a analyses (debería estar vacía)
        print("\n🔍 Probando consulta a analyses...")
        response = supabase.table('analyses').select('count').execute()
        print(f"✅ Tabla 'analyses' accesible (análisis registrados: {len(response.data)})")
        
        print("\n" + "="*50)
        print("✅ ¡Todas las pruebas pasaron exitosamente!")
        print("="*50)
        return True
        
    except Exception as e:
        print(f"\n❌ Error durante la prueba: {str(e)}")
        return False

if __name__ == "__main__":
    test_connection()
