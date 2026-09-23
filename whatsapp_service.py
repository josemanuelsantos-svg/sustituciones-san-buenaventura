"""
Servicio para formateo y envío de avisos de sustitución por WhatsApp.
"""

import re
import urllib.parse
from datetime import datetime
from typing import Optional
from models import SubstitutionRecord, TimeSlot

class WhatsAppService:
    @staticmethod
    def clean_phone_number(phone: str, default_country_code: str = "34") -> str:
        """
        Normaliza el número de teléfono para enlaces de WhatsApp (wa.me).
        Elimina espacios, guiones y signos más. Si no tiene prefijo, añade el código por defecto.
        """
        if not phone:
            return ""
        
        # Eliminar todo lo que no sea dígito
        digits = re.sub(r"\D", "", phone)
        
        # Si tiene 9 dígitos (formato estándar España 6xx xxx xxx), añadir prefijo 34
        if len(digits) == 9:
            return f"{default_country_code}{digits}"
        
        return digits

    @staticmethod
    def format_fecha_legible(fecha_str: str) -> str:
        try:
            dt = datetime.strptime(fecha_str, "%Y-%m-%d")
            dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
            meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
            return f"{dias[dt.weekday()]}, {dt.day} de {meses[dt.month - 1]} de {dt.year}"
        except Exception:
            return fecha_str

    @classmethod
    def format_substitution_message(cls, record: SubstitutionRecord, slot: Optional[TimeSlot] = None) -> str:
        """
        Crea el texto del mensaje con formato enriquecido para WhatsApp (*negrita*, emojis).
        """
        hora_str = ""
        if slot:
            hora_str = f" ({slot.hora_inicio} - {slot.hora_fin})"

        fecha_formateada = cls.format_fecha_legible(record.fecha)

        msg_lines = [
            "🔔 *AVISO DE SUSTITUCIÓN - COLEGIO*",
            f"Hola *{record.profesor_sustituto_nombre}*, tienes asignada la siguiente sustitución:",
            "",
            f"👤 *Profesor ausente:* {record.profesor_ausente_nombre}",
            f"📅 *Fecha:* {fecha_formateada}",
            f"⏰ *Horario:* {record.periodo_nombre}{hora_str}",
            f"📍 *Aula / Grupo:* {record.aula}" + (f" ({record.curso_grupo})" if record.curso_grupo else ""),
            f"📚 *Materia:* {record.materia or 'Por determinar'}",
        ]

        if record.observaciones and record.observaciones.strip():
            msg_lines.extend([
                "",
                f"📝 *Indicaciones del profesor:*",
                f"_{record.observaciones.strip()}_"
            ])

        msg_lines.extend([
            "",
            "¡Muchas gracias por tu colaboración!"
        ])

        return "\n".join(msg_lines)

    @classmethod
    def generate_whatsapp_url(cls, record: SubstitutionRecord, slot: Optional[TimeSlot] = None) -> str:
        """
        Genera el enlace universal `https://wa.me/<telefono>?text=...` que abre directamente la
        aplicación de WhatsApp o WhatsApp Web con el texto preescrito.
        """
        phone = cls.clean_phone_number(record.profesor_sustituto_telefono)
        text = cls.format_substitution_message(record, slot)
        
        encoded_text = urllib.parse.quote(text)
        
        if phone:
            return f"https://wa.me/{phone}?text={encoded_text}"
        else:
            # Enlace de compartir genérico si no hay teléfono registrado
            return f"https://api.whatsapp.com/send?text={encoded_text}"
