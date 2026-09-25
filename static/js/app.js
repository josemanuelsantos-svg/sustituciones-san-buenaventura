/**
 * Lógica de cliente para el Sistema de Sustituciones Escolares
 */

// Estado global de la aplicación
let appState = {
  profesores: [],
  tramos: [],
  horarios: [],
  sustituciones: [],
  estadisticas: [],
  ultimoResultadoBusqueda: null,
  ultimaSustitucionAsignada: null
};

const DIAS_SEMANA = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"];

document.addEventListener("DOMContentLoaded", () => {
  inicializarFecha();
  cargarDatosIniciales();
  configurarListeners();
});

function switchTab(tabId) {
  document.querySelectorAll(".tab-content").forEach(el => el.classList.add("hidden"));
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.classList.remove("bg-indigo-600", "text-white", "shadow");
    btn.classList.add("text-indigo-200");
  });

  const targetTab = document.getElementById(`tab-${tabId}`);
  const targetBtn = document.getElementById(`tab-btn-${tabId}`);

  if (targetTab) targetTab.classList.remove("hidden");
  if (targetBtn) {
    targetBtn.classList.add("bg-indigo-600", "text-white", "shadow");
    targetBtn.classList.remove("text-indigo-200");
  }

  if (tabId === "horarios") {
    cargarHorariosSemana();
  }
}

const NOMBRES_MESES = [
  "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
];

let calVisual = {
  ano: new Date().getFullYear(),
  mes: new Date().getMonth(),
  anoSel: new Date().getFullYear(),
  mesSel: new Date().getMonth(),
  diaSel: new Date().getDate()
};

function inicializarFecha() {
  const hoy = new Date();
  
  // Si hoy es fin de semana, por defecto apuntar al próximo lunes
  let fechaDefecto = new Date(hoy);
  if (hoy.getDay() === 0) fechaDefecto.setDate(hoy.getDate() + 1); // Domingo -> Lunes
  if (hoy.getDay() === 6) fechaDefecto.setDate(hoy.getDate() + 2); // Sábado -> Lunes

  calVisual.ano = fechaDefecto.getFullYear();
  calVisual.mes = fechaDefecto.getMonth();
  calVisual.anoSel = fechaDefecto.getFullYear();
  calVisual.mesSel = fechaDefecto.getMonth();
  calVisual.diaSel = fechaDefecto.getDate();

  setInputValueFromDate(fechaDefecto);
  renderCalendarioMensual();
}

function setFechaRelativa(offsetDias) {
  const d = new Date();
  d.setDate(d.getDate() + offsetDias);
  calVisual.ano = d.getFullYear();
  calVisual.mes = d.getMonth();
  calVisual.anoSel = d.getFullYear();
  calVisual.mesSel = d.getMonth();
  calVisual.diaSel = d.getDate();
  setInputValueFromDate(d);
  renderCalendarioMensual();
}

function setDiaSemanaActual(diaTargetIndex) { // 0=Lunes, 1=Martes, 2=Mié, 3=Jue, 4=Vie
  const d = new Date();
  const currentJsDay = d.getDay();
  const currentSchoolDay = (currentJsDay + 6) % 7; // 0=Lunes, ..., 6=Domingo
  const diff = diaTargetIndex - currentSchoolDay;
  d.setDate(d.getDate() + diff);
  calVisual.ano = d.getFullYear();
  calVisual.mes = d.getMonth();
  calVisual.anoSel = d.getFullYear();
  calVisual.mesSel = d.getMonth();
  calVisual.diaSel = d.getDate();
  setInputValueFromDate(d);
  renderCalendarioMensual();
}

function irAHoy() {
  setFechaRelativa(0);
}

function cambiarMes(delta) {
  calVisual.mes += delta;
  if (calVisual.mes < 0) {
    calVisual.mes = 11;
    calVisual.ano--;
  } else if (calVisual.mes > 11) {
    calVisual.mes = 0;
    calVisual.ano++;
  }
  renderCalendarioMensual();
}

function seleccionarDiaCalendario(y, m, d) {
  calVisual.anoSel = y;
  calVisual.mesSel = m;
  calVisual.diaSel = d;
  calVisual.ano = y;
  calVisual.mes = m;

  const dateObj = new Date(y, m, d);
  setInputValueFromDate(dateObj);
  renderCalendarioMensual();
}

