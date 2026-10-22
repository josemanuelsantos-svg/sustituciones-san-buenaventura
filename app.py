"""
Servidor Web Flask y API REST para el Sistema de Sustituciones Escolares.
"""

import os
import uuid
from datetime import datetime, date
from flask import Flask, render_template, request, jsonify, Response, send_file, send_from_directory
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

@app.route("/favicon.ico")
def favicon():
    return send_from_directory(os.path.join(app.root_path, "static"), "favicon.ico", mimetype="image/vnd.microsoft.icon")

@app.route("/")
@app.route("/selector")
def selector():
    """Página de selección previa de usuario: Elena (Infantil) o Bea (Primaria)."""
    return render_template("selector.html")

@app.route("/primaria")
def portal_primaria():
    """Portal de gestión de sustituciones de Primaria (Bea)."""
    return render_template("index.html")

@app.route("/infantil")
def portal_infantil():
    """Portal de gestión de sustituciones de Infantil (Elena)."""
    return render_template("infantil.html")

@app.route("/api/initial-data", methods=["GET"])
def get_initial_data():
    """Devuelve los datos maestros para inicializar la interfaz rápidamente, filtrable por etapa."""
    etapa = request.args.get("etapa")
    teachers = db.get_teachers(etapa=etapa)
    slots = db.get_time_slots(etapa=etapa)
    all_subs = db.get_substitutions()
    if etapa:
        teacher_ids = {t.id for t in teachers}
        substitutions = [s for s in all_subs if s.profesor_ausente_id in teacher_ids or s.profesor_sustituto_id in teacher_ids][:10]
    else:
        substitutions = all_subs[:10]
    
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
    etapa = request.args.get("etapa")
    if profesor_id:
        items = db.get_schedule_for_teacher(profesor_id)
    else:
        items = db.get_schedules(etapa=etapa)
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

@app.route("/api/actividad-docente-multiple", methods=["POST"])
def get_actividad_docente_multiple():
    """Devuelve las clases/actividades programadas de un docente para varios tramos de un mismo día."""
    data = request.json or {}
    profesor_id = data.get("profesor_id")
    fecha_str = data.get("fecha")
    periodos = data.get("periodos", [])

    if not profesor_id or not fecha_str or not periodos:
        return jsonify({"actividades": []})

    try:
        dia_semana = datetime.strptime(fecha_str, "%Y-%m-%d").weekday()
    except Exception:
        dia_semana = 0

    slots_map = {s.id: s for s in db.get_time_slots()}
    actividades = []
    for pid in periodos:
        slot = slots_map.get(pid)
        item = db.get_slot_activity_for_teacher(profesor_id, dia_semana, pid)
        if item and item.tipo_actividad == ActivityType.LECTIVA:
            aula_val = item.aula or ""
            grupo_val = aula_val if any(kw in aula_val.upper() for kw in ["EP", "ESO", "INF", "BAC"]) else ""
            actividades.append({
                "periodo_id": pid,
                "periodo_nombre": slot.nombre if slot else pid,
                "hora_inicio": slot.hora_inicio if slot else "",
                "hora_fin": slot.hora_fin if slot else "",
                "tiene_clase_lectiva": True,
                "aula": aula_val,
                "curso_grupo": grupo_val,
                "materia": item.materia or "",
                "tipo_actividad": item.tipo_actividad
            })
        else:
            actividades.append({
                "periodo_id": pid,
                "periodo_nombre": slot.nombre if slot else pid,
                "hora_inicio": slot.hora_inicio if slot else "",
                "hora_fin": slot.hora_fin if slot else "",
                "tiene_clase_lectiva": False,
                "aula": "",
                "curso_grupo": "",
                "materia": "",
                "tipo_actividad": item.tipo_actividad if item else "DISPONIBLE"
            })

    return jsonify({"actividades": actividades})


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


