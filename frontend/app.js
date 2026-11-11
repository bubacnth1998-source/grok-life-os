const API = "/api/v1";
const esc = (v) => String(v ?? "").replace(/[&<>\x22\x27]/g, ch => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", "\x22":"&quot;", "\x27":"&#39;" })[ch]);
let token = localStorage.getItem("glo_token") || "";
async function api(path, opts = {}) {
  const headers = { "Content-Type": "application/json", ...(opts.headers || {}) };
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(API + path, { ...opts, headers });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || res.statusText);
  return data;
}
function showApp(user) {
  document.getElementById("auth").classList.add("hidden");
  document.getElementById("app").classList.remove("hidden");
  document.getElementById("user-label").textContent = user?.full_name || user?.email || "";
  loadDash();
}
document.getElementById("btn-login").onclick = async () => {
  try {
    const data = await api("/auth/login", { method: "POST", body: JSON.stringify({ email: document.getElementById("email").value, password: document.getElementById("password").value }) });
    token = data.access_token; localStorage.setItem("glo_token", token); showApp(data.user);
  } catch (e) { document.getElementById("auth-err").textContent = e.message; }
};
document.getElementById("btn-register").onclick = async () => {
  try {
    const data = await api("/auth/register", { method: "POST", body: JSON.stringify({ email: document.getElementById("email").value, password: document.getElementById("password").value, full_name: document.getElementById("name").value || "Usuario" }) });
    token = data.access_token; localStorage.setItem("glo_token", token); showApp(data.user);
  } catch (e) { document.getElementById("auth-err").textContent = e.message; }
};
document.getElementById("btn-logout").onclick = () => { token = ""; localStorage.removeItem("glo_token"); location.reload(); };
const VIEWS = ["dash", "finance", "projects", "time", "life", "memory", "sim", "audit", "nexus", "workspace"];
document.querySelectorAll(".nav").forEach((btn) => {
  btn.onclick = () => {
    document.querySelectorAll(".nav").forEach((b) => b.classList.remove("bg-slate-800"));
    btn.classList.add("bg-slate-800");
    VIEWS.forEach((v) => { const el = document.getElementById("view-" + v); if (el) el.classList.toggle("hidden", btn.dataset.view !== v); });
    if (btn.dataset.view === "dash") loadDash();
    if (btn.dataset.view === "finance") loadFinance();
    if (btn.dataset.view === "projects") loadProjects();
    if (btn.dataset.view === "time") loadTime();
    if (btn.dataset.view === "life") loadLife();
    if (btn.dataset.view === "memory") loadMemory();
    if (btn.dataset.view === "sim") loadSim();
    if (btn.dataset.view === "audit") loadAudit();
    if (btn.dataset.view === "nexus") loadNexus();
    if (btn.dataset.view === "workspace") loadWorkspace();
  };
});
async function loadDash() {
  const el = document.getElementById("view-dash");
  try {
    const d = await api("/core/dashboard");
    el.innerHTML = `<h2 class="text-lg font-medium mb-2">LIFE CORE</h2><div class="grid gap-3 sm:grid-cols-2"><div class="rounded-xl border border-slate-800 p-4"><div class="text-slate-400 text-xs">Pendientes</div><div class="text-2xl">${esc(d.answers.pending_count)}</div></div><div class="rounded-xl border border-slate-800 p-4"><div class="text-slate-400 text-xs">Disponible</div><div class="text-2xl">${esc(d.finance.personal.available)} €</div></div></div><ul class="mt-4 text-sm">${(d.answers.next||[]).map(t=>`<li>• ${esc(t.title)}</li>`).join("")||"<li class='text-slate-500'>Nada prioritario</li>"}</ul>`;
  } catch (e) { el.innerHTML = `<p class="text-red-400">${esc(e.message)}</p>`; }
}
async function loadFinance() {
  const el = document.getElementById("view-finance");
  try {
    const s = await api("/finance/summary?scope=personal");
    const accounts = await api("/finance/accounts");
    el.innerHTML = `<h2 class="text-lg">Finance</h2><p class="text-sm text-slate-400">Disp ${s.available} · Res ${s.reserved}</p><ul class="mt-3">${accounts.map(a=>`<li class="border border-slate-800 rounded-lg px-3 py-2 flex justify-between"><span>${esc(a.name)}</span><span>${esc(a.balance)}</span></li>`).join("")||"<li class='text-slate-500'>Sin cuentas</li>"}</ul><button id="add-acc" class="mt-3 rounded-xl bg-slate-800 px-4 py-2 text-sm">+ Cuenta</button>`;
    document.getElementById("add-acc").onclick = async () => { const name = prompt("Nombre"); if (!name) return; await api("/finance/accounts", { method: "POST", body: JSON.stringify({ name }) }); loadFinance(); };
  } catch (e) { el.innerHTML = `<p class="text-red-400">${esc(e.message)}</p>`; }
}
async function loadProjects() {
  const el = document.getElementById("view-projects");
  try {
    const projects = await api("/projects"); const tasks = await api("/projects/tasks");
    el.innerHTML = `<h2 class="text-lg">Projects</h2><button id="add-p" class="rounded-xl bg-slate-800 px-4 py-2 text-sm">+ Proyecto</button><button id="add-t" class="rounded-xl bg-slate-800 px-4 py-2 text-sm">+ Tarea</button><ul class="mt-3">${projects.map(p=>`<li>${esc(p.name)} · ${esc(p.status)}</li>`).join("")}</ul><ul class="mt-2">${tasks.map(t=>`<li>${esc(t.title)} (${t.status})</li>`).join("")}</ul>`;
    document.getElementById("add-p").onclick = async () => { const name = prompt("Proyecto"); if (!name) return; await api("/projects", { method: "POST", body: JSON.stringify({ name }) }); loadProjects(); };
    document.getElementById("add-t").onclick = async () => { const title = prompt("Tarea"); if (!title) return; await api("/projects/tasks", { method: "POST", body: JSON.stringify({ title }) }); loadProjects(); };
  } catch (e) { el.innerHTML = `<p class="text-red-400">${esc(e.message)}</p>`; }
}
async function loadTime() {
  const el = document.getElementById("view-time");
  try {
    const agenda = await api("/time/agenda/today");
    el.innerHTML = `<h2 class="text-lg">Time · ${esc(agenda.date)}</h2><ul>${(agenda.events||[]).map(e=>`<li>${esc(e.title)}</li>`).join("")||"<li class='text-slate-500'>Sin eventos</li>"}</ul>`;
  } catch (e) { el.innerHTML = `<p class="text-red-400">${esc(e.message)}</p>`; }
}
async function loadLife() {
  const el = document.getElementById("view-life");
  try {
    const notes = await api("/life/notes");
    el.innerHTML = `<h2 class="text-lg">Life domains</h2><button id="add-l" class="rounded-xl bg-slate-800 px-4 py-2 text-sm">+ Nota</button><ul class="mt-3">${notes.map(n=>`<li><span class="text-xs text-slate-500">${esc(n.domain)}</span> ${esc(n.title)}</li>`).join("")}</ul>`;
    document.getElementById("add-l").onclick = async () => { const domain = prompt("Dominio", "housing"); const title = prompt("Título"); if (!domain||!title) return; await api("/life/notes", { method: "POST", body: JSON.stringify({ domain, title }) }); loadLife(); };
  } catch (e) { el.innerHTML = `<p class="text-red-400">${esc(e.message)}</p>`; }
}
async function loadMemory() {
  const el = document.getElementById("view-memory");
  try {
    const items = await api("/memory");
    el.innerHTML = `<h2 class="text-lg">Memory</h2><button id="add-m" class="rounded-xl bg-slate-800 px-4 py-2 text-sm">+ Item</button><ul class="mt-3">${items.map(m=>`<li>${esc(m.kind)}: ${esc(m.title)}</li>`).join("")}</ul>`;
    document.getElementById("add-m").onclick = async () => { const title = prompt("Título"); if (!title) return; await api("/memory", { method: "POST", body: JSON.stringify({ kind: "goal", title, confidence: "confirmed" }) }); loadMemory(); };
  } catch (e) { el.innerHTML = `<p class="text-red-400">${esc(e.message)}</p>`; }
}
async function loadSim() {
  const el = document.getElementById("view-sim");
  el.innerHTML = `<h2 class="text-lg">Simulator</h2><button id="sim-s" class="rounded-xl bg-slate-800 px-4 py-2 text-sm">Ahorro 300×12</button><pre id="sim-out" class="mt-3 text-xs"></pre>`;
  document.getElementById("sim-s").onclick = async () => { document.getElementById("sim-out").textContent = JSON.stringify(await api("/simulator/savings", { method: "POST", body: JSON.stringify({ monthly_save: 300, months: 12 }) }), null, 2); };
}
async function loadAudit() {
  const el = document.getElementById("view-audit");
  try {
    const r = await api("/audit/run");
    el.innerHTML = `<h2 class="text-lg">Audit</h2><p class="text-sm">c ${r.summary.critical} w ${r.summary.warn} i ${r.summary.info}</p><ul class="text-sm mt-2">${(r.findings||[]).slice(0,20).map(f=>`<li><strong>${esc(f.code)}</strong> ${esc(f.evidence)}</li>`).join("")}</ul>`;
  } catch (e) { el.innerHTML = `<p class="text-red-400">${esc(e.message)}</p>`; }
}
async function loadNexus() {
  try { const st = await api("/nexus/status"); document.getElementById("nexus-status").textContent = `Modo: ${st.mode}`;} catch (_){}
}
document.getElementById("nexus-form").onsubmit = async (ev) => {
  ev.preventDefault();
  const input = document.getElementById("nexus-input");
  const msg = input.value.trim(); if (!msg) return;
  const log = document.getElementById("nexus-log");
  log.innerHTML += `<div class="text-slate-400">Tú: ${esc(msg)}</div>`; input.value = "";
  try { const r = await api("/nexus/chat", { method: "POST", body: JSON.stringify({ message: msg }) }); log.innerHTML += `<div>NEXUS: ${esc(r.reply)}</div>`; }
  catch (e) { log.innerHTML += `<div class="text-red-400">${esc(e.message)}</div>`; }
};
if (token) api("/auth/me").then(showApp).catch(() => localStorage.removeItem("glo_token"));