function renderCalendarioMensual() {
  const mesLabel = document.getElementById("cal-mes-ano");
  const grid = document.getElementById("cal-dias-grid");
  const resumenLabel = document.getElementById("cal-fecha-seleccionada");

  if (!grid || !mesLabel) return;

  mesLabel.textContent = `${NOMBRES_MESES[calVisual.mes]} ${calVisual.ano}`;

  grid.innerHTML = "";

  const hoy = new Date();
  const hoyY = hoy.getFullYear();
  const hoyM = hoy.getMonth();
  const hoyD = hoy.getDate();

  // Primer día de este mes: 0=Domingo, ..., 6=Sábado -> convertir a 0=Lunes, 6=Domingo
  const primerDiaSemana = (new Date(calVisual.ano, calVisual.mes, 1).getDay() + 6) % 7;
  const totalDiasMes = new Date(calVisual.ano, calVisual.mes + 1, 0).getDate();
  const totalDiasMesAnt = new Date(calVisual.ano, calVisual.mes, 0).getDate();

  // Días del mes anterior (padding inicial)
  for (let i = primerDiaSemana - 1; i >= 0; i--) {
    const diaNum = totalDiasMesAnt - i;
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "py-1.5 rounded-lg text-slate-300 hover:text-slate-500 text-[11px] transition";
    btn.textContent = diaNum;
    const prevM = calVisual.mes === 0 ? 11 : calVisual.mes - 1;
    const prevY = calVisual.mes === 0 ? calVisual.ano - 1 : calVisual.ano;
    btn.onclick = () => seleccionarDiaCalendario(prevY, prevM, diaNum);
    grid.appendChild(btn);
  }

  // Días del mes actual
  for (let d = 1; d <= totalDiasMes; d++) {
    const btn = document.createElement("button");
    btn.type = "button";
    const diaSemana = (new Date(calVisual.ano, calVisual.mes, d).getDay() + 6) % 7;
    const esFinDeSemana = diaSemana >= 5;

    const esSeleccionado = (calVisual.ano === calVisual.anoSel && 
                            calVisual.mes === calVisual.mesSel && 
                            d === calVisual.diaSel);
    const esHoy = (calVisual.ano === hoyY && calVisual.mes === hoyM && d === hoyD);

    let classes = "py-1.5 rounded-lg text-xs font-medium transition flex items-center justify-center ";

    if (esSeleccionado) {
      classes += "bg-indigo-600 text-white font-bold shadow-sm scale-105 z-10 ";
    } else if (esHoy) {
      classes += "border border-indigo-400 text-indigo-700 font-bold bg-indigo-50/50 hover:bg-indigo-100 ";
    } else if (esFinDeSemana) {
      classes += "text-slate-300 hover:bg-slate-100 ";
    } else {
      classes += "text-slate-700 hover:bg-indigo-100/70 hover:text-indigo-900 ";
    }

    btn.className = classes;
    btn.textContent = d;
    btn.onclick = () => seleccionarDiaCalendario(calVisual.ano, calVisual.mes, d);
    grid.appendChild(btn);
  }

  // Días del mes siguiente (padding final hasta completar semanas de 7)
  const celdasUsadas = primerDiaSemana + totalDiasMes;
  const celdasRestantes = (7 - (celdasUsadas % 7)) % 7;
  for (let d = 1; d <= celdasRestantes; d++) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "py-1.5 rounded-lg text-slate-300 hover:text-slate-500 text-[11px] transition";
    btn.textContent = d;
    const nextM = calVisual.mes === 11 ? 0 : calVisual.mes + 1;
    const nextY = calVisual.mes === 11 ? calVisual.ano + 1 : calVisual.ano;
    btn.onclick = () => seleccionarDiaCalendario(nextY, nextM, d);
    grid.appendChild(btn);
  }

  if (resumenLabel) {
    const fechaSelStr = `${calVisual.anoSel}-${String(calVisual.mesSel + 1).padStart(2, '0')}-${String(calVisual.diaSel).padStart(2, '0')}`;
    resumenLabel.textContent = formatFechaEsp(fechaSelStr);
  }
}

function setInputValueFromDate(d) {
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  const input = document.getElementById("input-fecha");
  if (input) {
    input.value = `${yyyy}-${mm}-${dd}`;
    actualizarEtiquetaDiaSemana();
    consultarActividadProgramada();
  }
}

