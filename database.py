"""
Gestor de persistencia y base de datos en JSON para el Sistema de Sustituciones.
"""

import os
import json
from typing import List, Optional, Dict, Any
from models import Teacher, TimeSlot, ScheduleItem, SubstitutionRecord, ActivityType

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

class Database:
    def __init__(self, data_dir: str = DATA_DIR):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.teachers_file = os.path.join(self.data_dir, "profesores.json")
        self.slots_file = os.path.join(self.data_dir, "tramos_horarios.json")
        self.schedules_file = os.path.join(self.data_dir, "horarios.json")
        self.substitutions_file = os.path.join(self.data_dir, "sustituciones.json")
        
        self._ensure_files()

    def _ensure_files(self):
        """Asegura que los archivos existan con estructuras válidas."""
        for path in [self.teachers_file, self.slots_file, self.schedules_file, self.substitutions_file]:
            if not os.path.exists(path):
                with open(path, "w", encoding="utf-8") as f:
                    json.dump([], f, indent=2, ensure_ascii=False)

    def _read_json(self, path: str) -> List[Dict[str, Any]]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _write_json(self, path: str, data: List[Dict[str, Any]]):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    # --- TRAMOS HORARIOS ---
    def get_time_slots(self) -> List[TimeSlot]:
        raw = self._read_json(self.slots_file)
        slots = [TimeSlot(**item) for item in raw]
        slots.sort(key=lambda s: s.orden)
        return slots

    def get_time_slot(self, slot_id: str) -> Optional[TimeSlot]:
        for slot in self.get_time_slots():
            if slot.id == slot_id:
                return slot
        return None

    def save_time_slots(self, slots: List[TimeSlot]):
        self._write_json(self.slots_file, [s.to_dict() for s in slots])

    # --- PROFESORES ---
    def get_teachers(self, active_only: bool = False) -> List[Teacher]:
        raw = self._read_json(self.teachers_file)
        teachers = [Teacher(**item) for item in raw]
        if active_only:
            teachers = [t for t in teachers if t.activo]
        teachers.sort(key=lambda t: t.nombre)
        return teachers

    def get_teacher(self, teacher_id: str) -> Optional[Teacher]:
        for t in self.get_teachers():
            if t.id == teacher_id:
                return t
        return None

    def save_teachers(self, teachers: List[Teacher]):
        self._write_json(self.teachers_file, [t.to_dict() for t in teachers])

    def update_teacher_substitution_count(self, teacher_id: str, delta: int = 1):
        teachers = self.get_teachers()
        for t in teachers:
            if t.id == teacher_id:
                t.sustituciones_realizadas = max(0, t.sustituciones_realizadas + delta)
                break
        self.save_teachers(teachers)

    # --- HORARIOS ---
    def get_schedules(self) -> List[ScheduleItem]:
        raw = self._read_json(self.schedules_file)
        return [ScheduleItem(**item) for item in raw]

    def save_schedules(self, schedules: List[ScheduleItem]):
        self._write_json(self.schedules_file, [s.to_dict() for s in schedules])

    def get_schedule_for_teacher(self, teacher_id: str) -> List[ScheduleItem]:
        return [s for s in self.get_schedules() if s.profesor_id == teacher_id]

    def get_slot_activity_for_teacher(self, teacher_id: str, dia_semana: int, periodo_id: str) -> Optional[ScheduleItem]:
        for s in self.get_schedules():
            if s.profesor_id == teacher_id and s.dia_semana == dia_semana and s.periodo_id == periodo_id:
                return s
        return None

    # --- SUSTITUCIONES ---
    def get_substitutions(self) -> List[SubstitutionRecord]:
        raw = self._read_json(self.substitutions_file)
        records = [SubstitutionRecord(**item) for item in raw]
        # Ordenar por fecha descendente
        records.sort(key=lambda r: r.creado_en, reverse=True)
        return records

    def get_substitution(self, record_id: str) -> Optional[SubstitutionRecord]:
        for r in self.get_substitutions():
            if r.id == record_id:
                return r
        return None

    def add_substitution(self, record: SubstitutionRecord) -> SubstitutionRecord:
        records = self.get_substitutions()
        records.insert(0, record)
        self._write_json(self.substitutions_file, [r.to_dict() for r in records])
        
        # Incrementar contador de sustituciones del profesor que sustituye
        self.update_teacher_substitution_count(record.profesor_sustituto_id, 1)
        return record

    def delete_substitution(self, record_id: str) -> bool:
        records = self.get_substitutions()
        to_delete = None
        for r in records:
            if r.id == record_id:
                to_delete = r
                break
        
        if to_delete:
            records.remove(to_delete)
            self._write_json(self.substitutions_file, [r.to_dict() for r in records])
            self.update_teacher_substitution_count(to_delete.profesor_sustituto_id, -1)
            return True
        return False
