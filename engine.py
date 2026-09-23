"""
Motor inteligente de recomendación y asignación de sustituciones escolares.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from models import (
    Teacher,
    TimeSlot,
    ScheduleItem,
    SubstitutionCandidate,
    SubstitutionRecord,
    ActivityType
)
from database import Database

class SubstitutionEngine:
    def __init__(self, db: Database):
        self.db = db

    def find_candidates(
        self,
        fecha_str: str,
        periodo_id: str,
        profesor_ausente_id: str,
        materia: Optional[str] = None,
        aula: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Encuentra y clasifica a todos los candidatos disponibles para cubrir una ausencia,
        ordenados según criterios pedagógicos, de guardia y equidad de carga.
        """
        # Determinar día de la semana (0=Lunes, 4=Viernes)
        fecha_dt = datetime.strptime(fecha_str, "%Y-%m-%d")
        dia_semana = fecha_dt.weekday()

        profesor_ausente = self.db.get_teacher(profesor_ausente_id)
        if not profesor_ausente:
            raise ValueError(f"No se encontró al profesor ausente con id '{profesor_ausente_id}'")

        slot = self.db.get_time_slot(periodo_id)
        if not slot:
            raise ValueError(f"No se encontró el tramo horario con id '{periodo_id}'")

        # Obtener todas las sustituciones existentes para esa fecha y hora
        sustituciones_del_dia = [
            s for s in self.db.get_substitutions()
            if s.fecha == fecha_str and s.periodo_id == periodo_id and s.estado != "CANCELADA"
        ]
        profesores_ya_sustituyendo = {s.profesor_sustituto_id for s in sustituciones_del_dia}
        profesores_ya_ausentes = {s.profesor_ausente_id for s in sustituciones_del_dia}
        profesores_ya_ausentes.add(profesor_ausente_id)

        todos_los_profesores = self.db.get_teachers(active_only=True)
        candidatos_evaluados: List[SubstitutionCandidate] = []
        no_disponibles: List[Dict[str, str]] = []

        for docente in todos_los_profesores:
            # 1. No puede sustituirse a sí mismo ni a quien ya esté ausente
            if docente.id in profesores_ya_ausentes:
                continue

            # 2. No puede tener ya otra sustitución en ese tramo
            if docente.id in profesores_ya_sustituyendo:
                no_disponibles.append({
                    "profesor_id": docente.id,
                    "profesor_nombre": docente.nombre,
                    "motivo": "Ya tiene asignada otra sustitución en este mismo tramo horario"
                })
                continue

            # 3. Consultar su horario en ese día y período
            horario_slot = self.db.get_slot_activity_for_teacher(docente.id, dia_semana, periodo_id)

            if not horario_slot:
                no_disponibles.append({
                    "profesor_id": docente.id,
                    "profesor_nombre": docente.nombre,
                    "motivo": "Sin guardia ni apoyo asignado en este tramo"
                })
                continue

            tipo_actividad = horario_slot.tipo_actividad
            detalle_actividad = horario_slot.materia or horario_slot.descripcion or tipo_actividad

            # 4. Filtrar según tipo de actividad
            if tipo_actividad == ActivityType.LECTIVA:
                no_disponibles.append({
                    "profesor_id": docente.id,
                    "profesor_nombre": docente.nombre,
                    "motivo": f"Clase lectiva ({detalle_actividad})"
                })
                continue
            
            if tipo_actividad == ActivityType.NO_DISPONIBLE:
                no_disponibles.append({
                    "profesor_id": docente.id,
                    "profesor_nombre": docente.nombre,
                    "motivo": f"No disponible para sustituir ({detalle_actividad})"
                })
                continue

            if tipo_actividad == ActivityType.GUARDIA_RECREO and not slot.es_recreo:
                no_disponibles.append({
                    "profesor_id": docente.id,
                    "profesor_nombre": docente.nombre,
                    "motivo": "Guardia de recreo en hora lectiva ordinaria"
                })
                continue

            # 5. Si pasa el filtro, es un candidato elegible.
            # Calculamos su puntuación según el orden de prelación oficial del centro:
            # 1º Empezando siempre por Isabel, Pilar F, Carmen o cualquier profesor con hueco/guardia
            # 2º Luego Rubén y Bea
            # 3º Luego Jose
            # 4º Luego Dani y María
            # 5º La última en sustituir es Belén
            
            puntuacion = 0.0
            motivos = []
            pid = docente.id.lower()

            if pid == "ipena":
                # Isabel Peña: máxima prioridad en sustituciones
                puntuacion = 1000.0
                motivos.append("🌟 Prioridad 1: Asignación preferente (Isabel Peña)")
            elif pid == "p740":
                # Pilar F
                puntuacion = 900.0
                motivos.append("🌟 Prioridad 1: Asignación preferente (Pilar F)")
            elif pid == "m654":
                # Carmen / Mª Carmen
                puntuacion = 850.0
                motivos.append("🌟 Prioridad 1: Asignación preferente (Carmen)")
            elif pid in ["r299", "bleo0"]:
                # Rubén y Bea
                puntuacion = 500.0
                motivos.append("Prioridad 2: Asignación intermedia (Rubén / Bea)")
            elif pid in ["jos7", "j414"]:
                # Jose (José Manuel Santos / José Antonio)
                puntuacion = 300.0
                motivos.append("Prioridad 3: Asignación de reserva (Jose)")
            elif pid in ["dasenjo", "mar1"]:
                # Dani y María (Daniel Asenjo / María Pilar Pérez)
                puntuacion = 150.0
                motivos.append("Prioridad 4: Asignación baja (Dani / María)")
            elif pid == "m851":
                # Belén: última en sustituir
                puntuacion = 50.0
                motivos.append("⚠️ Prioridad 5: Última opción de sustitución (Belén)")
            else:
                # Cualquier otro profesor que tenga guardia o hueco libre
                puntuacion = 700.0
                motivos.append("Prioridad 1: Docente disponible con hueco/guardia")

            # Detalle del tipo de disponibilidad
            if tipo_actividad == ActivityType.GUARDIA_AULA:
                motivos.append("En Guardia de Aula")
            elif tipo_actividad == ActivityType.DISPONIBLE:
                motivos.append("Horario de Apoyo / Libre")

            # Afinidad de departamento
            coincide_depto = False
            if docente.departamento and profesor_ausente.departamento and \
               docente.departamento.strip().lower() == profesor_ausente.departamento.strip().lower():
                puntuacion += 15.0
                coincide_depto = True
                motivos.append(f"Mismo depto ({docente.departamento})")

            # Afinidad de etapa educativa
            coincide_etapa = False
            if docente.etapa and profesor_ausente.etapa and \
               docente.etapa.strip().lower() == profesor_ausente.etapa.strip().lower():
                puntuacion += 10.0
                coincide_etapa = True
                motivos.append(f"Misma etapa ({docente.etapa})")

            # Información de carga (no afecta al orden de prelación diario estricto)
            if docente.sustituciones_realizadas == 0:
                motivos.append("0 sustituciones acumuladas")
            else:
                motivos.append(f"{docente.sustituciones_realizadas} sustitución(es) acumuladas")

            motivo_completo = " · ".join(motivos)

            candidatos_evaluados.append(SubstitutionCandidate(
                profesor=docente,
                tipo_disponibilidad=tipo_actividad,
                puntuacion=puntuacion,
                motivo=motivo_completo,
                es_recomendado=False,
                coincide_departamento=coincide_depto,
                coincide_etapa=coincide_etapa
            ))

        # Ordenar candidatos de mayor a menor puntuación
        candidatos_evaluados.sort(key=lambda c: c.puntuacion, reverse=True)

        # Marcar el mejor candidato como recomendado
        if candidatos_evaluados:
            candidatos_evaluados[0].es_recomendado = True

        return {
            "fecha": fecha_str,
            "periodo": slot.to_dict(),
            "profesor_ausente": profesor_ausente.to_dict(),
            "total_candidatos": len(candidatos_evaluados),
            "recomendado": candidatos_evaluados[0].to_dict() if candidatos_evaluados else None,
            "candidatos": [c.to_dict() for c in candidatos_evaluados],
            "no_disponibles": no_disponibles
        }