function actualizarEtiquetaDiaSemana() {
  const inputFecha = document.getElementById("input-fecha");
  const labelDia = document.getElementById("label-dia-semana");
  if (!inputFecha || !labelDia || !inputFecha.value) return;

  const partes = inputFecha.value.split("-");
  if (partes.length !== 3) return;

  const y = parseInt(partes[0], 10);
  const m = parseInt(partes[1], 10) - 1;
  const d = parseInt(partes[2], 10);
  const fechaObj = new Date(y, m, d);

  const jsDay = fechaObj.getDay();
  const diaSemanaIndex = (jsDay + 6) % 7; // 0=Lunes, 4=Viernes, 5=Sábado, 6=Domingo
  
  const nombreDia = DIAS_SEMANA[diaSemanaIndex] || "";
  
  if (diaSemanaIndex >= 5) {
    labelDia.textContent = `⚠️ ${nombreDia} (Sin clase)`;
    labelDia.className = "text-xs font-bold text-amber-800 bg-amber-100 px-2.5 py-0.5 rounded-full border border-amber-300";
  } else {
    labelDia.textContent = `📅 ${nombreDia}`;
    labelDia.className = "text-xs font-bold text-indigo-700 bg-indigo-100 px-2.5 py-0.5 rounded-full border border-indigo-200";
  }
}

function formatFechaEsp(fechaStr) {
  if (!fechaStr) return "";
  const partes = fechaStr.split("-");
  if (partes.length !== 3) return fechaStr;
  const y = parseInt(partes[0], 10);
  const m = parseInt(partes[1], 10) - 1;
  const d = parseInt(partes[2], 10);
  const fechaObj = new Date(y, m, d);
  const jsDay = fechaObj.getDay();
  const diaSemanaIndex = (jsDay + 6) % 7;
  const diaNombre = DIAS_SEMANA[diaSemanaIndex] || "";
  return `${diaNombre} ${partes[2]}/${partes[1]}/${partes[0]}`;
}

function sincronizarFechaDesdeInput() {
  const inputFecha = document.getElementById("input-fecha");
  if (!inputFecha || !inputFecha.value) return;

  const partes = inputFecha.value.split("-");
  if (partes.length !== 3) return;

  const y = parseInt(partes[0], 10);
  const m = parseInt(partes[1], 10) - 1;
  const d = parseInt(partes[2], 10);

  calVisual.anoSel = y;
  calVisual.mesSel = m;
  calVisual.diaSel = d;
  calVisual.ano = y;
  calVisual.mes = m;

  renderCalendarioMensual();
  actualizarEtiquetaDiaSemana();
  consultarActividadProgramada();
}

function limpiarCamposActividad() {
  const inAula = document.getElementById("input-aula");
  const inGrupo = document.getElementById("input-grupo");
  const inMat = document.getElementById("input-materia");
  if (inAula) inAula.value = "";
  if (inGrupo) inGrupo.value = "";
  if (inMat) inMat.value = "";
}

function configurarListeners() {
  const inputFecha = document.getElementById("input-fecha");
  inputFecha.addEventListener("change", sincronizarFechaDesdeInput);
  inputFecha.addEventListener("input", sincronizarFechaDesdeInput);

  document.getElementById("select-tramo").addEventListener("change", consultarActividadProgramada);
  document.getElementById("select-profesor-ausente").addEventListener("change", consultarActividadProgramada);
}

async function consultarActividadProgramada() {
  const fecha = document.getElementById("input-fecha").value;
  const periodo_id = document.getElementById("select-tramo").value;
  const profesor_id = document.getElementById("select-profesor-ausente").value;

  if (!fecha || !periodo_id || !profesor_id) {
    limpiarCamposActividad();
    return;
  }

  try {
    const res = await fetch(`/api/actividad-docente?profesor_id=${profesor_id}&periodo_id=${periodo_id}&fecha=${fecha}`);
    const data = await res.json();
    if (data && data.encontrado) {
      document.getElementById("input-aula").value = data.aula || "";
      document.getElementById("input-grupo").value = data.curso_grupo || (data.aula && data.aula.includes("EP") ? data.aula : "");
      document.getElementById("input-materia").value = data.materia || "";
    } else {
      limpiarCamposActividad();
    }
  } catch (e) {
    console.error("Error al consultar actividad programada:", e);
  }
}

async function cargarDatosIniciales() {
  try {
    const res = await fetch("/api/initial-data");
    const data = await res.json();

    appState.profesores = data.profesores || [];
    appState.tramos = data.tramos || [];
    appState.sustituciones = data.ultimas_sustituciones || [];
    appState.estadisticas = data.estadisticas || [];

    poblarSelects();
    renderEstadisticas();
    renderHistorial();
  } catch (err) {
    console.error("Error al cargar datos maestros:", err);
  }
}

