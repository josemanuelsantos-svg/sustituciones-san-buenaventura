"""
Servidor Web Flask y API REST para el Sistema de Sustituciones Escolares.
"""

import os
import uuid
from datetime import datetime, date
from flask import Flask, render_template, request, jsonify, Response, send_file
from models import Teacher, TimeSlot, ScheduleItem, SubstitutionRecord, ActivityType
from database import Database
from engine import SubstitutionEngine
from calendar_service import CalendarService
from whatsapp_service import WhatsAppService
from email_service import EmailService
from sample_data import seed_database_if_empty

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["JSON_AS_ASCII"] = False

db = Database()
# Inicializar con datos si la base de datos está vacía
seed_database_if_empty(db, force=False)
engine = SubstitutionEngine(db)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/initial-data", methods=["GET"])
def get_initial_data():
    """Devuelve los datos maestros para inicializar la interfaz rápidamente."""
    teachers = db.get_teachers()
    slots = db.get_time_slots()
    substitutions = db.get_substitutions()[:10]  # Últimas 10
    
    # Calcular estadísticas de equidad
    stats = []
    for t in teachers:
        stats.append({
            "id": t.id,
            "nombre": t.nombre,
            "departamento": t.departamento,
            "etapa": t.etapa,
            "sustituciones": t.sustituciones_realizadas
        })
    stats.sort(key=lambda x: x["sustituciones"], reverse=True)

    today_str = date.today().isoformat()

    return jsonify({
        "hoy": today_str,
        "profesores": [t.to_dict() for t in teachers],
        "tramos": [s.to_dict() for s in slots],
        "ultimas_sustituciones": [s.to_dict() for s in substitutions],
        "estadisticas": stats,
        "tipos_actividad": [e.value for e in ActivityType]
    })

@app.route("/api/profesores", methods=["GET", "POST"])
def manage_teachers():
    if request.method == "POST":
        data = request.json or {}
        tid = data.get("id") or str(uuid.uuid4())[:8]
        teacher = Teacher(
            id=tid,
            nombre=data.get("nombre", "").strip(),
            telefono=data.get("telefono", "").strip(),
            email=data.get("email", "").strip(),
            departamento=data.get("departamento", "").strip(),
            etapa=data.get("etapa", "Secundaria"),
            activo=data.get("activo", True),
            sustituciones_realizadas=int(data.get("sustituciones_realizadas", 0))
        )
        teachers = [t for t in db.get_teachers() if t.id != tid]
        teachers.append(teacher)
        db.save_teachers(teachers)
        return jsonify({"success": True, "profesor": teacher.to_dict()})
    
    return jsonify([t.to_dict() for t in db.get_teachers()])

@app.route("/api/tramos", methods=["GET", "POST"])
def manage_slots():
    if request.method == "POST":
        data = request.json or []
        slots = [TimeSlot(**item) for item in data]
        db.save_time_slots(slots)
        return jsonify({"success": True, "tramos": [s.to_dict() for s in slots]})
    
    return jsonify([s.to_dict() for s in db.get_time_slots()])

@app.route("/api/horarios", methods=["GET"])
def get_horarios():
    profesor_id = request.args.get("profesor_id")
    if profesor_id:
        items = db.get_schedule_for_teacher(profesor_id)
    else:
        items = db.get_schedules()
    return jsonify([item.to_dict() for item in items])

@app.route("/api/actividad-docente", methods=["GET"])
def get_actividad_docente():
    """Devuelve la clase/actividad programada para un docente en un día y tramo concreto."""
    profesor_id = request.args.get("profesor_id")
    periodo_id = request.args.get("periodo_id")
    fecha_str = request.args.get("fecha")
    dia_str = request.args.get("dia_semana")

    if not profesor_id or not periodo_id:
        return jsonify({"encontrado": False}), 400

    if fecha_str:
        try:
            dia_semana = datetime.strptime(fecha_str, "%Y-%m-%d").weekday()
        except Exception:
            dia_semana = 0
    elif dia_str is not None:
        dia_semana = int(dia_str)
    else:
        dia_semana = 0

    item = db.get_slot_activity_for_teacher(profesor_id, dia_semana, periodo_id)
    if item:
        aula_val = item.aula or ""
        grupo_val = ""
        if any(kw in aula_val.upper() for kw in ["EP", "ESO", "INF", "BAC"]):
            grupo_val = aula_val
        return jsonify({
            "encontrado": True,
            "aula": aula_val,
            "curso_grupo": grupo_val,
            "materia": item.materia or "",
            "tipo_actividad": item.tipo_actividad,
            "descripcion": item.descripcion or ""
        })
    return jsonify({"encontrado": False})

