// Interfaz de consulta: primero muestra la evidencia (rápido) y luego la respuesta generada.
const $ = (s) => document.querySelector(s);
const esc = (t) => String(t ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

const ETIQUETAS = {
  respuesta_correcta: "Opción elegida", justificacion: "Justificación", descarte_opciones: "Opciones descartadas",
  respuesta: "Respuesta", palabras_clave: "Palabras clave", referencia_legal: "Referencia legal",
  marco_normativo: "Marco normativo", analisis: "Análisis", jurisprudencia: "Jurisprudencia", conclusion: "Conclusión",
};
const ORDEN = {
  multiple_choice: ["respuesta_correcta", "justificacion", "descarte_opciones"],
  semi_open: ["respuesta", "palabras_clave", "referencia_legal"],
  open_ended: ["marco_normativo", "analisis", "jurisprudencia", "conclusion"],
};

async function iniciar() {
  try {
    const e = await (await fetch("/api/estado")).json();
    for (const a of e.areas) $("#area").insertAdjacentHTML("beforeend", `<option>${esc(a)}</option>`);
    if (!e.indice) aviso("No hay índice construido. Ejecute `python -m src.corpus.nube` (corpus publicado) o `python -m src.corpus.build` y `python -m src.index.build`.");
  } catch { aviso("No se pudo consultar el estado del servidor."); }
}

function aviso(texto) { const a = $("#aviso"); a.textContent = texto; a.hidden = !texto; }

$("#formato").addEventListener("change", () => { $("#opciones").hidden = $("#formato").value !== "multiple_choice"; });

function cuerpoConsulta() {
  const c = { pregunta: $("#pregunta").value, formato: $("#formato").value, area: $("#area").value || null, sin_cache: $("#sinCache").checked };
  if (c.formato === "multiple_choice") {
    c.opciones = {};
    document.querySelectorAll("#opciones input").forEach((i) => { if (i.value.trim()) c.opciones[i.dataset.letra] = i.value.trim(); });
  }
  return c;
}

async function post(url, cuerpo) {
  const r = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(cuerpo) });
  const d = await r.json();
  if (!r.ok) throw new Error(typeof d.detail === "string" ? d.detail : JSON.stringify(d.detail));
  return d;
}

function pintarPasajes(pasajes, usados = []) {
  $("#nPasajes").textContent = `${pasajes.length} pasajes`;
  $("#pasajes").innerHTML = pasajes.map((p) => `
    <li class="pasaje ${usados.includes(p.n) ? "usado" : ""}" id="p${p.n}">
      <details ${p.n <= 2 ? "open" : ""}>
        <summary><span class="num">P${p.n}</span><span class="enc">${esc(p.encabezado)}</span>
          <span class="score">${p.rerank != null ? "pert. " + p.rerank.toFixed(3) : "score " + p.score}</span></summary>
        <pre>${esc(p.texto.split("\n").slice(1).join("\n"))}</pre>
        <div class="meta">${esc(p.doc_id)} [${p.inicio}–${p.fin}] · ${esc((p.origen || []).join(" + "))}
          ${p.url ? ` · <a href="${esc(p.url)}" target="_blank" rel="noopener">fuente</a>` : ""}</div>
      </details>
    </li>`).join("");
}

function pintarRespuesta(d) {
  const r = d.respuesta;
  const ins = $("#estadoRespuesta");
  ins.className = "insignia" + (r.abstencion ? " abst" : "");
  ins.textContent = r.abstencion ? "Abstención" : "Respondida";
  if (r.abstencion) {
    $("#respuesta").innerHTML = `<p>El corpus no aporta fundamento suficiente para responder. <em>${esc(d.traza.motivo)}</em></p>`;
  } else {
    $("#respuesta").innerHTML = ORDEN[r.formato].map((k) => {
      let v = r[k];
      if (k === "respuesta_correcta") v = `<span class="letra">${esc(v)}</span>`;
      else if (k === "descarte_opciones") v = Object.entries(v || {}).map(([l, t]) => `<div><b style="display:inline">${esc(l)}:</b> ${esc(t)}</div>`).join("");
      else if (k === "palabras_clave") v = `<div class="chips">${(v || []).map((x) => `<span class="chip">${esc(x)}</span>`).join("")}</div>`;
      else v = esc(v);
      return `<div class="campo"><b>${ETIQUETAS[k]}</b>${v}</div>`;
    }).join("");
  }
  $("#citas").innerHTML = d.citas.length ? d.citas.map((c) => `
    <div class="cita ${c.respaldada ? "ok" : "mal"}"><span>${esc(c.cita)}</span>
      <small>${c.respaldada ? "respaldada en " + c.pasajes.map((n) => `<a href="#p${n}">P${n}</a>`).join(", ") : "sin respaldo"}</small></div>`).join("")
    : "<p class='tiempos'>La respuesta no cita normas.</p>";
  const t = d.traza;
  $("#tiempos").textContent = `Recuperación ${t.s_recuperacion}s · generación ${t.s_generacion}s · total ${t.s_total}s`
    + (t.desde_cache ? " (desde caché)" : "") + ` · pasajes leídos por el modelo: ${t.pasajes_leidos}`
    + (t.citas_eliminadas.length ? ` · citas sin respaldo eliminadas: ${t.citas_eliminadas.length}` : "");
}

$("#form").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  aviso("");
  const boton = $("#enviar");
  boton.disabled = true;
  const c = cuerpoConsulta();
  $("#resultados").hidden = false;
  $("#respuesta").innerHTML = "<p>Recuperando evidencia…</p>";
  $("#citas").innerHTML = "";
  $("#tiempos").textContent = "";
  $("#estadoRespuesta").className = "insignia cargando";
  $("#estadoRespuesta").textContent = "Buscando…";
  try {
    const ev1 = await post("/api/recuperar", c);
    pintarPasajes(ev1.pasajes);
    $("#respuesta").innerHTML = "<p>Generando la respuesta con Qwen3-8B… (en CPU puede tardar un par de minutos)</p>";
    $("#estadoRespuesta").textContent = "Generando…";
    const d = await post("/api/consulta", c);
    pintarPasajes(d.pasajes, (d.citas || []).flatMap((x) => x.pasajes));
    pintarRespuesta(d);
  } catch (e) {
    aviso("Error: " + e.message);
    $("#estadoRespuesta").textContent = "Error";
  } finally {
    boton.disabled = false;
  }
});

iniciar();