@app.route("/api/buscar-sustitutos-multiple", methods=["POST"])
def search_substitutes_multiple():
    """
    Evalúa múltiples tramos horarios (o el día completo) para un profesor ausente,
    detectando su aula y asignatura en cada hora y devolviendo los candidatos idóneos por tramo.
    """
    data = request.json or {}
    fecha = data.get("fecha")
    periodos = data.get("periodos", [])
    profesor_ausente_id = data.get("profesor_ausente_id")
    overrides = data.get("overrides", {})

    if not fecha or not periodos or not profesor_ausente_id:
        return jsonify({"error": "fecha, periodos y profesor_ausente_id son obligatorios"}), 400

    ausente = db.get_teacher(profesor_ausente_id)
    if not ausente:
        return jsonify({"error": "Profesor ausente no encontrado"}), 404

    try:
        fecha_dt = datetime.strptime(fecha, "%Y-%m-%d")
    except Exception:
        return jsonify({"error": "Formato de fecha inválido (debe ser YYYY-MM-DD)"}), 400

    dia_semana = fecha_dt.weekday()
    if dia_semana >= 5:
        return jsonify({"error": "El día seleccionado es fin de semana (sin actividad lectiva)."}), 400

    slots_all = db.get_time_slots()
    slots_map = {s.id: s for s in slots_all}
    orden_ids = [s.id for s in slots_all]

    # Ordenar los periodos según el orden cronológico oficial
    periodos_ordenados = sorted(
        list(dict.fromkeys(periodos)),
        key=lambda x: orden_ids.index(x) if x in orden_ids else 999
    )

    # Sustituciones ya existentes ese día para ese profesor ausente
    sust_dia = [
        s for s in db.get_substitutions()
        if s.fecha == fecha and s.estado != "CANCELADA"
    ]

    tramos_evaluados = []
    for pid in periodos_ordenados:
        slot = slots_map.get(pid)
        if not slot:
            continue

        item = db.get_slot_activity_for_teacher(profesor_ausente_id, dia_semana, pid)
        ov = overrides.get(pid, {})

        tiene_clase = bool(item and item.tipo_actividad == ActivityType.LECTIVA)
        aula_auto = (item.aula or "") if tiene_clase else ""
        grupo_auto = aula_auto if any(kw in aula_auto.upper() for kw in ["EP", "ESO", "INF", "BAC"]) else ""
        materia_auto = (item.materia or "") if tiene_clase else ""

        aula_final = ov.get("aula") if ov.get("aula") is not None else aula_auto
        grupo_final = ov.get("curso_grupo") if ov.get("curso_grupo") is not None else grupo_auto
        materia_final = ov.get("materia") if ov.get("materia") is not None else materia_auto

        ya_asignada = next(
            (s.to_dict() for s in sust_dia if s.periodo_id == pid and s.profesor_ausente_id == profesor_ausente_id),
            None
        )

        evaluacion = engine.find_candidates(
            fecha_str=fecha,
            periodo_id=pid,
            profesor_ausente_id=profesor_ausente_id,
            materia=materia_final,
            aula=aula_final
        )

        tramos_evaluados.append({
            "periodo_id": pid,
            "periodo_nombre": slot.nombre,
            "hora_inicio": slot.hora_inicio,
            "hora_fin": slot.hora_fin,
            "tiene_clase_lectiva": tiene_clase,
            "tipo_actividad_ausente": item.tipo_actividad if item else "DISPONIBLE",
            "aula": aula_final,
            "curso_grupo": grupo_final,
            "materia": materia_final,
            "ya_asignada": ya_asignada,
            "recomendado": evaluacion.get("recomendado"),
            "candidatos": evaluacion.get("candidatos", []),
            "no_disponibles": evaluacion.get("no_disponibles", [])
        })

    return jsonify({
        "fecha": fecha,
        "dia_semana": dia_semana,
        "profesor_ausente": ausente.to_dict(),
        "tramos_evaluados": tramos_evaluados
    })


def _crear_registro_sustitucion(fecha, periodo_id, profesor_ausente_id, profesor_sustituto_id, aula, curso_grupo, materia, observaciones):
    """Función auxiliar que valida y registra una sustitución individual y genera sus enlaces."""
    ausente = db.get_teacher(profesor_ausente_id)
    sustituto = db.get_teacher(profesor_sustituto_id)
    slot = db.get_time_slot(periodo_id)

    if not ausente or not sustituto or not slot:
        raise ValueError("Entidades no encontradas en el sistema")

    try:
        fecha_dt = datetime.strptime(fecha, "%Y-%m-%d")
    except Exception:
        raise ValueError("Formato de fecha inválido (debe ser YYYY-MM-DD)")

    if fecha_dt.weekday() >= 5:
        raise ValueError("No se pueden registrar sustituciones en fines de semana.")

    # Comprobar si el sustituto ya tiene otra sustitución en ese mismo tramo
    sustituciones_existentes = [
        s for s in db.get_substitutions()
        if s.fecha == fecha and s.periodo_id == periodo_id and s.estado != "CANCELADA"
    ]
    for s in sustituciones_existentes:
        if s.profesor_sustituto_id == sustituto.id:
            raise ValueError(f"{sustituto.nombre} ya tiene asignada otra sustitución en {slot.nombre} ({s.aula}).")
        if s.profesor_ausente_id == sustituto.id:
            raise ValueError(f"{sustituto.nombre} figura como ausente en {slot.nombre}.")

    # Comprobar si el sustituto tiene clase lectiva
    actividad = db.get_slot_activity_for_teacher(sustituto.id, fecha_dt.weekday(), periodo_id)
    if actividad and actividad.tipo_actividad == ActivityType.LECTIVA:
        raise ValueError(f"{sustituto.nombre} tiene clase lectiva en {slot.nombre} ({actividad.materia or actividad.aula}).")

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
        aula=aula or "Aula asignada",
        curso_grupo=curso_grupo or "",
        materia=materia or "",
        observaciones=observaciones or "",
        estado="ASIGNADA"
    )

    db.add_substitution(record)

    calendar_url = CalendarService.generate_google_calendar_url(record, slot)
    calendar_view_url = CalendarService.get_calendar_view_url()
    whatsapp_url = WhatsAppService.generate_whatsapp_url(record, slot)
    whatsapp_text = WhatsAppService.format_substitution_message(record, slot)
    email_url = EmailService.generate_mailto_url(record, slot)
    email_body = EmailService.format_email_body(record, slot)

    return {
        "record": record.to_dict(),
        "hora_inicio": slot.hora_inicio,
        "hora_fin": slot.hora_fin,
        "calendar_url": calendar_url,
        "calendar_view_url": calendar_view_url,
        "whatsapp_url": whatsapp_url,
        "whatsapp_text": whatsapp_text,
        "email_url": email_url,
        "email_body": email_body,
        "ics_url": f"/api/descargar-ics/{record.id}"
    }