@app.route("/api/horarios/guardar", methods=["POST"])
def save_horarios():
    """Guarda o actualiza los elementos de horario de un profesor o en lote."""
    data = request.json or {}
    profesor_id = data.get("profesor_id")
    items_data = data.get("items", [])

    if not profesor_id:
        return jsonify({"error": "profesor_id es requerido"}), 400

    current_schedules = [s for s in db.get_schedules() if s.profesor_id != profesor_id]
    for item in items_data:
        current_schedules.append(ScheduleItem(
            profesor_id=profesor_id,
            dia_semana=int(item["dia_semana"]),
            periodo_id=item["periodo_id"],
            tipo_actividad=item.get("tipo_actividad", ActivityType.LECTIVA),
            aula=item.get("aula", ""),
            materia=item.get("materia", ""),
            descripcion=item.get("descripcion", "")
        ))
    db.save_schedules(current_schedules)
    return jsonify({"success": True, "total": len(current_schedules)})

@app.route("/api/buscar-sustitutos", methods=["POST"])
def search_substitutes():
    """
    Busca y clasifica los candidatos disponibles para cubrir una ausencia específica.
    """
    data = request.json or {}
    fecha = data.get("fecha")
    periodo_id = data.get("periodo_id")
    profesor_ausente_id = data.get("profesor_ausente_id")
    materia = data.get("materia")
    aula = data.get("aula")

    if not fecha or not periodo_id or not profesor_ausente_id:
        return jsonify({"error": "fecha, periodo_id y profesor_ausente_id son obligatorios"}), 400

    try:
        resultado = engine.find_candidates(
            fecha_str=fecha,
            periodo_id=periodo_id,
            profesor_ausente_id=profesor_ausente_id,
            materia=materia,
            aula=aula
        )
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/asignar-sustitucion", methods=["POST"])
def assign_substitution():
    """
    Confirma y guarda una sustitución, generando los enlaces de Calendar y WhatsApp.
    """
    data = request.json or {}
    fecha = data.get("fecha")
    periodo_id = data.get("periodo_id")
    profesor_ausente_id = data.get("profesor_ausente_id")
    profesor_sustituto_id = data.get("profesor_sustituto_id")
    aula = data.get("aula", "Sin aula")
    curso_grupo = data.get("curso_grupo", "")
    materia = data.get("materia", "")
    observaciones = data.get("observaciones", "")

    if not all([fecha, periodo_id, profesor_ausente_id, profesor_sustituto_id]):
        return jsonify({"error": "Faltan campos obligatorios para la asignación"}), 400

    ausente = db.get_teacher(profesor_ausente_id)
    sustituto = db.get_teacher(profesor_sustituto_id)
    slot = db.get_time_slot(periodo_id)

    if not ausente or not sustituto or not slot:
        return jsonify({"error": "Entidades no encontradas en el sistema"}), 404

    try:
        fecha_dt = datetime.strptime(fecha, "%Y-%m-%d")
    except Exception:
        return jsonify({"error": "Formato de fecha inválido (debe ser YYYY-MM-DD)"}), 400

    if fecha_dt.weekday() >= 5:
        return jsonify({"error": "No se pueden registrar sustituciones en fines de semana."}), 400

    # Comprobar si el sustituto ya tiene otra sustitución en ese mismo tramo
    sustituciones_existentes = [
        s for s in db.get_substitutions()
        if s.fecha == fecha and s.periodo_id == periodo_id and s.estado != "CANCELADA"
    ]
    for s in sustituciones_existentes:
        if s.profesor_sustituto_id == sustituto.id:
            return jsonify({"error": f"{sustituto.nombre} ya tiene asignada otra sustitución en este mismo tramo ({s.aula})."}), 400
        if s.profesor_ausente_id == sustituto.id:
            return jsonify({"error": f"{sustituto.nombre} figura como ausente en esta misma fecha y hora."}), 400

    # Comprobar si el sustituto tiene clase lectiva
    actividad = db.get_slot_activity_for_teacher(sustituto.id, fecha_dt.weekday(), periodo_id)
    if actividad and actividad.tipo_actividad == ActivityType.LECTIVA:
        return jsonify({"error": f"{sustituto.nombre} tiene clase lectiva en este tramo ({actividad.materia or actividad.aula})."}), 400

    record_id = f"sub-{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:4]}"

    record = SubstitutionRecord(
        id=record_id,
        fecha=fecha,
        dia_semana=fecha_dt.weekday(),
        periodo_id=slot.id,
        periodo_nombre=slot.nombre,
        profesor_ausente_id=ausente.id,
        profesor_ausente_nombre=ausente.nombre,
        profesor_sustituto_id=sustituto.id,
        profesor_sustituto_nombre=sustituto.nombre,
        profesor_sustituto_telefono=sustituto.telefono,
        profesor_sustituto_email=sustituto.email,
        aula=aula,
        curso_grupo=curso_grupo,
        materia=materia,
        observaciones=observaciones,
        estado="ASIGNADA"
    )

    db.add_substitution(record)

    # Generar enlaces listos para usar
    calendar_url = CalendarService.generate_google_calendar_url(record, slot)
    calendar_view_url = CalendarService.get_calendar_view_url()
    whatsapp_url = WhatsAppService.generate_whatsapp_url(record, slot)
    whatsapp_text = WhatsAppService.format_substitution_message(record, slot)
    email_url = EmailService.generate_mailto_url(record, slot)
    email_body = EmailService.format_email_body(record, slot)

    return jsonify({
        "success": True,
        "record": record.to_dict(),
        "calendar_url": calendar_url,
        "calendar_view_url": calendar_view_url,
        "whatsapp_url": whatsapp_url,
        "whatsapp_text": whatsapp_text,
        "email_url": email_url,
        "email_body": email_body,
        "ics_url": f"/api/descargar-ics/{record.id}"
    })