function poblarSelects() {
  // 1. Select de tramos
  const selectTramo = document.getElementById("select-tramo");
  selectTramo.innerHTML = '<option value="">-- Selecciona hora / tramo --</option>';
  appState.tramos.forEach(t => {
    const option = document.createElement("option");
    option.value = t.id;
    option.textContent = `${t.nombre} (${t.hora_inicio} - ${t.hora_fin})${t.es_recreo ? ' [Recreo]' : ''}`;
    selectTramo.appendChild(option);
  });

  // 2. Select de profesores ausentes
  const selectAusente = document.getElementById("select-profesor-ausente");
  selectAusente.innerHTML = '<option value="">-- Selecciona profesor ausente --</option>';
  
  // 3. Select de filtro de profesor en cuadrante
  const selectFiltro = document.getElementById("select-filtro-profesor");
  selectFiltro.innerHTML = '<option value="todos">-- Vista global (Todos los profesores) --</option>';

  appState.profesores.forEach(p => {
    const optAusente = document.createElement("option");
    optAusente.value = p.id;
    optAusente.textContent = `${p.nombre} (${p.departamento} - ${p.etapa})`;
    selectAusente.appendChild(optAusente);

    const optFiltro = document.createElement("option");
    optFiltro.value = p.id;
    optFiltro.textContent = `${p.nombre} (${p.departamento})`;
    selectFiltro.appendChild(optFiltro);
  });
}

// ===============================================
// BÚSQUEDA Y EVALUACIÓN DE CANDIDATOS
// ===============================================

async function buscarSustitutos() {
  const fecha = document.getElementById("input-fecha").value;
  const periodo_id = document.getElementById("select-tramo").value;
  const profesor_ausente_id = document.getElementById("select-profesor-ausente").value;
  const aula = document.getElementById("input-aula").value;
  const curso_grupo = document.getElementById("input-grupo").value;
  const materia = document.getElementById("input-materia").value;
  const observaciones = document.getElementById("input-observaciones").value;

  if (!fecha || !periodo_id || !profesor_ausente_id) {
    alert("Por favor completa al menos la fecha, la hora y el profesor ausente.");
    return;
  }

  // Comprobar si es fin de semana
  const partesF = fecha.split("-");
  if (partesF.length === 3) {
    const dObj = new Date(parseInt(partesF[0], 10), parseInt(partesF[1], 10) - 1, parseInt(partesF[2], 10));
    const diaSem = (dObj.getDay() + 6) % 7;
    if (diaSem >= 5) {
      alert("⚠️ El día seleccionado corresponde a fin de semana (sin actividad escolar). Por favor selecciona un día lectivo de lunes a viernes.");
      return;
    }
  }

  const btnBuscar = document.getElementById("btn-buscar");
  if (btnBuscar) {
    btnBuscar.disabled = true;
    btnBuscar.classList.add("opacity-75", "cursor-not-allowed");
  }

  // Ocultar paneles y mostrar spinner
  document.getElementById("panel-inicial").classList.add("hidden");
  document.getElementById("panel-confirmacion").classList.add("hidden");
  document.getElementById("panel-resultados").classList.add("hidden");
  document.getElementById("panel-cargando").classList.remove("hidden");

  try {
    const res = await fetch("/api/buscar-sustitutos", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        fecha,
        periodo_id,
        profesor_ausente_id,
        materia,
        aula
      })
    });

    const data = await res.json();
    document.getElementById("panel-cargando").classList.add("hidden");

    if (data.error) {
      alert("Aviso: " + data.error);
      document.getElementById("panel-inicial").classList.remove("hidden");
      return;
    }

    appState.ultimoResultadoBusqueda = data;
    renderResultadosBusqueda(data);

  } catch (err) {
    document.getElementById("panel-cargando").classList.add("hidden");
    alert("Error de conexión al buscar sustitutos");
    console.error(err);
  } finally {
    if (btnBuscar) {
      btnBuscar.disabled = false;
      btnBuscar.classList.remove("opacity-75", "cursor-not-allowed");
    }
  }
}

