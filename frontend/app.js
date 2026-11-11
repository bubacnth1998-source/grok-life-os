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
const VIEWS = ["dash", "finance", "projects", "time", "life", "memory", "sim", "audit", "nexus"];
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
