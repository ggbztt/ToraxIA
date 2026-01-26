"""
Utilidades para traducción de nombres de patologías
"""

# Diccionario de traducción Inglés -> Español
PATHOLOGY_TRANSLATIONS = {
    'Atelectasis': 'Atelectasia',
    'Cardiomegaly': 'Cardiomegalia',
    'Effusion': 'Derrame Pleural',
    'Infiltration': 'Infiltración',
    'Mass': 'Masa',
    'Nodule': 'Nódulo',
    'Pneumonia': 'Neumonía',
    'Pneumothorax': 'Neumotórax',
    'Consolidation': 'Consolidación',
    'Edema': 'Edema',
    'Emphysema': 'Enfisema',
    'Fibrosis': 'Fibrosis',
    'Pleural_Thickening': 'Engrosamiento Pleural',
    'Hernia': 'Hernia'
}

# Diccionario inverso Español -> Inglés (para búsquedas)
PATHOLOGY_TRANSLATIONS_REVERSE = {v: k for k, v in PATHOLOGY_TRANSLATIONS.items()}


def translate_pathology(pathology_name: str, to_spanish: bool = True) -> str:
    """
    Traduce el nombre de una patología entre inglés y español
    
    Args:
        pathology_name: Nombre de la patología
        to_spanish: Si True, traduce a español. Si False, traduce a inglés
    
    Returns:
        Nombre traducido, o el original si no se encuentra traducción
    """
    if to_spanish:
        return PATHOLOGY_TRANSLATIONS.get(pathology_name, pathology_name)
    else:
        return PATHOLOGY_TRANSLATIONS_REVERSE.get(pathology_name, pathology_name)


def get_all_pathologies_spanish() -> list:
    """Retorna lista de todas las patologías en español"""
    return list(PATHOLOGY_TRANSLATIONS.values())


def get_all_pathologies_english() -> list:
    """Retorna lista de todas las patologías en inglés"""
    return list(PATHOLOGY_TRANSLATIONS.keys())