function renderResultadosBusqueda(data) {
  const panelResultados = document.getElementById("panel-resultados");
  panelResultados.classList.remove("hidden");

  const rec = data.recomendado;

  if (!rec) {
    document.getElementById("card-recomendado").classList.add("hidden");
    document.getElementById("lista-alternativas").innerHTML = `
      <div class="p-4 bg-amber-50 border border-amber-200 rounded-xl text-amber-800 text-xs">
        ⚠️ No se han encontrado profesores disponibles en guardia o libres en este tramo.
      </div>
    `;
    renderNoDisponibles(data.no_disponibles);
    return;
  }

  // Tarjeta recomendada
  document.getElementById("card-recomendado").classList.remove("hidden");
  document.getElementById("rec-nombre").textContent = rec.profesor.nombre;
  document.getElementById("rec-depto").querySelector(".val").textContent = rec.profesor.departamento;
  document.getElementById("rec-etapa").querySelector(".val").textContent = rec.profesor.etapa;
  document.getElementById("rec-telefono").querySelector(".val").textContent = rec.profesor.telefono || "Sin teléfono";
  document.getElementById("rec-motivo").textContent = rec.motivo;
  document.getElementById("rec-puntuacion").textContent = `Puntos: ${rec.puntuacion.toFixed(0)}`;
  
  const dispoLabel = rec.tipo_disponibilidad === "GUARDIA_AULA" ? "🛡️ En Guardia de Aula" : "🟢 Hora Libre / Complementaria";
  document.getElementById("rec-disponibilidad").textContent = dispoLabel;

  // Alternativas
  const alternativas = (data.candidatos || []).slice(1);
  document.getElementById("count-alternativas").textContent = alternativas.length;
  
  const listaAlt = document.getElementById("lista-alternativas");
  listaAlt.innerHTML = "";

  if (alternativas.length === 0) {
    listaAlt.innerHTML = `<p class="text-xs text-slate-400 italic py-2">No hay más profesores disponibles en este tramo.</p>`;
  } else {
    alternativas.forEach(c => {
      const card = document.createElement("div");
      card.className = "flex items-center justify-between p-3 rounded-xl border border-slate-200 hover:border-indigo-300 hover:bg-slate-50 transition";
      
      const badgeGuardia = c.tipo_disponibilidad === "GUARDIA_AULA" 
        ? `<span class="bg-emerald-100 text-emerald-800 text-[10px] font-semibold px-2 py-0.5 rounded">Guardia Aula</span>`
        : `<span class="bg-blue-100 text-blue-800 text-[10px] font-semibold px-2 py-0.5 rounded">Disponible</span>`;

      card.innerHTML = `
        <div>
          <div class="flex items-center gap-2">
            <span class="font-bold text-slate-800 text-xs">${c.profesor.nombre}</span>
            ${badgeGuardia}
          </div>
          <div class="text-[11px] text-slate-500 mt-0.5">${c.motivo}</div>
        </div>
        <button onclick="asignarCandidato('${c.profesor.id}')" class="py-1.5 px-3 bg-indigo-50 hover:bg-indigo-600 hover:text-white text-indigo-700 font-semibold text-xs rounded-lg transition border border-indigo-200 hover:border-indigo-600">
          Elegir este
        </button>
      `;
      listaAlt.appendChild(card);
    });
  }

  // No disponibles
  renderNoDisponibles(data.no_disponibles);
}

function renderNoDisponibles(noDisponibles = []) {
  document.getElementById("count-nodisponibles").textContent = noDisponibles.length;
  const listaND = document.getElementById("lista-nodisponibles");
  listaND.innerHTML = "";

  noDisponibles.forEach(nd => {
    const item = document.createElement("div");
    item.className = "py-1.5 flex items-center justify-between text-xs";
    item.innerHTML = `
      <span class="font-medium text-slate-700">${nd.profesor_nombre}</span>
      <span class="text-slate-400 text-[11px]">${nd.motivo}</span>
    `;
    listaND.appendChild(item);
  });
}

function asignarRecomendado() {
  if (appState.ultimoResultadoBusqueda && appState.ultimoResultadoBusqueda.recomendado) {
    asignarCandidato(appState.ultimoResultadoBusqueda.recomendado.profesor.id);
  }
}

// ===============================================
// ASIGNACIÓN, CALENDAR Y WHATSAPP
// ===============================================