@app.route("/api/asignar-sustitucion", methods=["POST"])
def assign_substitution():
    """
    Confirma y guarda una sustitución individual, generando los enlaces de Calendar, Email y WhatsApp.
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

    try:
        res = _crear_registro_sustitucion(
            fecha=fecha,
            periodo_id=periodo_id,
            profesor_ausente_id=profesor_ausente_id,
            profesor_sustituto_id=profesor_sustituto_id,
            aula=aula,
            curso_grupo=curso_grupo,
            materia=materia,
            observaciones=observaciones
        )
        res["success"] = True
        return jsonify(res)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/asignar-sustituciones-multiple", methods=["POST"])
def assign_substitutions_multiple():
    """
    Confirma y guarda varias sustituciones al mismo tiempo (varias horas o día completo),
    devolviendo los enlaces individuales de Calendar y Correo para cada profesor sustituto.
    """
    data = request.json or {}
    fecha = data.get("fecha")
    profesor_ausente_id = data.get("profesor_ausente_id")
    observaciones_globales = data.get("observaciones", "")
    asignaciones = data.get("asignaciones", [])

    if not fecha or not profesor_ausente_id or not asignaciones:
        return jsonify({"error": "Faltan datos obligatorios para asignar las sustituciones."}), 400

    asignadas = []
    errores = []

    for item in asignaciones:
        periodo_id = item.get("periodo_id")
        profesor_sustituto_id = item.get("profesor_sustituto_id")
        if not periodo_id or not profesor_sustituto_id:
            continue

        aula = item.get("aula") or "Aula asignada"
        curso_grupo = item.get("curso_grupo") or ""
        materia = item.get("materia") or ""
        obs = item.get("observaciones") if item.get("observaciones") is not None else observaciones_globales

        try:
            creada = _crear_registro_sustitucion(
                fecha=fecha,
                periodo_id=periodo_id,
                profesor_ausente_id=profesor_ausente_id,
                profesor_sustituto_id=profesor_sustituto_id,
                aula=aula,
                curso_grupo=curso_grupo,
                materia=materia,
                observaciones=obs
            )
            asignadas.append(creada)
        except ValueError as e:
            errores.append({"periodo_id": periodo_id, "error": str(e)})

    if not asignadas and errores:
        return jsonify({"error": errores[0]["error"], "errores": errores}), 400

    return jsonify({
        "success": True,
        "asignadas": asignadas,
        "errores": errores,
        "calendar_view_url": CalendarService.get_calendar_view_url()
    })

@app.route("/api/sustituciones", methods=["GET"])
def list_substitutions():
    etapa = request.args.get("etapa")
    slots_map = {s.id: s for s in db.get_time_slots()}
    result = []
    teachers = db.get_teachers(etapa=etapa) if etapa else None
    teacher_ids = {t.id for t in teachers} if teachers else None

    for s in db.get_substitutions():
        if teacher_ids and (s.profesor_ausente_id not in teacher_ids and s.profesor_sustituto_id not in teacher_ids):
            continue
        d = s.to_dict()
        slot = slots_map.get(s.periodo_id)
        d["calendar_url"] = CalendarService.generate_google_calendar_url(s, slot)
        d["whatsapp_url"] = WhatsAppService.generate_whatsapp_url(s, slot)
        d["email_url"] = EmailService.generate_mailto_url(s, slot)
        result.append(d)
    return jsonify(result)

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