const voiceButton = document.getElementById("btn-voice");
if (voiceButton) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    voiceButton.title = "El navegador no admite dictado por voz";
    voiceButton.onclick = () => { document.getElementById("nexus-status").textContent = "El dictado por voz no está disponible en este navegador."; };
  } else {
    const recognition = new SpeechRecognition();
    recognition.lang = "es-ES";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.onstart = () => { voiceButton.textContent = "Escuchando…"; voiceButton.disabled = true; };
    recognition.onend = () => { voiceButton.textContent = "🎙"; voiceButton.disabled = false; };
    recognition.onerror = (event) => { document.getElementById("nexus-status").textContent = "Dictado: " + event.error; };
    recognition.onresult = (event) => {
      const transcript = event.results?.[0]?.[0]?.transcript || "";
      const input = document.getElementById("nexus-input");
      input.value = [input.value, transcript].filter(Boolean).join(" ").trim();
      input.focus();
    };
    voiceButton.onclick = () => { try { recognition.start(); } catch (_) {} };
  }
}

async function loadWorkspace() {
  const el = document.getElementById("view-workspace");
  el.innerHTML = '<h2 class="text-lg font-medium mb-3">Workspace</h2><p class="text-sm text-slate-400 mb-4">Hábitos, negocio, viajes, aprendizaje y biblioteca. Los datos se guardan en tu cuenta.</p><div id="workspace-content" class="space-y-4">Cargando módulos…</div>';
  const host = document.getElementById("workspace-content");
  try {
    const [habits, trips, courses, media, clients, invoices, rules, intelligence] = await Promise.all([
      api("/habits"), api("/travel/trips"), api("/learning/courses"), api("/media/items"),
      api("/business/clients"), api("/business/invoices"), api("/automation/rules"), api("/intelligence/snapshot")
    ]);
    host.innerHTML = `
      <section class="rounded-xl border border-slate-800 p-3"><div class="flex justify-between items-center"><h3 class="font-medium">Hábitos</h3><button id="ws-habit" class="rounded-lg bg-slate-800 px-3 py-2">+ Añadir</button></div><ul class="mt-2 space-y-2">${habits.map(x=>`<li class="flex justify-between gap-2"><span>${esc(x.name)} · ${esc(x.frequency)}</span><button data-habit-log="${Number(x.id)}" class="rounded-lg bg-slate-800 px-3 py-1">${x.completed_today ? "Hecho" : "Completar"}</button></li>`).join("") || "<li class='text-slate-500'>Sin hábitos</li>"}</ul></section>
      <section class="rounded-xl border border-slate-800 p-3"><div class="flex justify-between items-center"><h3 class="font-medium">Viajes</h3><button id="ws-trip" class="rounded-lg bg-slate-800 px-3 py-2">+ Viaje</button></div><ul class="mt-2">${trips.map(x=>`<li>${esc(x.title)} · ${esc(x.destination || "Destino pendiente")} · ${esc(x.status)}</li>`).join("") || "<li class='text-slate-500'>Sin viajes</li>"}</ul></section>
      <section class="rounded-xl border border-slate-800 p-3"><div class="flex justify-between items-center"><h3 class="font-medium">Aprendizaje</h3><button id="ws-course" class="rounded-lg bg-slate-800 px-3 py-2">+ Curso</button></div><ul class="mt-2">${courses.map(x=>`<li>${esc(x.title)} · ${esc(x.progress)}%</li>`).join("") || "<li class='text-slate-500'>Sin cursos</li>"}</ul></section>
      <section class="rounded-xl border border-slate-800 p-3"><div class="flex justify-between items-center"><h3 class="font-medium">Biblioteca multimedia</h3><button id="ws-media" class="rounded-lg bg-slate-800 px-3 py-2">+ Recurso</button></div><ul class="mt-2">${media.map(x=>`<li>${esc(x.title)} · ${esc(x.media_type)}</li>`).join("") || "<li class='text-slate-500'>Sin recursos</li>"}</ul></section>
      <section class="rounded-xl border border-slate-800 p-3"><div class="flex justify-between items-center"><h3 class="font-medium">Negocio</h3><button id="ws-client" class="rounded-lg bg-slate-800 px-3 py-2">+ Cliente</button></div><p class="text-sm text-slate-400 mt-1">${clients.length} clientes · ${invoices.length} facturas</p><ul class="mt-2">${clients.map(x=>`<li>${esc(x.name)} · ${esc(x.email || "Sin email")}</li>`).join("") || "<li class='text-slate-500'>Sin clientes</li>"}</ul></section>
      <section class="rounded-xl border border-slate-800 p-3"><h3 class="font-medium">Automatizaciones</h3><ul class="mt-2">${rules.map(x=>`<li>${esc(x.name)} · ${esc(x.trigger_type)} · ${x.is_active ? "Activa" : "Pausada"}</li>`).join("") || "<li class='text-slate-500'>Sin reglas</li>"}</ul><p class="text-xs text-slate-500 mt-2">Las reglas actuales solo se ejecutan manualmente o bajo confirmación; no hay scheduler en segundo plano.</p></section>
      <section class="rounded-xl border border-slate-800 p-3"><h3 class="font-medium">Inteligencia</h3><ul class="mt-2">${intelligence.facts.map(x=>`<li>${esc(x.text)}</li>`).join("")}</ul><p class="text-xs text-slate-500 mt-2">${esc(intelligence.disclaimer)}</p></section>`;
    document.getElementById("ws-habit").onclick = async () => { const name=prompt("Nombre del hábito"); if(name?.trim()){await api("/habits",{method:"POST",body:JSON.stringify({name})});loadWorkspace();} };
    document.getElementById("ws-trip").onclick = async () => { const title=prompt("Nombre del viaje"); if(!title?.trim())return; const destination=prompt("Destino")||""; await api("/travel/trips",{method:"POST",body:JSON.stringify({title,destination})});loadWorkspace(); };
    document.getElementById("ws-course").onclick = async () => { const title=prompt("Nombre del curso"); if(title?.trim()){await api("/learning/courses",{method:"POST",body:JSON.stringify({title})});loadWorkspace();} };
    document.getElementById("ws-media").onclick = async () => { const title=prompt("Nombre del recurso"); if(!title?.trim())return; const url_or_path=prompt("URL o ruta (opcional)")||null; await api("/media/items",{method:"POST",body:JSON.stringify({title,media_type:"other",url_or_path})});loadWorkspace(); };
    document.getElementById("ws-client").onclick = async () => { const name=prompt("Nombre del cliente"); if(name?.trim()){await api("/business/clients",{method:"POST",body:JSON.stringify({name})});loadWorkspace();} };
    host.querySelectorAll("[data-habit-log]").forEach(btn=>btn.onclick=async()=>{await api("/habits/"+btn.dataset.habitLog+"/log",{method:"POST"});loadWorkspace();});
  } catch (e) {
    host.innerHTML = '<p class="text-red-400">No se pudieron cargar todos los módulos: '+esc(e.message)+'</p><p class="text-xs text-slate-500 mt-2">Comprueba que las migraciones y rutas de la API estén disponibles.</p>';
  }
}


// Installable shell only: the service worker deliberately never caches /api/ responses.
if ("serviceWorker" in navigator && window.isSecureContext) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js").catch((error) => {
      console.warn("Grok LIFE OS: service worker registration failed", error);
    });
  }, { once: true });
}