async function asignarCandidato(profesorSustitutoId, btnTrigger = null) {
  const fecha = document.getElementById("input-fecha").value;
  const periodo_id = document.getElementById("select-tramo").value;
  const profesor_ausente_id = document.getElementById("select-profesor-ausente").value;
  const aula = document.getElementById("input-aula").value || "Aula asignada";
  const curso_grupo = document.getElementById("input-grupo").value;
  const materia = document.getElementById("input-materia").value;
  const observaciones = document.getElementById("input-observaciones").value;

  if (btnTrigger) {
    btnTrigger.disabled = true;
    btnTrigger.classList.add("opacity-70", "cursor-not-allowed");
  }

  try {
    const res = await fetch("/api/asignar-sustitucion", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        fecha,
        periodo_id,
        profesor_ausente_id,
        profesor_sustituto_id: profesorSustitutoId,
        aula,
        curso_grupo,
        materia,
        observaciones
      })
    });

    const data = await res.json();
    if (data.error) {
      alert("Aviso: " + data.error);
      if (btnTrigger) {
        btnTrigger.disabled = false;
        btnTrigger.classList.remove("opacity-70", "cursor-not-allowed");
      }
      return;
    }

    appState.ultimaSustitucionAsignada = data;

    // Mostrar panel de éxito
    document.getElementById("panel-resultados").classList.add("hidden");
    const confPanel = document.getElementById("panel-confirmacion");
    confPanel.classList.remove("hidden");

    const r = data.record;
    document.getElementById("conf-resumen").textContent = 
      `${r.profesor_sustituto_nombre} sustituirá a ${r.profesor_ausente_nombre} el ${formatFechaEsp(r.fecha)} en ${r.periodo_nombre} (${r.aula}).`;

    // Configurar enlace Google Calendar
    document.getElementById("btn-calendar").href = data.calendar_url;

    // Configurar enlace WhatsApp
    document.getElementById("btn-whatsapp").href = data.whatsapp_url;

    // Configurar enlace Email
    const btnEmail = document.getElementById("btn-email");
    if (btnEmail) {
      btnEmail.href = data.email_url || "#";
      const lblEmail = document.getElementById("btn-email-sub");
      if (lblEmail && r.profesor_sustituto_email) {
        lblEmail.textContent = r.profesor_sustituto_email;
      }
    }

    // Configurar descarga .ics
    document.getElementById("btn-ics").href = data.ics_url;

    // Mostrar vista previa mensaje WhatsApp
    document.getElementById("pre-whatsapp").textContent = data.whatsapp_text;

    // Recargar historial y estadísticas
    cargarDatosIniciales();

  } catch (err) {
    alert("Error de red al registrar la sustitución");
    console.error(err);
    if (btnTrigger) {
      btnTrigger.disabled = false;
      btnTrigger.classList.remove("opacity-70", "cursor-not-allowed");
    }
  }
}

function nuevaSustitucion() {
  document.getElementById("panel-confirmacion").classList.add("hidden");
  document.getElementById("panel-inicial").classList.remove("hidden");
  
  // Mantener la fecha seleccionada para comodidad del usuario
  const fechaActual = document.getElementById("input-fecha").value;
  
  document.getElementById("select-tramo").value = "";
  document.getElementById("select-profesor-ausente").value = "";
  limpiarCamposActividad();
  document.getElementById("input-observaciones").value = "";

  if (fechaActual) {
    document.getElementById("input-fecha").value = fechaActual;
    actualizarEtiquetaDiaSemana();
  }
}

function copiarMensajeWA() {
  const texto = document.getElementById("pre-whatsapp").textContent;
  navigator.clipboard.writeText(texto).then(() => {
    alert("¡Mensaje copiado al portapapeles! Listo para pegar en WhatsApp.");
  });
}

// ===============================================
// VISOR DE HORARIOS Y CUADRANTE
// ===============================================

async function cargarHorariosSemana() {
  try {
    const res = await fetch("/api/horarios");
    appState.horarios = await res.json();
    renderHorarioProfesor("todos");
  } catch (err) {
    console.error("Error al cargar horarios:", err);
  }
}

