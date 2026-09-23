"""
Servicio para generación de eventos e integración con Google Calendar.
"""

import urllib.parse
from datetime import datetime
from typing import Optional
from models import SubstitutionRecord, TimeSlot

class CalendarService:
    @staticmethod
    def _parse_event_datetimes(fecha_str: str, hora_inicio_str: str, hora_fin_str: str):
        """
        Convierte fecha (YYYY-MM-DD) y horas (HH:MM) a objetos datetime y cadenas UTC/Locales compatibles con Google Calendar.
        """
        # Formato esperado: fecha "2026-09-16", hora "08:00"
        dt_start = datetime.strptime(f"{fecha_str} {hora_inicio_str}", "%Y-%m-%d %H:%M")
        dt_end = datetime.strptime(f"{fecha_str} {hora_fin_str}", "%Y-%m-%d %H:%M")
        
        # Formato Google Calendar: YYYYMMDDTHHmmSS
        fmt_google = "%Y%m%dT%H%M00"
        dates_param = f"{dt_start.strftime(fmt_google)}/{dt_end.strftime(fmt_google)}"
        
        return dt_start, dt_end, dates_param

    SANBUENAVENTURA_CALENDAR_ID = "sanbuenaventura.org_a3l1eg1rpu9a4si7ihp48gqjns@group.calendar.google.com"
    SANBUENAVENTURA_CALENDAR_CID = "c2FuYnVlbmF2ZW50dXJhLm9yZ19hM2wxZWcxcnB1OWA0c2k3aWhwNDhncWpuc0Bncm91cC5jYWxlbmRhci5nb29nbGUuY29t"
    SANBUENAVENTURA_CALENDAR_URL = f"https://calendar.google.com/calendar/u/0?cid={SANBUENAVENTURA_CALENDAR_CID}"

    @classmethod
    def get_calendar_view_url(cls) -> str:
        return cls.SANBUENAVENTURA_CALENDAR_URL

    @classmethod
    def generate_google_calendar_url(cls, record: SubstitutionRecord, slot: Optional[TimeSlot] = None) -> str:
        """
        Genera una URL directa (1-clic) para crear el evento en el calendario específico de San Buenaventura.
        """
        hora_ini = slot.hora_inicio if slot else "09:00"
        hora_fin = slot.hora_fin if slot else "10:00"

        try:
            _, _, dates_param = cls._parse_event_datetimes(record.fecha, hora_ini, hora_fin)
        except Exception:
            dates_param = ""

        # Título descriptivo
        summary = f"Sustitución: {record.profesor_sustituto_nombre} sustituye a {record.profesor_ausente_nombre}"
        if record.materia:
            summary += f" ({record.materia})"

        # Descripción con todos los datos clave
        details = (
            f"📋 DETALLES DE LA SUSTITUCIÓN - SAN BUENAVENTURA\n\n"
            f"👤 Profesor sustituto: {record.profesor_sustituto_nombre}\n"
            f"❌ Profesor ausente: {record.profesor_ausente_nombre}\n"
            f"⏰ Tramo horario: {record.periodo_nombre} ({hora_ini} - {hora_fin})\n"
            f"📍 Aula / Grupo: {record.aula} - {record.curso_grupo}\n"
            f"📚 Materia: {record.materia}\n"
        )
        if record.observaciones:
            details += f"\n📝 Indicaciones / Tareas:\n{record.observaciones}\n"
        
        details += f"\n📅 Calendario oficial: {cls.SANBUENAVENTURA_CALENDAR_URL}"

        location = f"{record.aula} ({record.curso_grupo})" if record.curso_grupo else record.aula

        params = {
            "action": "TEMPLATE",
            "text": summary,
            "dates": dates_param,
            "details": details,
            "location": location,
            "ctz": "Europe/Madrid",
            "src": cls.SANBUENAVENTURA_CALENDAR_ID
        }

        query_string = urllib.parse.urlencode(params)
        return f"https://calendar.google.com/calendar/render?{query_string}"

    @classmethod
    def generate_ics_file_content(cls, record: SubstitutionRecord, slot: Optional[TimeSlot] = None) -> str:
        """
        Genera el contenido de un archivo .ics estándar para importar en Google Calendar, Outlook o Apple Calendar.
        """
        hora_ini = slot.hora_inicio if slot else "09:00"
        hora_fin = slot.hora_fin if slot else "10:00"

        dt_start, dt_end, _ = cls._parse_event_datetimes(record.fecha, hora_ini, hora_fin)
        
        dt_stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        dt_start_fmt = dt_start.strftime("%Y%m%dT%H%M%S")
        dt_end_fmt = dt_end.strftime("%Y%m%dT%H%M%S")

        summary = f"Sustitución: {record.profesor_sustituto_nombre} a {record.profesor_ausente_nombre}"
        description = (
            f"Profesor ausente: {record.profesor_ausente_nombre}\\n"
            f"Profesor sustituto: {record.profesor_sustituto_nombre}\\n"
            f"Aula: {record.aula} ({record.curso_grupo})\\n"
            f"Materia: {record.materia}\\n"
            f"Notas: {record.observaciones}"
        )
        location = f"{record.aula} ({record.curso_grupo})"

        ics_content = (
            "BEGIN:VCALENDAR\r\n"
            "VERSION:2.0\r\n"
            "PRODID:-//Colegio//Sistema Sustituciones v1.0//ES\r\n"
            "CALSCALE:GREGORIAN\r\n"
            "METHOD:PUBLISH\r\n"
            "BEGIN:VEVENT\r\n"
            f"UID:sustitucion-{record.id}@colegio.es\r\n"
            f"DTSTAMP:{dt_stamp}\r\n"
            f"DTSTART:{dt_start_fmt}\r\n"
            f"DTEND:{dt_end_fmt}\r\n"
            f"SUMMARY:{summary}\r\n"
            f"DESCRIPTION:{description}\r\n"
            f"LOCATION:{location}\r\n"
            "STATUS:CONFIRMED\r\n"
            "END:VEVENT\r\n"
            "END:VCALENDAR\r\n"
        )
        return ics_content
