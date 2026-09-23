"""
Servicio para formateo y generación de enlaces de aviso por Email institucional.
"""

import urllib.parse
from datetime import datetime
from typing import Optional
from models import SubstitutionRecord, TimeSlot

class EmailService:
    @staticmethod
    def format_fecha_legible(fecha_str: str) -> str:
        try:
            dt = datetime.strptime(fecha_str, "%Y-%m-%d")
            dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
            meses = [
                "enero", "febrero", "marzo", "abril", "mayo", "junio",
                "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
            ]
            return f"{dias[dt.weekday()]}, {dt.day} de {meses[dt.month - 1]} de {dt.year}"
        except Exception:
            return fecha_str

    @classmethod
    def format_email_subject(cls, record: SubstitutionRecord) -> str:
        return f"Aviso de Sustitución - {record.periodo_nombre} ({record.fecha})"

    @classmethod
    def format_email_body(cls, record: SubstitutionRecord, slot: Optional[TimeSlot] = None) -> str:
        hora_str = f" ({slot.hora_inicio} - {slot.hora_fin})" if slot else ""
        fecha_legible = cls.format_fecha_legible(record.fecha)
        aula_grupo = f"{record.aula}" + (f" ({record.curso_grupo})" if record.curso_grupo else "")

        body_lines = [
            f"Hola {record.profesor_sustituto_nombre},",
            "",
            "Te comunicamos que tienes asignada la siguiente sustitución escolar:",
            "",
            f"• Profesor ausente: {record.profesor_ausente_nombre}",
            f"• Fecha: {fecha_legible}",
            f"• Horario: {record.periodo_nombre}{hora_str}",
            f"• Aula / Grupo: {aula_grupo}",
            f"• Materia: {record.materia or 'Por determinar'}",
        ]

        if record.observaciones and record.observaciones.strip():
            body_lines.extend([
                "",
                f"• Indicaciones del profesor:",
                f"  {record.observaciones.strip()}"
            ])

        body_lines.extend([
            "",
            "Muchas gracias por tu colaboración.",
            "",
            "Atentamente,",
            "Jefatura de Estudios / Coordinación",
            "Colegio San Buenaventura"
        ])

        return "\n".join(body_lines)

    @classmethod
    def generate_mailto_url(cls, record: SubstitutionRecord, slot: Optional[TimeSlot] = None) -> str:
        email = record.profesor_sustituto_email or ""
        subject = cls.format_email_subject(record)
        body = cls.format_email_body(record, slot)

        params = {
            "subject": subject,
            "body": body
        }
        query_string = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
        return f"mailto:{email}?{query_string}"
