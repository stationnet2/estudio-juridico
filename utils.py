from models import EstadoCaso

def evaluar_caso_automatico(cliente):
    """
    Evaluación automática inicial para filtrar casos
    Basado en criterios jurídicos reales
    """
    puntuacion = cliente.puntuacion_viabilidad
    
    # Casos APTOS (Alta Prioridad)
    if (cliente.hay_lesiones and puntuacion >= 7) or puntuacion >= 8:
        return EstadoCaso.APTO
    
    # Casos que requieren revisión humana
    elif (cliente.hay_danos_materiales or 
          cliente.tiene_seguro or 
          puntuacion >= 5):
        return EstadoCaso.EN_REVISION
    
    # Casos de baja viabilidad
    else:
        return EstadoCaso.DESCARTADO

def obtener_color_prioridad(prioridad):
    """Devuelve clase CSS según prioridad"""
    if prioridad >= 4:
        return "bg-danger"
    elif prioridad == 3:
        return "bg-warning"
    else:
        return "bg-info"

def obtener_badge_estado(estado):
    """Devuelve badge Bootstrap según estado"""
    colores = {
        EstadoCaso.NUEVO: "bg-primary",
        EstadoCaso.EN_REVISION: "bg-warning",
        EstadoCaso.APTO: "bg-success",
        EstadoCaso.DESCARTADO: "bg-secondary",
        EstadoCaso.CONTACTADO: "bg-info"
    }
    return colores.get(estado, "bg-secondary")