@app.route("/api/sustituciones", methods=["GET"])
def list_substitutions():
    return jsonify([s.to_dict() for s in db.get_substitutions()])

@app.route("/api/sustituciones/<record_id>", methods=["DELETE"])
def delete_substitution(record_id):
    success = db.delete_substitution(record_id)
    if success:
        return jsonify({"success": True})
    return jsonify({"error": "Sustitución no encontrada"}), 404

@app.route("/api/descargar-ics/<record_id>")
def download_ics(record_id):
    record = db.get_substitution(record_id)
    if not record:
        return "Sustitución no encontrada", 404
    
    slot = db.get_time_slot(record.periodo_id)
    ics_content = CalendarService.generate_ics_file_content(record, slot)

    return Response(
        ics_content,
        mimetype="text/calendar",
        headers={"Content-Disposition": f"attachment; filename=sustitucion_{record.fecha}_{record.periodo_id}.ics"}
    )

@app.route("/api/importar-horarios", methods=["POST"])
def import_schedules():
    """
    Punto de entrada para cuando el usuario proporcione sus horarios.
    Acepta un JSON con profesores, tramos y asignaciones semanales.
    """
    data = request.json or {}
    
    # 1. Importar o actualizar profesores si vienen
    if "profesores" in data:
        teachers = [Teacher(**t) for t in data["profesores"]]
        db.save_teachers(teachers)

    # 2. Importar o actualizar tramos horarios si vienen
    if "tramos" in data:
        slots = [TimeSlot(**s) for s in data["tramos"]]
        db.save_time_slots(slots)

    # 3. Importar o actualizar matriz de horarios
    if "horarios" in data:
        schedules = [ScheduleItem(**h) for h in data["horarios"]]
        db.save_schedules(schedules)

    return jsonify({
        "success": True,
        "mensaje": "Datos importados correctamente",
        "total_profesores": len(db.get_teachers()),
        "total_tramos": len(db.get_time_slots()),
        "total_horarios": len(db.get_schedules())
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5055))
    print(f"Iniciando Sistema de Sustituciones Escolares en http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
