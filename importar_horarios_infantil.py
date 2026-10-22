"""
Script de importación oficial para los horarios de Educación Infantil (3, 4 y 5 años)
del Colegio San Buenaventura.
Regla clave: Siempre que hay un hueco en el horario de una profesora, está DISPONIBLE para sustituir.
"""

import os
import json
import sqlite3
from models import Teacher, TimeSlot, ScheduleItem, ActivityType
from database import Database

db = Database()

# 1. Definición de tramos horarios propios de Infantil (08:45 a 16:00)
TRAMOS_INFANTIL = [
    TimeSlot(id="INF_1H", nombre="1ª Hora (08:45 - 09:30)", hora_inicio="08:45", hora_fin="09:30", es_recreo=False, orden=101, etapa="Infantil"),
    TimeSlot(id="INF_2H", nombre="2ª Hora (09:30 - 10:00)", hora_inicio="09:30", hora_fin="10:00", es_recreo=False, orden=102, etapa="Infantil"),
    TimeSlot(id="INF_REC", nombre="Recreo (10:00 - 10:30)", hora_inicio="10:00", hora_fin="10:30", es_recreo=True, orden=103, etapa="Infantil"),
    TimeSlot(id="INF_3H", nombre="3ª Hora (10:30 - 11:15)", hora_inicio="10:30", hora_fin="11:15", es_recreo=False, orden=104, etapa="Infantil"),
    TimeSlot(id="INF_4H", nombre="4ª Hora (11:15 - 12:15)", hora_inicio="11:15", hora_fin="12:15", es_recreo=False, orden=105, etapa="Infantil"),
    TimeSlot(id="INF_COM", nombre="Comedor (12:15 - 14:00)", hora_inicio="12:15", hora_fin="14:00", es_recreo=True, orden=106, etapa="Infantil"),
    TimeSlot(id="INF_5H", nombre="5ª Hora (14:00 - 15:00)", hora_inicio="14:00", hora_fin="15:00", es_recreo=False, orden=107, etapa="Infantil"),
    TimeSlot(id="INF_6H", nombre="6ª Hora (15:00 - 16:00)", hora_inicio="15:00", hora_fin="16:00", es_recreo=False, orden=108, etapa="Infantil"),
]

# 2. Las 11 profesoras de Educación Infantil
PROFESORES_INFANTIL = [
    Teacher(
        id="ACAL0",
        nombre="Alejandra Calvo López-Covarrubias",
        telefono="",
        email="alejandracalvo@sanbuenaventura.org",
        departamento="Tutoría 3 años-C",
        etapa="Infantil",
        activo=True,
        sustituciones_realizadas=0
    ),
    Teacher(
        id="APER0",
        nombre="Alejandra Pérez Villalba",
        telefono="",
        email="alejandraperez@sanbuenaventura.org",
        departamento="Tutoría 5 años-A / Robótica",
        etapa="Infantil",
        activo=True,
        sustituciones_realizadas=0
    ),
    Teacher(
        id="CDUE1",
        nombre="Cristina Duerto del Pino",
        telefono="",
        email="cristinaduerto@sanbuenaventura.org",
        departamento="Inglés Infantil",
        etapa="Infantil",
        activo=True,
        sustituciones_realizadas=0
    ),
    Teacher(
        id="E587",
        nombre="Elena Díaz Martín",
        telefono="",
        email="elenadiaz@sanbuenaventura.org",
        departamento="Tutoría 3 años-A / Coordinación Infantil",
        etapa="Infantil",
        activo=True,
        sustituciones_realizadas=0
    ),
    Teacher(
        id="GDEL0",
        nombre="Gema del Pozo Villegas",
        telefono="",
        email="gemadelpozo@sanbuenaventura.org",
        departamento="Tutoría 4 años-C / Inglés",
        etapa="Infantil",
        activo=True,
        sustituciones_realizadas=0
    ),
    Teacher(
        id="M251",
        nombre="Mª de las Nieves Jiménez Jiménez",
        telefono="",
        email="nievesjimenez@sanbuenaventura.org",
        departamento="Tutoría 3 años-B / Psicomotricidad",
        etapa="Infantil",
        activo=True,
        sustituciones_realizadas=0
    ),
    Teacher(
        id="M111",
        nombre="María Jesús Parras Maeso",
        telefono="",
        email="mariajesusparras@sanbuenaventura.org",
        departamento="Música y Robótica",
        etapa="Infantil",
        activo=True,
        sustituciones_realizadas=0
    ),
    Teacher(
        id="MESP0",
        nombre="Maria Teresa Espejo Rodríguez",
        telefono="",
        email="mariateresaespejo@sanbuenaventura.org",
        departamento="Tutoría 5 años-B / Psicomotricidad",
        etapa="Infantil",
        activo=True,
        sustituciones_realizadas=0
    ),
    Teacher(
        id="M133",
        nombre="Marta Rodríguez Centeno",
        telefono="",
        email="martarodriguez@sanbuenaventura.org",
        departamento="Tutoría 5 años-C / Inglés",
        etapa="Infantil",
        activo=True,
        sustituciones_realizadas=0
    ),
    Teacher(
        id="N637",
        nombre="Nuria Romero Sanz",
        telefono="",
        email="nuriaromero@sanbuenaventura.org",
        departamento="Tutoría 4 años-B / Música",
        etapa="Infantil",
        activo=True,
        sustituciones_realizadas=0
    ),
    Teacher(
        id="SUS8",
        nombre="Susana López Gómez",
        telefono="",
        email="susanalopez@sanbuenaventura.org",
        departamento="Tutoría 4 años-A",
        etapa="Infantil",
        activo=True,
        sustituciones_realizadas=0
    )
]