function renderHorarioProfesor(filtroProfesorId) {
  const tbody = document.getElementById("tbody-horarios");
  tbody.innerHTML = "";

  const checkSoloGuardias = document.getElementById("check-solo-guardias");
  const soloGuardias = checkSoloGuardias ? checkSoloGuardias.checked : false;

  const dias = [0, 1, 2, 3, 4]; // Lunes a Viernes

  appState.tramos.forEach(tramo => {
    const tr = document.createElement("tr");
    tr.className = tramo.es_recreo ? "bg-amber-50/60 font-semibold" : "hover:bg-slate-50";

    // Celda de tramo
    let html = `
      <td class="p-3 border-r border-slate-200 font-medium text-slate-900">
        <div>${tramo.nombre}</div>
        <div class="text-[10px] text-slate-500 font-normal">${tramo.hora_inicio} - ${tramo.hora_fin}</div>
      </td>
    `;

    // Celdas por día
    dias.forEach(dia => {
      let items = appState.horarios.filter(h => 
        h.dia_semana === dia && 
        h.periodo_id === tramo.id &&
        (filtroProfesorId === "todos" || h.profesor_id === filtroProfesorId)
      );

      // Si está activado "Solo guardias y horas libres" y vemos todos los profesores
      if (soloGuardias && filtroProfesorId === "todos") {
        items = items.filter(h => 
          h.tipo_actividad === "GUARDIA_AULA" || 
          h.tipo_actividad === "DISPONIBLE" || 
          h.tipo_actividad === "GUARDIA_RECREO"
        );
      }

      html += `<td class="p-2 border-r border-slate-200 align-top">`;
      
      if (items.length === 0) {
        html += `<span class="text-[11px] text-slate-300">-</span>`;
      } else {
        html += `<div class="space-y-1.5">`;
        items.forEach(it => {
          const prof = appState.profesores.find(p => p.id === it.profesor_id);
          const profName = prof ? prof.nombre : it.profesor_id;

          let badgeClass = "bg-slate-100 text-slate-700 border-slate-200";
          let tipoLabel = it.tipo_actividad;
          if (it.tipo_actividad === "GUARDIA_AULA") {
            badgeClass = "bg-emerald-100 text-emerald-900 border-emerald-300 font-semibold";
            tipoLabel = "Guardia Aula";
          } else if (it.tipo_actividad === "DISPONIBLE") {
            badgeClass = "bg-blue-100 text-blue-900 border-blue-300 font-medium";
            tipoLabel = "Apoyo / Libre";
          } else if (it.tipo_actividad === "NO_DISPONIBLE") {
            badgeClass = "bg-rose-100 text-rose-800 border-rose-300";
            tipoLabel = "No disponible";
          } else if (it.tipo_actividad === "GUARDIA_RECREO") {
            badgeClass = "bg-amber-100 text-amber-900 border-amber-300";
            tipoLabel = "Guardia Recreo";
          } else if (it.tipo_actividad === "LECTIVA") {
            tipoLabel = "Clase";
          }

          html += `
            <div class="px-2 py-1 rounded-lg border text-[11px] ${badgeClass} shadow-2xs">
              <div class="font-bold flex items-center justify-between gap-1">
                <span class="truncate">${profName}</span>
                <span class="text-[9px] opacity-80 uppercase shrink-0">${tipoLabel}</span>
              </div>
              <div class="text-[10px] opacity-75 truncate">${it.materia || it.aula || ''}</div>
            </div>
          `;
        });
        html += `</div>`;
      }

      html += `</td>`;
    });

    tr.innerHTML = html;
    tbody.appendChild(tr);
  });
}

// ===============================================
// HISTORIAL Y ESTADÍSTICAS
// ===============================================

function renderEstadisticas() {
  const grid = document.getElementById("grid-estadisticas");
  grid.innerHTML = "";

  appState.estadisticas.forEach(s => {
    const card = document.createElement("div");
    card.className = "bg-slate-50 border border-slate-200 rounded-xl p-3 flex items-center justify-between";
    card.innerHTML = `
      <div>
        <div class="text-xs font-bold text-slate-800">${s.nombre}</div>
        <div class="text-[10px] text-slate-500">${s.departamento}</div>
      </div>
      <div class="text-center">
        <span class="inline-block px-2 py-0.5 rounded-full text-xs font-bold ${s.sustituciones > 0 ? 'bg-indigo-100 text-indigo-800' : 'bg-slate-200 text-slate-600'}">
          ${s.sustituciones}
        </span>
        <div class="text-[9px] text-slate-400">hechas</div>
      </div>
    `;
    grid.appendChild(card);
  });
}

function filtrarHistorial() {
  renderHistorial();
}

function limpiarFiltrosHistorial() {
  const fText = document.getElementById("filtro-historial-texto");
  const fFecha = document.getElementById("filtro-historial-fecha");
  if (fText) fText.value = "";
  if (fFecha) fFecha.value = "";
  renderHistorial();
}

