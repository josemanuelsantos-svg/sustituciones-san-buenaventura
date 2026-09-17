"""
Carga el cuadrante oficial de sustituciones y guardias de Primaria
a partir de la imagen proporcionada por el usuario.
"""

from typing import Dict, List, Tuple
from database import Database
from models import ScheduleItem, ActivityType

# Mapeo de nombres informales del cuadrante a los IDs oficiales del sistema
MAPA_DOCENTES = {
    "alvaro_p": "aort0",      # Álvaro Paris Ortega Bonilla
    "belen": "m851",          # Mª Belén Hernando Martín
    "pili_p": "mar1",         # María Pilar Pérez Fernández
    "ma_carmen": "m654",      # Mª Carmen Ibáñez Abad
    "pilar_f": "p740",        # Pilar Fuentes Saavedra
    "jose_a": "j414",         # Jose Antonio Utrillas Sánchez
    "bea": "bleo0",           # Beatriz de León Ruiz
    "jose_m": "jos7",         # José Manuel Santos Alejano
    "pedro_z": "ped4",        # Pedro Zapata Paredes
    "ruben_r": "r299",        # Rubén Recio Molina
    "lorena": "l681",         # Lorena Moreno Barrigas
    "isabel_h": "ihid0",      # Isabel Hidalgo Castañeda
}

# Cuadrante de guardias prioritarias por día (0=Lunes, 4=Viernes) y tramo
# Tramos: 1H (9:00), 2H (9:45), 3H (11:00), 4H (12:00 - rotulado 11:30 en cuadrante)
CUADRANTE_GUARDIAS: Dict[Tuple[int, str], List[str]] = {
    # LUNES (dia 0)
    (0, "1H"): ["aort0", "m851", "mar1"],   # Álvaro P, Belén, Pili P
    (0, "2H"): ["jos7", "m851", "m654"],    # José M, Belén, Mª Carmen
    (0, "3H"): ["bleo0", "ped4"],           # Bea, Pedro Z
    (0, "4H"): ["p740", "r299"],            # Pilar F, Rubén R.

    # MARTES (dia 1)
    (1, "1H"): ["m654", "p740"],            # Mª Carmen, Pilar F
    (1, "2H"): ["jos7", "m851"],            # José M, Belén
    (1, "3H"): ["l681", "m851"],            # Lorena, Belén
    (1, "4H"): ["jos7", "m851"],            # José M, Belén

    # MIÉRCOLES (dia 2)
    (2, "1H"): ["j414", "m851"],            # José A., Belén
    (2, "2H"): ["m654", "ped4"],            # Mª Carmen, Pedro Z
    (2, "3H"): ["jos7", "mar1"],            # José M, Pili P
    (2, "4H"): ["jos7", "r299"],            # José M, Rubén R.

    # JUEVES (dia 3)
    (3, "1H"): ["bleo0", "m654"],           # Bea, Mª Carmen
    (3, "2H"): ["m851", "r299"],            # Belén, Rubén R.
    (3, "3H"): ["ihid0", "jos7"],           # Isabel H, José M
    (3, "4H"): ["m851", "mar1"],            # Belén, Pili P

    # VIERNES (dia 4)
    (4, "1H"): ["jos7", "m851"],            # José M, Belén
    (4, "2H"): ["jos7", "m654"],            # José M, Mª Carmen
    (4, "3H"): ["bleo0", "jos7"],           # Bea, José M
    (4, "4H"): ["jos7", "r299"],            # José M, Rubén R.
}

def aplicar_cuadrante():
    db = Database()
    schedules = db.get_schedules()

    # Eliminar guardias previas para no duplicar si se ejecuta varias veces
    schedules_filtrados = [
        s for s in schedules 
        if s.tipo_actividad != ActivityType.GUARDIA_AULA and s.tipo_actividad != ActivityType.DISPONIBLE
    ]

    nuevas_guardias = 0
    # 1. Insertar las guardias de aula prioritarias de la tabla
    for (dia, slot_id), prof_list in CUADRANTE_GUARDIAS.items():
        for prof_id in prof_list:
            schedules_filtrados.append(ScheduleItem(
                profesor_id=prof_id,
                dia_semana=dia,
                periodo_id=slot_id,
                tipo_actividad=ActivityType.GUARDIA_AULA,
                aula="Guardia",
                materia="Guardia de Sustitución",
                descripcion="Docente asignado en cuadrante para sustituciones"
            ))
            nuevas_guardias += 1

    # 2. Configuración específica de Isabel Hidalgo:
    # "Isabel tiene todo el horario de apoyo, excepto las dos primeras del lunes que hace las relis de Javi en sexto."
    # Primero eliminamos TODAS las asignaciones previas de Isabel (tanto lectivas como guardias)
    schedules_filtrados = [
        s for s in schedules_filtrados 
        if s.profesor_id != "ihid0"
    ]
    
    # Lunes 1H y 2H: Religión 6º EP (hace las relis de Javi en sexto)
    schedules_filtrados.append(ScheduleItem(
        profesor_id="ihid0",
        dia_semana=0,
        periodo_id="1H",
        tipo_actividad=ActivityType.LECTIVA,
        aula="6ºEP-A",
        materia="Religión 6º EP (Relis Javi)",
        descripcion="Religión en 6º EP-A con Isabel"
    ))
    schedules_filtrados.append(ScheduleItem(
        profesor_id="ihid0",
        dia_semana=0,
        periodo_id="2H",
        tipo_actividad=ActivityType.LECTIVA,
        aula="6ºEP-C",
        materia="Religión 6º EP (Relis Javi)",
        descripcion="Religión en 6º EP-C con Isabel"
    ))

    # Jueves 3H: Está asignada explícitamente en el cuadrante como guardia
    schedules_filtrados.append(ScheduleItem(
        profesor_id="ihid0",
        dia_semana=3,
        periodo_id="3H",
        tipo_actividad=ActivityType.GUARDIA_AULA,
        aula="Guardia",
        materia="Guardia de Sustitución",
        descripcion="Docente asignado en cuadrante para sustituciones"
    ))

    # En el resto de horas de la semana, Isabel está en Horario de Apoyo (disponible para sustituir)
    todos_los_dias = [0, 1, 2, 3, 4]
    tramos_lectivos = ["1H", "2H", "3H", "4H"]

    apoyos_isabel = 0
    for dia in todos_los_dias:
        for slot_id in tramos_lectivos:
            # Si es Lunes 1H o 2H, o Jueves 3H, ya está asignada arriba
            if (dia == 0 and slot_id in ["1H", "2H"]) or (dia == 3 and slot_id == "3H"):
                continue
            schedules_filtrados.append(ScheduleItem(
                profesor_id="ihid0",
                dia_semana=dia,
                periodo_id=slot_id,
                tipo_actividad=ActivityType.DISPONIBLE,
                aula="Apoyo",
                materia="Horario de Apoyo",
                descripcion="Disponible para sustituciones (Horario de Apoyo)"
            ))
            apoyos_isabel += 1

    db.save_schedules(schedules_filtrados)

    print(f"✓ Cuadrante aplicado correctamente:")
    print(f"  - Guardias de sustitución añadidas: {nuevas_guardias}")
    print(f"  - Horas de apoyo de Isabel configuradas: {apoyos_isabel}")
    print(f"  - Total de registros de horario en sistema: {len(schedules_filtrados)}")

if __name__ == "__main__":
    aplicar_cuadrante()
