"""
Mapeos manuales para normalización de EAPB/Aseguradoras
Basado en análisis de duplicados realizado el 2025
Desarrollado para Dashboard de Vacunación - Fiebre Amarilla del Tolima
"""

# Mapeos principales basados en análisis de similitud
EAPB_MAPPING = {
    # Grupo 1: LA NUEVA EPS (163,084 registros)
    "LA NUEVA EPS S.A.-CM": "LA NUEVA EPS S.A.",
    # Grupo 2: SALUD TOTAL (67,577 registros)
    "SALUD TOTAL S.A. E.P.S. CM": "SALUD TOTAL S.A. E.P.S.",
    "SALUD TOTAL EPS-S S.A. Contributivo": "SALUD TOTAL S.A. E.P.S.",
    "SALUD TOTAL ENTIDAD PROMOTORA DE SALUD DEL REGIMEN CONTRIBUTIVO Y DEL REGIMEN SUBSIDIADO S.A. -CM": "SALUD TOTAL S.A. E.P.S.",
    # Grupo 3: PIJAOS SALUD EPSI (26,005 registros)
    "PIJAOS SALUD EPSI -CM": "PIJAOS SALUD EPSI",
    # Grupo 4: MEDIMAS EPS (29,385 registros)
    "MEDIMÁS EPS S.A.S. -CM": "MEDIMAS EPS S.A.S",
    # Grupo 5: COMPARTA (14,987 registros)
    "COOPERATIVA DE SALUD COMUNITARIA-COMPARTA-CM": "COMPARTA - COOPERATIVA DE SALUD COMUNITARIA COMPARTA EPS S",
    # Grupo 6: SALUDVIDA (1,550 registros)
    "SALUDVIDA S.A. EPS": "SALUDVIDA S.A. EPS -CM",
    "SALUDVIDA S.A .E.P.S -CM": "SALUDVIDA S.A. EPS -CM",
    # Grupo 7: EMPRESA MUTUAL EMDISALUD (1,286 registros)
    "EMPRESA MUTUAL PARA EL DESARROLLO INTEGRAL  DE LA SALUD E.S.S. EMDISALUD ESS-CM": "Empresa Mutual para el Desarrollo Integral de la salud E.S.S.",
    # Grupo 8: COMFAMILIAR HUILA (263 registros)
    "CAJA DE COMPENSACIÓN FAMILIAR DEL HUILA - COMFAMILIAR HUILA CM": "CAJA DE COMPENSACIÓN FAMILIAR DEL HUILA - COMFAMILIAR HUILA",
    # Grupo 9: FUERZAS MILITARES (218 registros)
    "Fuerzas Militares RES": "Fuerzas Militares",
    # Grupo 10: SAVIA SALUD (214 registros)
    "SAVIA SALUD E.P.S. -CM": "SAVIA SALUD E.P.S.",
    # Grupo 11: CAJACOPI ATLANTICO (197 registros)
    "CAJA DE COMPENSACION FAMILIAR CAJACOPI ATLANTICO -CM": "CAJA DE COMPENSACION FAMILIAR CAJACOPI ATLANTICO",
    # Grupo 12: ASOCIACION MUTUAL SER (171 registros)
    "ASOCIACION MUTUAL SER EPS Subsidiado": "ASOCIACION MUTUAL SER EPS-S",
    # Grupo 13: ASOCIACION INDIGENA DEL CAUCA (130 registros)
    "Asociación Indígena Del Cauca": "Asociación Indígena del Cauca ",
    # Grupo 14: ALIANSALUD (144 registros)
    "ALIANSALUD EPS": "ALIANSALUD EPS - CM",
    # Grupo 15: HUMANA VIVIR (119 registros)
    "HUMANA VIVIR SA EPS": "Humana Vivir",
    # Grupo 16: CAPRESOCA (38 registros)
    "Capresoca E.P.S.-CM": "Capresoca E.P.S.",
    # Grupo 17: COOSALUD (41 registros)
    "COOSALUD EPS S.A. Contributivo": "COOSALUD EPS S.A.Contributivo",
    # Grupo 18: UNIVERSIDAD NACIONAL (20 registros)
    "UNIVERSIDAD NACIONAL DE COLOMBIA": "UNIVERSIDAD NACIONAL DE COLOMBIA -UNISALUD",
    # Grupo 19: COMFACHOCO (14 registros)
    "CAJA DE COMPENSACIÓN FAMILIAR DEL CHOCÓ - COMFACHOCO -CM": "CAJA DE COMPENSACIÓN FAMILIAR DEL CHOCÓ - COMFACHOCO",
    # Grupo 20: DUSAKAWI (20 registros)
    "ASOCIACIÓN DE CABILDOS INDÍGENAS DEL CESAR Y GUAJIRA-DUSAKAWI A.R.S.I. -CM": "ASOCIACIÓN DE CABILDOS INDÍGENAS DEL CESAR Y GUAJIRA-DUSAKAWI A.R.S.I.",
    # Umbral 0.85 - Grupos adicionales
    # ASMET (46,415 registros)
    "ASOCIACIÓN MUTUAL LA ESPERANZA ASMET  SALUD-CM": "ASMET - ASOCIACIÓN MUTUAL LA ESPERANZA DE EL TAMBO ASMET ESS",
    # CAFESALUD (2,785 registros)
    "CAFESALUD EPSS SA": "Cafesalud",
    # POLICIA NACIONAL (507 registros)
    "POLICIA NACIONAL SANIDAD": "Policia Nacional",
    # CONVIDA (345 registros)
    "EPS CONVIDA -CM": "Convida",
    # EMSSANAR (339 registros)
    "Asociación Mutual SER Empresa Solidaria de Salud ESS-CM": "EMSSANAR - ASOCIACION MUTIAL EMPRESA SOLIDARIA DE SALUD EMSSANAR ESS",
    "ASOCIACIÓN MUTUAL EMPRESA SOLIDARIA DE SALUD DE NARIÑO E.S.S. EMSSANAR E.S.S.-CM": "EMSSANAR - ASOCIACION MUTIAL EMPRESA SOLIDARIA DE SALUD EMSSANAR ESS",
    # ASOCIACION MUTUAL SER - Expansión (175 registros)
    "ASOCIACION MUTUAL SER EPS Contributivo": "ASOCIACION MUTUAL SER EPS-S",
    # SERVICIO OCCIDENTAL (125 registros)
    "EPS SERVICIO OCCIDENTAL DE SALUD  S.A. - EPS S.O.S. S.A.-CM": "SERVICIO OCCIDENTAL DE SALUD SA SOS",
    # Umbral 0.75 - Grupos adicionales
    # ECOOPSOS (13,554 registros)
    "ENTIDAD COOPERATIVA SOL.DE SALUD DEL NORTE DE SOACHA ECOOPSOS-CM": "ECOOPSOS - ENTIDAD COOPERATIVA SOLIDADARIA DE SALUD ECOOPSOS ESS EPS-S",
    # COOMEVA (2,740 registros)
    "COOMEVA   E.P.S.  S.A.-CM": "COOMEVA EPS S A",
    # SALUDVIDA - Expansión (1,910 registros)
    "SALUDVIDA EPS SA": "SALUDVIDA S.A. EPS -CM",
    # FUERZAS ARMADAS - No unificar Ejército y Policía (mantener separados)
    # 'Policia Nacional': 'Ejército Nacional',  # COMENTADO - mantener separados
    # FERROCARRILES (96 registros)
    "FPS de Ferrocarriles Nacionales": "Fondo de Pasivo Social de Ferrocarriles Nacionales de Colombia",
    # CRUZ BLANCA (54 registros)
    "CRUZ BLANCA  EPS S.A.-CM": "Cruz Blanca",
}

# Mapeos adicionales identificados manualmente
ADDITIONAL_MAPPINGS = {
    # Agregar aquí mapeos adicionales que se identifiquen posteriormente
    # o correcciones específicas
}

# Combinar todos los mapeos
ALL_EAPB_MAPPINGS = {**EAPB_MAPPING, **ADDITIONAL_MAPPINGS}


def get_eapb_stats():
    """
    Retorna estadísticas sobre los mapeos definidos
    """
    return {
        "total_mappings": len(ALL_EAPB_MAPPINGS),
        "main_mappings": len(EAPB_MAPPING),
        "additional_mappings": len(ADDITIONAL_MAPPINGS),
        "affected_records_estimate": 340000,  # Estimado basado en análisis
        "unique_canonical_names": len(set(ALL_EAPB_MAPPINGS.values())),
    }


if __name__ == "__main__":
    stats = get_eapb_stats()
    print("📊 Estadísticas de Mapeos EAPB:")
    for key, value in stats.items():
        print(f"  - {key}: {value:,}".replace(",", "."))
