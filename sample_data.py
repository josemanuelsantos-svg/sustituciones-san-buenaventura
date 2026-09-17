"""
Generador de datos de prueba realistas para el Sistema de Sustituciones Escolares.
Permite inicializar el sistema con profesores, tramos horarios y un horario semanal completo.
"""

from typing import List
from models import TimeSlot, Teacher, ScheduleItem, ActivityType
from database import Database

def generate_default_time_slots() -> List[TimeSlot]:
    return [
        TimeSlot(id="1H", nombre="1ª Hora", hora_inicio="08:00", hora_fin="08:55", es_recreo=False, orden=1),
        TimeSlot(id="2H", nombre="2ª Hora", hora_inicio="08:55", hora_fin="09:50", es_recreo=False, orden=2),
        TimeSlot(id="3H", nombre="3ª Hora", hora_inicio="09:50", hora_fin="10:45", es_recreo=False, orden=3),
        TimeSlot(id="REC", nombre="Recreo", hora_inicio="10:45", hora_fin="11:15", es_recreo=True, orden=4),
        TimeSlot(id="4H", nombre="4ª Hora", hora_inicio="11:15", hora_fin="12:10", es_recreo=False, orden=5),
        TimeSlot(id="5H", nombre="5ª Hora", hora_inicio="12:10", hora_fin="13:05", es_recreo=False, orden=6),
        TimeSlot(id="6H", nombre="6ª Hora", hora_inicio="13:05", hora_fin="14:00", es_recreo=False, orden=7),
    ]

def generate_default_teachers() -> List[Teacher]:
    return [
        Teacher(
            id="maria-lopez",
            nombre="María López Martín",
            telefono="+34611223344",
            email="maria.lopez@colegio.es",
            departamento="Matemáticas",
            etapa="Secundaria",
            activo=True,
            sustituciones_realizadas=1
        ),
        Teacher(
            id="carlos-ruiz",
            nombre="Carlos Ruiz Gómez",
            telefono="+34622334455",
            email="carlos.ruiz@colegio.es",
            departamento="Matemáticas",
            etapa="Secundaria",
            activo=True,
            sustituciones_realizadas=0
        ),
        Teacher(
            id="lucia-sanchez",
            nombre="Lucía Sánchez Fernández",
            telefono="+34633445566",
            email="lucia.sanchez@colegio.es",
            departamento="Lengua Castellana",
            etapa="Secundaria",
            activo=True,
            sustituciones_realizadas=2
        ),
        Teacher(
            id="javier-morales",
            nombre="Javier Morales Gil",
            telefono="+34644556677",
            email="javier.morales@colegio.es",
            departamento="Ciencias de la Naturaleza",
            etapa="Secundaria",
            activo=True,
            sustituciones_realizadas=0
        ),
        Teacher(
            id="elena-navarro",
            nombre="Elena Navarro Ortiz",
            telefono="+34655667788",
            email="elena.navarro@colegio.es",
            departamento="Inglés",
            etapa="Primaria",
            activo=True,
            sustituciones_realizadas=0
        ),
        Teacher(
            id="david-castro",
            nombre="David Castro Romero",
            telefono="+34666778899",
            email="david.castro@colegio.es",
            departamento="Educación Física",
            etapa="Secundaria",
            activo=True,
            sustituciones_realizadas=1
        ),
        Teacher(
            id="ana-gutierrez",
            nombre="Ana Gutiérrez Vargas",
            telefono="+34677889900",
            email="ana.gutierrez@colegio.es",
            departamento="Geografía e Historia",
            etapa="Secundaria",
            activo=True,
            sustituciones_realizadas=0
        ),
    ]