# Diccionario completo de horarios por profesora
# Formato: (dia_semana, periodo_id): (aula, materia)
# Si no está en el diccionario o es None -> es un HUECO LIBRE -> DISPONIBLE
NOMBRES_MATERIAS = {
    "CAR": "Crecimiento en armonía",
    "CAR2": "Crecimiento en armonía II",
    "PSI": "Psicomotricidad",
    "DEE3": "Descubrimiento y Exploración del Entorno",
    "DEE3.1": "Descubrimiento y exploración del entorno",
    "DEE3.2": "Descubrimiento y Exploración del Entorno II",
    "CRR": "Comunicación y representación de la realidad",
    "CRR 2": "Comunicación y representación de la realidad II",
    "CRR II": "Comunicación y representación de la realidad II",
    "REL3": "Religión",
    "ING": "Lengua extranjera inglés",
    "d179": "Descubrimiento y Exploración del Entorno II",
    "MUS": "Lenguaje y expresión musical",
    "RBT": "Robótica y programación"
}

HORARIOS_DOCENTES = {
    # 1. ALEJANDRA CALVO LOPEZ-COVARRUBIAS (ACAL0) - Pág. 10
    "ACAL0": {
        (1, "INF_1H"): ("3 años-C", "CRR: Comunicación y representación de la realidad"),
        (3, "INF_1H"): ("3 años-C", "CRR: Comunicación y representación de la realidad"),
        (0, "INF_2H"): ("3 años-C", "CAR: Crecimiento en armonía"),
        (1, "INF_2H"): ("3 años-C", "CAR: Crecimiento en armonía"),
        (2, "INF_2H"): ("3 años-C", "CAR: Crecimiento en armonía"),
        (3, "INF_2H"): ("3 años-C", "REL3: Religión"),
        (4, "INF_2H"): ("3 años-C", "CAR: Crecimiento en armonía"),
        (0, "INF_3H"): ("3 años-C", "DEE3: Descubrimiento y Exploración del Entorno"),
        (1, "INF_3H"): ("3 años-C", "DEE3: Descubrimiento y Exploración del Entorno"),
        (2, "INF_3H"): ("3 años-C", "DEE3: Descubrimiento y Exploración del Entorno"),
        (4, "INF_3H"): ("3 años-C", "DEE3: Descubrimiento y Exploración del Entorno"),
        (0, "INF_4H"): ("3 años-C", "CRR: Comunicación y representación de la realidad"),
        (1, "INF_4H"): ("3 años-C", "DEE3: Descubrimiento y Exploración del Entorno"),
        (2, "INF_4H"): ("3 años-C", "CAR: Crecimiento en armonía"),
        (4, "INF_4H"): ("3 años-C", "REL3: Religión"),
        (0, "INF_5H"): ("3 años-C", "DEE3: Descubrimiento y Exploración del Entorno"),
        (1, "INF_5H"): ("3 años-C", "DEE3: Descubrimiento y Exploración del Entorno"),
        (2, "INF_5H"): ("3 años-C", "MUS: Lenguaje y expresión musical"),
        (3, "INF_5H"): ("3 años-C", "DEE3: Descubrimiento y Exploración del Entorno"),
        (4, "INF_5H"): ("3 años-C", "CRR: Comunicación y representación de la realidad"),
        (0, "INF_6H"): ("3 años-C", "CRR: Comunicación y representación de la realidad"),
        (1, "INF_6H"): ("3 años-C", "CRR: Comunicación y representación de la realidad"),
        (2, "INF_6H"): ("3 años-C", "RBT: Robótica y programación"),
        (3, "INF_6H"): ("3 años-C", "DEE3: Descubrimiento y Exploración del Entorno"),
        (4, "INF_6H"): ("3 años-C", "CAR: Crecimiento en armonía"),
    },

    # 2. ALEJANDRA PÉREZ VILLALBA (APER0) - Pág. 11
    "APER0": {
        (0, "INF_1H"): ("5 años-A", "DEE3: Descubrimiento y Exploración del Entorno"),
        (1, "INF_1H"): ("5 años-C", "DEE3.2: Descubrimiento y Exploración del Entorno II"),
        (2, "INF_1H"): ("5 años-A", "DEE3: Descubrimiento y Exploración del Entorno"),
        (3, "INF_1H"): ("5 años-A", "DEE3: Descubrimiento y Exploración del Entorno"),
        (4, "INF_1H"): ("5 años-A", "DEE3: Descubrimiento y Exploración del Entorno"),
        (0, "INF_2H"): ("5 años-A", "CAR: Crecimiento en armonía"),
        (1, "INF_2H"): ("5 años-A", "CAR: Crecimiento en armonía"),
        (2, "INF_2H"): ("5 años-A", "CAR: Crecimiento en armonía"),
        (3, "INF_2H"): ("5 años-C", "CRR 2: Comunicación y representación de la realidad II"),
        (4, "INF_2H"): ("5 años-A", "CAR: Crecimiento en armonía"),
        (0, "INF_3H"): ("5 años-A", "CRR: Comunicación y representación de la realidad"),
        (1, "INF_3H"): ("5 años-A", "REL3: Religión"),
        (2, "INF_3H"): ("5 años-A", "CRR: Comunicación y representación de la realidad"),
        (3, "INF_3H"): ("5 años-A", "CRR: Comunicación y representación de la realidad"),
        (4, "INF_3H"): ("5 años-A", "REL3: Religión"),
        (0, "INF_4H"): ("5 años-A", "CRR: Comunicación y representación de la realidad"),
        (1, "INF_4H"): ("5 años-A", "CRR: Comunicación y representación de la realidad"),
        (2, "INF_4H"): ("5 años-A", "DEE3: Descubrimiento y Exploración del Entorno"),
        (3, "INF_4H"): ("5 años-A", "DEE3: Descubrimiento y Exploración del Entorno"),
        (4, "INF_4H"): ("5 años-A", "CRR: Comunicación y representación de la realidad"),
        (0, "INF_5H"): ("5 años-B", "RBT: Robótica y programación"),
        (2, "INF_5H"): ("5 años-A", "DEE3: Descubrimiento y Exploración del Entorno"),
        (3, "INF_5H"): ("5 años-A", "DEE3: Descubrimiento y Exploración del Entorno"),
        (4, "INF_5H"): ("5 años-A", "DEE3: Descubrimiento y Exploración del Entorno"),
        (0, "INF_6H"): ("5 años-C", "RBT: Robótica y programación"),
        (1, "INF_6H"): ("5 años-A", "RBT: Robótica y programación"),
        (2, "INF_6H"): ("5 años-A", "DEE3: Descubrimiento y Exploración del Entorno"),
        (4, "INF_6H"): ("5 años-A", "DEE3: Descubrimiento y Exploración del Entorno"),
    },

    # 3. CRISTINA DUERTO DEL PINO (CDUE1) - Pág. 12
    "CDUE1": {
        (0, "INF_1H"): ("3 años-C", "ING: Lengua extranjera inglés"),
        (2, "INF_1H"): ("3 años-C", "ING: Lengua extranjera inglés"),
        (4, "INF_1H"): ("3 años-A", "ING: Lengua extranjera inglés"),
        (0, "INF_3H"): ("3 años-B", "ING: Lengua extranjera inglés"),
        (1, "INF_3H"): ("3 años-B", "ING: Lengua extranjera inglés"),
        (2, "INF_3H"): ("3 años-B", "ING: Lengua extranjera inglés"),
        (4, "INF_3H"): ("4 años-C", "d179: Descubrimiento y Exploración del Entorno II"),
        (1, "INF_4H"): ("3 años-A", "ING: Lengua extranjera inglés"),
        (2, "INF_4H"): ("3 años-A", "ING: Lengua extranjera inglés"),
        (3, "INF_4H"): ("3 años-C", "ING: Lengua extranjera inglés"),
    },

    # 4. ELENA DÍAZ MARTÍN (E587) - Pág. 13
    "E587": {
        (0, "INF_1H"): ("3 años-A", "CAR: Crecimiento en armonía"),
        (1, "INF_1H"): ("3 años-A", "PSI: Psicomotricidad"),
        (2, "INF_1H"): ("3 años-A", "CAR: Crecimiento en armonía"),
        (3, "INF_1H"): ("3 años-A", "PSI: Psicomotricidad"),
        (4, "INF_1H"): ("3 años-C", "PSI: Psicomotricidad"),
        (0, "INF_2H"): ("3 años-A", "CAR: Crecimiento en armonía"),
        (1, "INF_2H"): ("3 años-A", "CAR: Crecimiento en armonía"),
        (2, "INF_2H"): ("3 años-A", "CAR: Crecimiento en armonía"),
        (3, "INF_2H"): ("3 años-A", "CAR: Crecimiento en armonía"),
        (4, "INF_2H"): ("3 años-A", "REL3: Religión"),
        (0, "INF_3H"): ("3 años-A", "DEE3: Descubrimiento y Exploración del Entorno"),
        (1, "INF_3H"): ("3 años-A", "DEE3: Descubrimiento y Exploración del Entorno"),
        (2, "INF_3H"): ("3 años-A", "DEE3: Descubrimiento y Exploración del Entorno"),
        (3, "INF_3H"): ("3 años-C", "PSI: Psicomotricidad"),
        (4, "INF_3H"): ("3 años-A", "DEE3: Descubrimiento y Exploración del Entorno"),
        (0, "INF_4H"): ("3 años-A", "DEE3: Descubrimiento y Exploración del Entorno"),
        (1, "INF_4H"): ("4 años-A", "PSI: Psicomotricidad"),
        (2, "INF_4H"): ("4 años-A", "PSI: Psicomotricidad"),
        (3, "INF_4H"): ("3 años-A", "DEE3: Descubrimiento y Exploración del Entorno"),
        (0, "INF_5H"): ("3 años-A", "CRR: Comunicación y representación de la realidad"),
        (1, "INF_5H"): ("3 años-A", "CRR: Comunicación y representación de la realidad"),
        (2, "INF_5H"): ("3 años-A", "CRR: Comunicación y representación de la realidad"),
        (3, "INF_5H"): ("3 años-A", "DEE3: Descubrimiento y Exploración del Entorno"),
        (4, "INF_5H"): ("3 años-A", "DEE3: Descubrimiento y Exploración del Entorno"),
        (0, "INF_6H"): ("3 años-A", "CRR: Comunicación y representación de la realidad"),
        (1, "INF_6H"): ("3 años-A", "CRR: Comunicación y representación de la realidad"),
        (2, "INF_6H"): ("3 años-A", "DEE3: Descubrimiento y Exploración del Entorno"),
        (3, "INF_6H"): ("3 años-A", "REL3: Religión"),
        (4, "INF_6H"): ("3 años-A", "CRR: Comunicación y representación de la realidad"),
    },

    # 5. GEMA DEL POZO VILLEGAS (GDEL0) - Pág. 14
    "GDEL0": {
        (0, "INF_1H"): ("4 años-C", "CAR: Crecimiento en armonía"),
        (1, "INF_1H"): ("4 años-C", "CAR: Crecimiento en armonía"),
        (2, "INF_1H"): ("4 años-C", "REL3: Religión"),
        (3, "INF_1H"): ("4 años-C", "ING: Lengua extranjera inglés"),
        (4, "INF_1H"): ("4 años-C", "CAR: Crecimiento en armonía"),
        (0, "INF_2H"): ("4 años-C", "CAR: Crecimiento en armonía"),
        (1, "INF_2H"): ("4 años-C", "REL3: Religión"),
        (2, "INF_2H"): ("4 años-C", "CAR: Crecimiento en armonía"),
        (3, "INF_2H"): ("4 años-B", "ING: Lengua extranjera inglés"),
        (4, "INF_2H"): ("4 años-C", "ING: Lengua extranjera inglés"),
        (0, "INF_3H"): ("4 años-C", "DEE3: Descubrimiento y Exploración del Entorno"),
        (1, "INF_3H"): ("4 años-C", "CAR: Crecimiento en armonía"),
        (2, "INF_3H"): ("4 años-B", "ING: Lengua extranjera inglés"),
        (3, "INF_3H"): ("4 años-C", "DEE3: Descubrimiento y Exploración del Entorno"),
        (4, "INF_3H"): ("4 años-A", "ING: Lengua extranjera inglés"),
        (0, "INF_4H"): ("4 años-A", "ING: Lengua extranjera inglés"),
        (1, "INF_4H"): ("4 años-B", "ING: Lengua extranjera inglés"),
        (2, "INF_4H"): ("4 años-C", "ING: Lengua extranjera inglés"),
        (3, "INF_4H"): ("4 años-C", "DEE3: Descubrimiento y Exploración del Entorno"),
        (4, "INF_4H"): ("4 años-C", "CRR: Comunicación y representación de la realidad"),
        (0, "INF_5H"): ("4 años-C", "DEE3: Descubrimiento y Exploración del Entorno"),
        (1, "INF_5H"): ("4 años-C", "DEE3: Descubrimiento y Exploración del Entorno"),
        (2, "INF_5H"): ("4 años-A", "ING: Lengua extranjera inglés"),
        (3, "INF_5H"): ("4 años-C", "CRR: Comunicación y representación de la realidad"),
        (4, "INF_5H"): ("4 años-C", "CRR: Comunicación y representación de la realidad"),
        (0, "INF_6H"): ("4 años-C", "CRR: Comunicación y representación de la realidad"),
        (1, "INF_6H"): ("4 años-C", "CAR: Crecimiento en armonía"),
        (2, "INF_6H"): ("4 años-C", "DEE3: Descubrimiento y Exploración del Entorno"),
        (3, "INF_6H"): ("4 años-C", "DEE3: Descubrimiento y Exploración del Entorno"),
        (4, "INF_6H"): ("4 años-C", "CRR: Comunicación y representación de la realidad"),
    },

    # 6. Mª DE LAS NIEVES JIMÉNEZ JIMÉNEZ (M251) - Pág. 15
    "M251": {
        (0, "INF_1H"): ("3 años-B", "PSI: Psicomotricidad"),
        (1, "INF_1H"): ("3 años-B", "CAR: Crecimiento en armonía"),
        (2, "INF_1H"): ("3 años-B", "PSI: Psicomotricidad"),
        (3, "INF_1H"): ("3 años-B", "CAR: Crecimiento en armonía"),
        (4, "INF_1H"): ("3 años-B", "CAR: Crecimiento en armonía"),
        (0, "INF_2H"): ("3 años-B", "CAR: Crecimiento en armonía"),
        (1, "INF_2H"): ("3 años-B", "DEE3: Descubrimiento y Exploración del Entorno"),
        (2, "INF_2H"): ("3 años-B", "CAR: Crecimiento en armonía"),
        (3, "INF_2H"): ("3 años-B", "DEE3: Descubrimiento y Exploración del Entorno"),
        (4, "INF_2H"): ("3 años-B", "REL3: Religión"),
        (0, "INF_3H"): ("4 años-B", "PSI: Psicomotricidad"),
        (1, "INF_3H"): ("4 años-B", "PSI: Psicomotricidad"),
        (2, "INF_3H"): ("4 años-C", "PSI: Psicomotricidad"),
        (3, "INF_3H"): ("3 años-B", "DEE3: Descubrimiento y Exploración del Entorno"),
        (4, "INF_3H"): ("3 años-B", "CAR: Crecimiento en armonía"),
        (0, "INF_4H"): ("4 años-C", "PSI: Psicomotricidad"),
        (1, "INF_4H"): ("3 años-B", "MUS: Lenguaje y expresión musical"),
        (2, "INF_4H"): ("3 años-B", "REL3: Religión"),
        (3, "INF_4H"): ("3 años-B", "DEE3: Descubrimiento y Exploración del Entorno"),
        (4, "INF_4H"): ("3 años-B", "DEE3: Descubrimiento y Exploración del Entorno"),
        (0, "INF_5H"): ("3 años-B", "CRR: Comunicación y representación de la realidad"),
        (1, "INF_5H"): ("3 años-B", "DEE3: Descubrimiento y Exploración del Entorno"),
        (2, "INF_5H"): ("3 años-B", "DEE3: Descubrimiento y Exploración del Entorno"),
        (3, "INF_5H"): ("3 años-B", "DEE3: Descubrimiento y Exploración del Entorno"),
        (4, "INF_5H"): ("3 años-B", "CRR: Comunicación y representación de la realidad"),
        (0, "INF_6H"): ("3 años-B", "CRR: Comunicación y representación de la realidad"),
        (1, "INF_6H"): ("3 años-B", "CRR: Comunicación y representación de la realidad"),
        (2, "INF_6H"): ("3 años-B", "CRR: Comunicación y representación de la realidad"),
        (3, "INF_6H"): ("3 años-B", "DEE3: Descubrimiento y Exploración del Entorno"),
        (4, "INF_6H"): ("3 años-B", "CRR: Comunicación y representación de la realidad"),
    },

    # 7. MARÍA JESÚS PARRAS MAESO (M111) - Pág. 16
    "M111": {
        (1, "INF_2H"): ("5 años-C", "MUS: Lenguaje y expresión musical"),
        (3, "INF_3H"): ("3 años-A", "MUS: Lenguaje y expresión musical"),
        (0, "INF_4H"): ("3 años-B", "RBT: Robótica y programación"),
        (3, "INF_4H"): ("4 años-A", "RBT: Robótica y programación"),
        (4, "INF_4H"): ("3 años-A", "RBT: Robótica"),
        (1, "INF_5H"): ("5 años-A", "MUS: Lenguaje y expresión musical"),
        (2, "INF_5H"): ("4 años-C", "RBT: Robótica y programación"),
        (4, "INF_5H"): ("4 años-A", "MUS: Lenguaje y expresión musical"),
        (3, "INF_6H"): ("5 años-B", "MUS: Lenguaje y expresión musical"),
    },

    # 8. MARIA TERESA ESPEJO RODRÍGUEZ (MESP0) - Pág. 17
    "MESP0": {
        (0, "INF_1H"): ("5 años-B", "CAR: Crecimiento en armonía"),
        (1, "INF_1H"): ("5 años-B", "CAR: Crecimiento en armonía"),
        (2, "INF_1H"): ("5 años-B", "CAR: Crecimiento en armonía"),
        (3, "INF_1H"): ("5 años-B", "CAR: Crecimiento en armonía"),
        (4, "INF_1H"): ("5 años-B", "CAR: Crecimiento en armonía"),
        (0, "INF_2H"): ("5 años-B", "CRR: Comunicación y representación de la realidad"),
        (2, "INF_2H"): ("5 años-B", "CAR: Crecimiento en armonía"),
        (3, "INF_2H"): ("5 años-B", "CRR: Comunicación y representación de la realidad"),
        (4, "INF_2H"): ("5 años-B", "CRR: Comunicación y representación de la realidad"),
        (0, "INF_3H"): ("5 años-B", "DEE3: Descubrimiento y Exploración del Entorno"),
        (1, "INF_3H"): ("5 años-B", "DEE3: Descubrimiento y Exploración del Entorno"),
        (2, "INF_3H"): ("5 años-B", "CRR: Comunicación y representación de la realidad"),
        (3, "INF_3H"): ("5 años-B", "REL3: Religión"),
        (4, "INF_3H"): ("5 años-B", "REL3: Religión"),
        (0, "INF_4H"): ("5 años-B", "DEE3: Descubrimiento y Exploración del Entorno"),
        (1, "INF_4H"): ("5 años-B", "DEE3: Descubrimiento y Exploración del Entorno"),
        (2, "INF_4H"): ("5 años-B", "DEE3: Descubrimiento y Exploración del Entorno"),
        (3, "INF_4H"): ("5 años-B", "DEE3: Descubrimiento y Exploración del Entorno"),
        (4, "INF_4H"): ("5 años-C", "PSI: Psicomotricidad"),
        (0, "INF_5H"): ("5 años-C", "PSI: Psicomotricidad"),
        (1, "INF_5H"): ("5 años-B", "CRR: Comunicación y representación de la realidad"),
        (2, "INF_5H"): ("5 años-B", "DEE3: Descubrimiento y Exploración del Entorno"),
        (3, "INF_5H"): ("5 años-B", "DEE3: Descubrimiento y Exploración del Entorno"),
        (4, "INF_5H"): ("5 años-B", "CRR: Comunicación y representación de la realidad"),
        (0, "INF_6H"): ("5 años-A", "PSI: Psicomotricidad"),
        (1, "INF_6H"): ("5 años-B", "PSI: Psicomotricidad"),
        (2, "INF_6H"): ("5 años-B", "PSI: Psicomotricidad"),
        (3, "INF_6H"): ("5 años-A", "PSI: Psicomotricidad"),
        (4, "INF_6H"): ("5 años-B", "DEE3: Descubrimiento y Exploración del Entorno"),
    },

    # 9. MARTA RODRÍGUEZ CENTENO (M133) - Pág. 18
    "M133": {
        (0, "INF_1H"): ("5 años-C", "DEE3.1: Descubrimiento y exploración del entorno"),
        (1, "INF_1H"): ("5 años-A", "ING: Lengua extranjera inglés"),
        (2, "INF_1H"): ("5 años-C", "DEE3.1: Descubrimiento y exploración del entorno"),
        (3, "INF_1H"): ("5 años-C", "DEE3.1: Descubrimiento y exploración del entorno"),
        (4, "INF_1H"): ("5 años-C", "ING: Lengua extranjera inglés"),
        (0, "INF_2H"): ("5 años-C", "ING: Lengua extranjera inglés"),
        (1, "INF_2H"): ("5 años-B", "ING: Lengua extranjera inglés"),
        (2, "INF_2H"): ("5 años-C", "ING: Lengua extranjera inglés"),
        (3, "INF_2H"): ("5 años-A", "ING: Lengua extranjera inglés"),
        (4, "INF_2H"): ("5 años-C", "REL3: Religión"),
        (0, "INF_3H"): ("5 años-C", "CAR: Crecimiento en armonía"),
        (1, "INF_3H"): ("5 años-C", "CAR: Crecimiento en armonía"),
        (2, "INF_3H"): ("5 años-C", "CAR: Crecimiento en armonía"),
        (3, "INF_3H"): ("5 años-C", "CAR: Crecimiento en armonía"),
        (4, "INF_3H"): ("5 años-C", "CAR: Crecimiento en armonía"),
        (0, "INF_4H"): ("5 años-C", "CRR: Comunicación y representación de la realidad"),
        (1, "INF_4H"): ("5 años-C", "CRR: Comunicación y representación de la realidad"),
        (2, "INF_4H"): ("5 años-C", "CRR: Comunicación y representación de la realidad"),
        (3, "INF_4H"): ("5 años-C", "REL3: Religión"),
        (4, "INF_4H"): ("5 años-B", "ING: Lengua extranjera inglés"),
        (0, "INF_5H"): ("5 años-A", "ING: Lengua extranjera inglés"),
        (1, "INF_5H"): ("5 años-C", "CRR: Comunicación y representación de la realidad"),
        (2, "INF_5H"): ("5 años-C", "CRR: Comunicación y representación de la realidad"),
        (3, "INF_5H"): ("5 años-C", "CRR: Comunicación y representación de la realidad"),
        (4, "INF_5H"): ("5 años-C", "CRR: Comunicación y representación de la realidad"),
        (0, "INF_6H"): ("5 años-B", "ING: Lengua extranjera inglés"),
        (1, "INF_6H"): ("5 años-C", "DEE3.1: Descubrimiento y exploración del entorno"),
        (2, "INF_6H"): ("5 años-C", "DEE3.1: Descubrimiento y exploración del entorno"),
        (3, "INF_6H"): ("5 años-C", "DEE3.1: Descubrimiento y exploración del entorno"),
        (4, "INF_6H"): ("5 años-C", "DEE3.1: Descubrimiento y exploración del entorno"),
    },

    # 10. NURIA ROMERO SANZ (N637) - Pág. 19
    "N637": {
        (0, "INF_1H"): ("4 años-B", "CAR: Crecimiento en armonía"),
        (1, "INF_1H"): ("4 años-B", "CAR: Crecimiento en armonía"),
        (2, "INF_1H"): ("4 años-B", "REL3: Religión"),
        (3, "INF_1H"): ("4 años-B", "CAR: Crecimiento en armonía"),
        (4, "INF_1H"): ("4 años-B", "CAR: Crecimiento en armonía"),
        (0, "INF_2H"): ("4 años-B", "CAR: Crecimiento en armonía"),
        (1, "INF_2H"): ("4 años-B", "CAR: Crecimiento en armonía"),
        (2, "INF_2H"): ("4 años-B", "CAR: Crecimiento en armonía"),
        (3, "INF_2H"): ("4 años-C", "CAR2: Crecimiento en armonía II"),
        (4, "INF_2H"): ("4 años-B", "REL3: Religión"),
        (1, "INF_3H"): ("4 años-A", "CRR II: Comunicación y representación de la realidad II"),
        (3, "INF_3H"): ("4 años-B", "DEE3: Descubrimiento y Exploración del Entorno"),
        (4, "INF_3H"): ("4 años-B", "DEE3: Descubrimiento y Exploración del Entorno"),
        (0, "INF_4H"): ("4 años-B", "MUS: Lenguaje y expresión musical"),
        (1, "INF_4H"): ("4 años-C", "MUS: Lenguaje y expresión musical"),
        (2, "INF_4H"): ("4 años-B", "CRR: Comunicación y representación de la realidad"),
        (3, "INF_4H"): ("4 años-B", "DEE3: Descubrimiento y Exploración del Entorno"),
        (4, "INF_4H"): ("4 años-B", "CRR: Comunicación y representación de la realidad"),
        (0, "INF_5H"): ("4 años-B", "DEE3: Descubrimiento y Exploración del Entorno"),
        (1, "INF_5H"): ("4 años-B", "DEE3: Descubrimiento y Exploración del Entorno"),
        (2, "INF_5H"): ("4 años-B", "DEE3: Descubrimiento y Exploración del Entorno"),
        (3, "INF_5H"): ("4 años-B", "DEE3: Descubrimiento y Exploración del Entorno"),
        (4, "INF_5H"): ("4 años-B", "DEE3: Descubrimiento y Exploración del Entorno"),
        (0, "INF_6H"): ("4 años-B", "DEE3: Descubrimiento y Exploración del Entorno"),
        (1, "INF_6H"): ("4 años-B", "CAR: Crecimiento en armonía"),
        (2, "INF_6H"): ("4 años-B", "RBT: Robótica y programación"),
        (3, "INF_6H"): ("4 años-B", "DEE3: Descubrimiento y Exploración del Entorno"),
        (4, "INF_6H"): ("4 años-B", "DEE3: Descubrimiento y Exploración del Entorno"),
    },

    # 11. SUSANA LÓPEZ GÓMEZ (SUS8) - Pág. 20
    "SUS8": {
        (0, "INF_1H"): ("4 años-A", "CAR: Crecimiento en armonía"),
        (1, "INF_1H"): ("4 años-A", "CAR: Crecimiento en armonía"),
        (2, "INF_1H"): ("4 años-A", "CAR: Crecimiento en armonía"),
        (3, "INF_1H"): ("4 años-A", "DEE3: Descubrimiento y Exploración del Entorno"),
        (4, "INF_1H"): ("4 años-A", "DEE3: Descubrimiento y Exploración del Entorno"),
        (0, "INF_2H"): ("4 años-A", "CAR: Crecimiento en armonía"),
        (1, "INF_2H"): ("4 años-A", "CAR: Crecimiento en armonía"),
        (2, "INF_2H"): ("4 años-A", "CAR: Crecimiento en armonía"),
        (3, "INF_2H"): ("4 años-A", "CAR: Crecimiento en armonía"),
        (4, "INF_2H"): ("4 años-A", "REL3: Religión"),
        (0, "INF_3H"): ("4 años-A", "DEE3: Descubrimiento y Exploración del Entorno"),
        (2, "INF_3H"): ("4 años-A", "DEE3: Descubrimiento y Exploración del Entorno"),
        (3, "INF_3H"): ("4 años-A", "DEE3: Descubrimiento y Exploración del Entorno"),
        (4, "INF_4H"): ("4 años-A", "CRR: Comunicación y representación de la realidad"),
        (0, "INF_5H"): ("4 años-A", "DEE3: Descubrimiento y Exploración del Entorno"),
        (1, "INF_5H"): ("4 años-A", "REL3: Religión"),
        (3, "INF_5H"): ("4 años-A", "CAR: Crecimiento en armonía"),
        (0, "INF_6H"): ("4 años-A", "CRR: Comunicación y representación de la realidad"),
        (1, "INF_6H"): ("4 años-A", "CRR: Comunicación y representación de la realidad"),
        (2, "INF_6H"): ("4 años-A", "CRR: Comunicación y representación de la realidad"),
        (3, "INF_6H"): ("4 años-A", "CRR: Comunicación y representación de la realidad"),
        (4, "INF_6H"): ("4 años-A", "CAR: Crecimiento en armonía"),
    }
}

