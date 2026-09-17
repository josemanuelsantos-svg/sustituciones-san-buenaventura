"""
Modelos de datos y estructuras para el Sistema de Sustituciones Escolares.
"""

from dataclasses import dataclass, asdict, field
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime, date, time

class ActivityType(str, Enum):
    LECTIVA = "LECTIVA"                           # Clase regular con alumnos (NO sustituible)
    GUARDIA_AULA = "GUARDIA_AULA"                 # Guardia de aula/pasillo (Máxima prioridad para sustituir)
    GUARDIA_RECREO = "GUARDIA_RECREO"             # Guardia de patio/recreo
    DISPONIBLE = "DISPONIBLE"                     # Hora complementaria/libre computable para sustitución
    NO_DISPONIBLE = "NO_DISPONIBLE"               # Reuniones, tutorías, jefatura, horas no utilizables

class StageType(str, Enum):
    INFANTIL = "Infantil"
    PRIMARIA = "Primaria"
    SECUNDARIA = "Secundaria"
    BACHILLERATO = "Bachillerato"
    GENERAL = "General"

@dataclass
class TimeSlot:
    id: str                                       # ej. "1H", "2H", "REC", "3H"
    nombre: str                                   # ej. "1ª Hora", "Recreo"
    hora_inicio: str                              # ej. "08:00"
    hora_fin: str                                 # ej. "08:55"
    es_recreo: bool = False
    orden: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class Teacher:
    id: str                                       # ej. "carlos-garcia"
    nombre: str                                   # ej. "Carlos García Pérez"
    telefono: str                                 # ej. "+34612345678"
    email: str                                    # ej. "carlos.garcia@colegio.es"
    departamento: str                             # ej. "Matemáticas"
    etapa: str                                    # ej. "Secundaria"
    activo: bool = True
    sustituciones_realizadas: int = 0             # Contador acumulado para reparto equitativo

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class ScheduleItem:
    profesor_id: str
    dia_semana: int                               # 0=Lunes, 1=Martes, 2=Miércoles, 3=Jueves, 4=Viernes
    periodo_id: str                               # Relacionado con TimeSlot.id
    tipo_actividad: str                           # ActivityType
    aula: Optional[str] = None                    # ej. "Aula 204", "Lab Química"
    materia: Optional[str] = None                 # ej. "Matemáticas 3º ESO"
    descripcion: Optional[str] = None             # ej. "Reunión de dpto"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class SubstitutionCandidate:
    profesor: Teacher
    tipo_disponibilidad: str                      # GUARDIA_AULA, DISPONIBLE, etc.
    puntuacion: float                             # Puntuación calculada por el motor
    motivo: str                                   # Justificación de la sugerencia
    es_recomendado: bool = False
    coincide_departamento: bool = False
    coincide_etapa: bool = False

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['profesor'] = self.profesor.to_dict()
        return data

@dataclass
class SubstitutionRecord:
    id: str
    fecha: str                                    # YYYY-MM-DD
    dia_semana: int                               # 0 a 4
    periodo_id: str
    periodo_nombre: str
    profesor_ausente_id: str
    profesor_ausente_nombre: str
    profesor_sustituto_id: str
    profesor_sustituto_nombre: str
    profesor_sustituto_telefono: str
    profesor_sustituto_email: str
    aula: str
    curso_grupo: str
    materia: str
    observaciones: str = ""
    estado: str = "ASIGNADA"                      # ASIGNADA, CONFIRMADA, CANCELADA
    creado_en: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