async function renderHistorial() {
  try {
    const res = await fetch("/api/sustituciones");
    const data = await res.json();
    appState.sustituciones = data;

    const fTextEl = document.getElementById("filtro-historial-texto");
    const fFechaEl = document.getElementById("filtro-historial-fecha");
    const qTexto = fTextEl ? fTextEl.value.trim().toLowerCase() : "";
    const qFecha = fFechaEl ? fFechaEl.value.trim() : "";

    let filtradas = data;
    if (qTexto) {
      filtradas = filtradas.filter(sub => 
        (sub.profesor_ausente_nombre && sub.profesor_ausente_nombre.toLowerCase().includes(qTexto)) ||
        (sub.profesor_sustituto_nombre && sub.profesor_sustituto_nombre.toLowerCase().includes(qTexto)) ||
        (sub.aula && sub.aula.toLowerCase().includes(qTexto)) ||
        (sub.materia && sub.materia.toLowerCase().includes(qTexto)) ||
        (sub.curso_grupo && sub.curso_grupo.toLowerCase().includes(qTexto))
      );
    }
    if (qFecha) {
      filtradas = filtradas.filter(sub => sub.fecha === qFecha);
    }

    const badgeTotal = document.getElementById("total-sustituciones-badge");
    if (badgeTotal) {
      badgeTotal.textContent = `${filtradas.length} de ${data.length} registros`;
    }

    const tbody = document.getElementById("tbody-historial");
    tbody.innerHTML = "";

    if (filtradas.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" class="p-6 text-center text-xs text-slate-400">No se encontraron sustituciones con los filtros aplicados.</td></tr>`;
      return;
    }

    filtradas.forEach(sub => {
      const tr = document.createElement("tr");
      tr.className = "hover:bg-slate-50 transition";
      tr.innerHTML = `
        <td class="p-3">
          <div class="font-semibold text-slate-800">${formatFechaEsp(sub.fecha)}</div>
          <div class="text-[11px] text-indigo-600 font-medium">${sub.periodo_nombre}</div>
        </td>
        <td class="p-3">
          <div class="font-medium text-rose-700">${sub.profesor_ausente_nombre}</div>
        </td>
        <td class="p-3">
          <div class="font-semibold text-emerald-700">${sub.profesor_sustituto_nombre}</div>
          <div class="text-[10px] text-slate-500">${sub.profesor_sustituto_email || ''}</div>
        </td>
        <td class="p-3">
          <div class="font-medium text-slate-800">${sub.aula} ${sub.curso_grupo ? '(' + sub.curso_grupo + ')' : ''}</div>
          <div class="text-[11px] text-slate-500">${sub.materia}</div>
        </td>
        <td class="p-3 text-center">
          <div class="flex items-center justify-center gap-1.5">
            <a href="/api/descargar-ics/${sub.id}" title="Descargar iCal .ics" class="p-1.5 rounded-lg bg-slate-100 hover:bg-indigo-100 text-indigo-600 transition">
              <i class="ph ph-calendar-plus text-base"></i>
            </a>
            <button onclick="eliminarSustitucion('${sub.id}')" title="Eliminar registro" class="p-1.5 rounded-lg bg-slate-100 hover:bg-rose-100 text-rose-600 transition">
              <i class="ph ph-trash text-base"></i>
            </button>
          </div>
        </td>
      `;
      tbody.appendChild(tr);
    });

  } catch (err) {
    console.error("Error al renderizar historial:", err);
  }
}

async function eliminarSustitucion(id) {
  if (!confirm("¿Deseas anular esta sustitución? Se restará del balance del profesor sustituto.")) return;
  try {
    const res = await fetch(`/api/sustituciones/${id}`, { method: "DELETE" });
    if (res.ok) {
      alert("✅ Sustitución anulada correctamente en el sistema.\n\n⚠️ Recuerda: Si ya habías añadido el evento a Google Calendar, debes eliminarlo también desde allí.");
      cargarDatosIniciales();
    } else {
      const err = await res.json();
      alert("No se pudo anular: " + (err.error || "Error del servidor"));
    }
  } catch (err) {
    alert("Error de conexión al intentar anular la sustitución.");
  }
}

// ===============================================
// IMPORTACIÓN DE HORARIOS
// ===============================================

function cargarEjemploJSON() {
  const ejemplo = {
    "profesores": [
      {
        "id": "antonio-perez",
        "nombre": "Antonio Pérez Gómez",
        "telefono": "+34600000001",
        "email": "antonio.perez@colegio.es",
        "departamento": "Matemáticas",
        "etapa": "Secundaria",
        "activo": true,
        "sustituciones_realizadas": 0
      }
    ],
    "horarios": [
      {
        "profesor_id": "antonio-perez",
        "dia_semana": 0,
        "periodo_id": "1H",
        "tipo_actividad": "GUARDIA_AULA",
        "aula": "Planta 1",
        "materia": "Guardia",
        "descripcion": "Disponible para sustitución"
      }
    ]
  };
  document.getElementById("textarea-importar").value = JSON.stringify(ejemplo, null, 2);
}

async function ejecutarImportacion() {
  const contenido = document.getElementById("textarea-importar").value.trim();
  if (!contenido) {
    alert("Introduce los datos en formato JSON.");
    return;
  }

  try {
    const datosJSON = JSON.parse(contenido);
    const res = await fetch("/api/importar-horarios", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(datosJSON)
    });

    const resultado = await res.json();
    if (resultado.success) {
      alert(`¡Horarios importados con éxito!\n- Profesores: ${resultado.total_profesores}\n- Horarios: ${resultado.total_horarios}`);
      cargarDatosIniciales();
      switchTab("horarios");
    } else {
      alert("Error en la importación: " + (resultado.error || "Formato incorrecto"));
    }
  } catch (err) {
    alert("El JSON no es válido: " + err.message);
  }
}