def ejecutar_volcado():
    print("=== INICIANDO VOLCADO OFICIAL DE HORARIOS DE INFANTIL ===")
    
    # 1. Guardar tramos de Infantil
    db.upsert_time_slots(TRAMOS_INFANTIL)
    print(f"-> {len(TRAMOS_INFANTIL)} tramos horarios de Infantil guardados correctamente.")

    # 2. Guardar profesores de Infantil
    db.save_teachers(PROFESORES_INFANTIL)
    print(f"-> {len(PROFESORES_INFANTIL)} profesoras de Infantil guardadas correctamente.")

    # 3. Generar la matriz completa de horarios (30 tramos por profesora)
    # Si hay clase -> LECTIVA. Si NO hay clase (hueco) -> DISPONIBLE
    tramos_lectivos = ["INF_1H", "INF_2H", "INF_3H", "INF_4H", "INF_5H", "INF_6H"]
    dias_semana = [0, 1, 2, 3, 4] # Lunes a Viernes

    schedules_a_guardar = []
    conteo_lectivas = 0
    conteo_huecos = 0

    for prof in PROFESORES_INFANTIL:
        pid = prof.id
        horario_prof = HORARIOS_DOCENTES.get(pid, {})

        for dia in dias_semana:
            for periodo in tramos_lectivos:
                clave = (dia, periodo)
                if clave in horario_prof:
                    aula, materia = horario_prof[clave]
                    schedules_a_guardar.append(ScheduleItem(
                        profesor_id=pid,
                        dia_semana=dia,
                        periodo_id=periodo,
                        tipo_actividad=ActivityType.LECTIVA,
                        aula=aula,
                        materia=materia,
                        descripcion=f"{materia} en {aula}"
                    ))
                    conteo_lectivas += 1
                else:
                    # HUECO LIBRE -> DISPONIBLE para sustituir
                    schedules_a_guardar.append(ScheduleItem(
                        profesor_id=pid,
                        dia_semana=dia,
                        periodo_id=periodo,
                        tipo_actividad=ActivityType.DISPONIBLE,
                        aula="",
                        materia="",
                        descripcion="Hueco libre / Disponible para sustitución"
                    ))
                    conteo_huecos += 1

    db.upsert_schedules(schedules_a_guardar)
    print(f"-> Horarios volcados: {len(schedules_a_guardar)} registros en total.")
    print(f"   * Clases lectivas: {conteo_lectivas}")
    print(f"   * Huecos libres disponibles para sustituir: {conteo_huecos}")
    print("=== VOLCADO COMPLETADO CON ÉXITO ===")

if __name__ == "__main__":
    ejecutar_volcado()