def generate_default_schedules() -> List[ScheduleItem]:
    """
    Genera un horario representativo de lunes a viernes:
    - Carlos Ruiz tiene GUARDIA_AULA el martes a 2ª hora y 3ª hora.
    - María López tiene clase lectiva el martes a 3ª hora en 2º ESO A.
    - Javier Morales tiene DISPONIBLE el martes a 3ª hora.
    - Lucía Sánchez tiene NO_DISPONIBLE (reunión dpto) el martes a 3ª hora.
    """
    schedules: List[ScheduleItem] = []
    
    slots = ["1H", "2H", "3H", "REC", "4H", "5H", "6H"]
    
    # 1. Carlos Ruiz (Matemáticas)
    # Martes (dia_semana=1): 1H Lectiva, 2H Guardia Aula, 3H Guardia Aula, 4H Lectiva, 5H Disponible
    schedules.append(ScheduleItem("carlos-ruiz", 1, "1H", ActivityType.LECTIVA, "Aula 101", "Matemáticas 1º ESO A"))
    schedules.append(ScheduleItem("carlos-ruiz", 1, "2H", ActivityType.GUARDIA_AULA, "Planta 1", "Guardia de Aula"))
    schedules.append(ScheduleItem("carlos-ruiz", 1, "3H", ActivityType.GUARDIA_AULA, "Planta 1", "Guardia de Aula"))
    schedules.append(ScheduleItem("carlos-ruiz", 1, "REC", ActivityType.GUARDIA_RECREO, "Patio Central", "Guardia de Recreo"))
    schedules.append(ScheduleItem("carlos-ruiz", 1, "4H", ActivityType.LECTIVA, "Aula 102", "Matemáticas 1º ESO B"))
    schedules.append(ScheduleItem("carlos-ruiz", 1, "5H", ActivityType.DISPONIBLE, "Sala Profesores", "Hora complementaria"))

    # 2. María López (Matemáticas)
    schedules.append(ScheduleItem("maria-lopez", 1, "1H", ActivityType.GUARDIA_AULA, "Planta 2", "Guardia de Aula"))
    schedules.append(ScheduleItem("maria-lopez", 1, "2H", ActivityType.LECTIVA, "Aula 201", "Matemáticas 3º ESO A"))
    schedules.append(ScheduleItem("maria-lopez", 1, "3H", ActivityType.LECTIVA, "Aula 202", "Matemáticas 3º ESO B"))
    schedules.append(ScheduleItem("maria-lopez", 1, "4H", ActivityType.DISPONIBLE, "Sala Profesores", "Preparación"))
    schedules.append(ScheduleItem("maria-lopez", 1, "5H", ActivityType.LECTIVA, "Aula 204", "Matemáticas 4º ESO A"))

    # 3. Javier Morales (Ciencias)
    schedules.append(ScheduleItem("javier-morales", 1, "1H", ActivityType.LECTIVA, "Lab Física", "Física y Química 3º ESO"))
    schedules.append(ScheduleItem("javier-morales", 1, "2H", ActivityType.DISPONIBLE, "Lab Física", "Preparación Laboratorio"))
    schedules.append(ScheduleItem("javier-morales", 1, "3H", ActivityType.DISPONIBLE, "Sala Profesores", "Hora libre complementaria"))
    schedules.append(ScheduleItem("javier-morales", 1, "4H", ActivityType.GUARDIA_AULA, "Planta 2", "Guardia de Aula"))
    schedules.append(ScheduleItem("javier-morales", 1, "5H", ActivityType.LECTIVA, "Lab Química", "Física y Química 4º ESO"))

    # 4. Lucía Sánchez (Lengua)
    schedules.append(ScheduleItem("lucia-sanchez", 1, "1H", ActivityType.LECTIVA, "Aula 203", "Lengua 2º ESO"))
    schedules.append(ScheduleItem("lucia-sanchez", 1, "2H", ActivityType.LECTIVA, "Aula 204", "Lengua 3º ESO"))
    schedules.append(ScheduleItem("lucia-sanchez", 1, "3H", ActivityType.NO_DISPONIBLE, "Despacho", "Reunión Jefatura"))
    schedules.append(ScheduleItem("lucia-sanchez", 1, "4H", ActivityType.GUARDIA_AULA, "Planta 1", "Guardia de Aula"))

    # 5. David Castro (Ed. Física)
    schedules.append(ScheduleItem("david-castro", 1, "1H", ActivityType.DISPONIBLE, "Gimnasio", "Organización material"))
    schedules.append(ScheduleItem("david-castro", 1, "2H", ActivityType.GUARDIA_AULA, "Pabellón", "Guardia de Aula"))
    schedules.append(ScheduleItem("david-castro", 1, "3H", ActivityType.GUARDIA_AULA, "Pabellón", "Guardia de Aula"))
    schedules.append(ScheduleItem("david-castro", 1, "4H", ActivityType.LECTIVA, "Pistas", "Educación Física 1º ESO"))

    # 6. Ana Gutiérrez (Geografía e Historia)
    schedules.append(ScheduleItem("ana-gutierrez", 1, "1H", ActivityType.LECTIVA, "Aula 103", "Historia 4º ESO"))
    schedules.append(ScheduleItem("ana-gutierrez", 1, "2H", ActivityType.LECTIVA, "Aula 104", "Geografía 2º ESO"))
    schedules.append(ScheduleItem("ana-gutierrez", 1, "3H", ActivityType.DISPONIBLE, "Biblioteca", "Atención biblioteca"))

    # Rellenar resto de días con patrones base para pruebas
    for dia in [0, 2, 3, 4]:
        for teacher in ["carlos-ruiz", "maria-lopez", "javier-morales", "lucia-sanchez", "david-castro", "ana-gutierrez"]:
            for slot_id in ["1H", "2H", "3H", "4H", "5H"]:
                schedules.append(ScheduleItem(
                    profesor_id=teacher,
                    dia_semana=dia,
                    periodo_id=slot_id,
                    tipo_actividad=ActivityType.GUARDIA_AULA if slot_id == "2H" else ActivityType.LECTIVA,
                    aula="Aula General",
                    materia="Clase Regular" if slot_id != "2H" else "Guardia"
                ))

    return schedules

def seed_database_if_empty(db: Database, force: bool = False):
    """Inicializa la base de datos con datos de prueba si los archivos están vacíos."""
    if force or len(db.get_time_slots()) == 0:
        db.save_time_slots(generate_default_time_slots())
    
    if force or len(db.get_teachers()) == 0:
        db.save_teachers(generate_default_teachers())
        
    if force or len(db.get_schedules()) == 0:
        db.save_schedules(generate_default_schedules())

if __name__ == "__main__":
    db = Database()
    seed_database_if_empty(db, force=True)
    print(f"Base de datos poblada exitosamente:")
    print(f"- Tramos horarios: {len(db.get_time_slots())}")
    print(f"- Profesores: {len(db.get_teachers())}")
    print(f"- Elementos de horario: {len(db.get_schedules())}")
