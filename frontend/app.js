const $ = (s) => document.querySelector(s);
let planos = [], alunos = [];

async function api(method, path, body) {
  const r = await fetch(window.API_URL + path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = r.status === 204 ? null : await r.json();
  if (!r.ok) throw new Error((data && data.erro) || "Erro " + r.status);
  return data;
}

function aviso(texto, tipo) {
  const m = $("#msg");
  m.textContent = texto;
  m.className = tipo;
  setTimeout(() => (m.className = ""), 4000);
}

const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const formData = (f) => Object.fromEntries(new FormData(f));

async function acao(fn, okMsg) {
  try { await fn(); if (okMsg) aviso(okMsg, "ok"); }
  catch (e) { aviso(e.message, "erro"); }
}

// ---- abas
document.querySelectorAll("nav button").forEach((b) => b.onclick = () => {
  document.querySelectorAll("nav button, section").forEach((e) => e.classList.remove("ativo"));
  b.classList.add("ativo");
  $("#" + b.dataset.tab).classList.add("ativo");
});

// ---- planos
async function carregarPlanos() {
  planos = await api("GET", "/planos");
  $("#t-planos").innerHTML = planos.map((p) => `<tr><td>${esc(p.nome)}</td><td>R$ ${Number(p.valor_mensal).toFixed(2)}</td><td>${p.duracao_meses}</td>
    <td><button onclick="editarPlano(${p.id})">Editar</button> <button onclick="excluirPlano(${p.id})">Excluir</button></td></tr>`).join("");
  $("#sel-plano").innerHTML = planos.map((p) => `<option value="${p.id}">${esc(p.nome)}</option>`).join("");
}
window.editarPlano = (id) => { const p = planos.find((x) => x.id === id); const f = $("#f-plano"); for (const k in p) if (f[k]) f[k].value = p[k]; };
window.excluirPlano = (id) => acao(async () => { await api("DELETE", "/planos/" + id); await carregarPlanos(); }, "Plano removido");
$("#f-plano").onsubmit = (e) => { e.preventDefault(); const d = formData(e.target);
  acao(async () => { d.id ? await api("PUT", "/planos/" + d.id, d) : await api("POST", "/planos", d); e.target.reset(); await carregarPlanos(); }, "Plano salvo"); };

// ---- alunos
async function carregarAlunos() {
  const b = $("#busca").value.trim();
  alunos = await api("GET", "/alunos" + (b ? "?busca=" + encodeURIComponent(b) : ""));
  $("#t-alunos").innerHTML = alunos.map((a) => `<tr><td>${esc(a.nome)}</td><td>${esc(a.cpf)}</td><td>${esc(a.telefone)}</td><td>${esc(a.plano)}</td>
    <td><button onclick="editarAluno(${a.id})">Editar</button> <button onclick="excluirAluno(${a.id})">Excluir</button></td></tr>`).join("");
}
window.editarAluno = (id) => { const a = alunos.find((x) => x.id === id); const f = $("#f-aluno"); for (const k in a) if (f[k]) f[k].value = a[k] ?? ""; };
window.excluirAluno = (id) => { if (confirm("Excluir aluno e suas inscrições?")) acao(async () => { await api("DELETE", "/alunos/" + id); await carregarAlunos(); await carregarAulas(); }, "Aluno removido"); };
$("#f-aluno").onsubmit = (e) => { e.preventDefault(); const d = formData(e.target);
  acao(async () => { d.id ? await api("PUT", "/alunos/" + d.id, d) : await api("POST", "/alunos", d); e.target.reset(); await carregarAlunos(); }, "Aluno salvo"); };
$("#busca").oninput = () => acao(carregarAlunos);

// ---- aulas e inscrições
async function carregarAulas() {
  const aulas = await api("GET", "/aulas");
  const opts = alunos.map((a) => `<option value="${a.id}">${esc(a.nome)}</option>`).join("");
  $("#t-aulas").innerHTML = aulas.map((a) => `<tr><td>${esc(a.modalidade)}</td><td>${esc(a.dia_semana)}</td><td>${esc(a.horario)}</td><td>${a.vagas_restantes}/${a.vagas}</td>
    <td><select id="insc-${a.id}">${opts}</select> <button onclick="inscrever(${a.id})">Inscrever</button></td>
    <td><button onclick="excluirAula(${a.id})">Excluir</button></td></tr>`).join("");
}
window.inscrever = (aulaId) => acao(async () => { await api("POST", `/aulas/${aulaId}/inscricoes`, { aluno_id: $("#insc-" + aulaId).value }); await carregarAulas(); }, "Inscrição criada");
window.excluirAula = (id) => acao(async () => { await api("DELETE", "/aulas/" + id); await carregarAulas(); }, "Aula removida");
$("#f-aula").onsubmit = (e) => { e.preventDefault(); const d = formData(e.target);
  acao(async () => { d.id ? await api("PUT", "/aulas/" + d.id, d) : await api("POST", "/aulas", d); e.target.reset(); await carregarAulas(); }, "Aula salva"); };

acao(async () => { await carregarPlanos(); await carregarAlunos(); await carregarAulas(); });

// ---- Aula 4: arquivos (URL pre-assinada -> S3 -> Lambda miniatura) e relatorios (RF-02, RF-04)
const TIPOS_OK = ["image/jpeg", "image/png", "application/pdf"];
const MAX_BYTES = 5 * 1024 * 1024;

async function carregarArqTela() {
  const al = await api("GET", "/alunos");
  $("#arq-aluno").innerHTML = '<option value="">Escolha...</option>' + al.map((a) => `<option value="${a.id}">${esc(a.nome)}</option>`).join("");
  $("#arq-lista").innerHTML = "";
}

async function listarArquivosAluno() {
  const id = $("#arq-aluno").value;
  if (!id) { $("#arq-lista").innerHTML = ""; return; }
  const lista = await api("GET", `/alunos/${id}/arquivos`);
  $("#arq-lista").innerHTML = lista.map((a) => {
    const arq = a.url_miniatura
      ? `<a href="${a.url}" target="_blank"><img src="${a.url_miniatura}" width="150" height="150" alt="miniatura"></a>`
      : `<a href="${a.url}" target="_blank">abrir</a>`;
    return `<tr><td>${esc(a.categoria)}</td><td>${arq}</td><td>${esc(a.status)}</td><td>${esc(a.tamanho_bytes)}</td><td>${a.largura ? esc(a.largura + "x" + a.altura) : ""}</td></tr>`;
  }).join("");
}

$("#arq-aluno").onchange = () => acao(listarArquivosAluno);

$("#f-arquivo").onsubmit = (e) => {
  e.preventDefault();
  acao(async () => {
    const id = $("#arq-aluno").value;
    const file = $("#arq-file").files[0];
    const categoria = $("#arq-cat").value;
    if (!id) throw new Error("Escolha um aluno");
    if (!file) throw new Error("Escolha um arquivo");
    if (!TIPOS_OK.includes(file.type)) throw new Error("Use JPG, PNG ou PDF");
    if (file.size > MAX_BYTES) throw new Error("Arquivo maior que 5 MB");
    const p = await api("POST", `/alunos/${id}/arquivos/presign`, { nome: file.name, tipo: file.type, tamanho: file.size, categoria });
    const put = await fetch(p.url, { method: "PUT", headers: { "Content-Type": p.content_type }, body: file });
    if (!put.ok) throw new Error("S3 recusou o upload (HTTP " + put.status + ")");
    for (let i = 0; i < 10; i++) {
      await new Promise((r) => setTimeout(r, 1500));
      const l = await api("GET", `/alunos/${id}/arquivos`);
      const a = l.find((x) => x.id === p.arquivo_id);
      if (a && a.status !== "PENDENTE") break;
    }
    e.target.reset();
    $("#arq-aluno").value = id;
    await listarArquivosAluno();
  }, "Arquivo enviado e processado");
};

function tabelaRel(linhas) {
  if (!linhas.length) return "<p>Sem dados.</p>";
  const cols = Object.keys(linhas[0]);
  return "<table><thead><tr>" + cols.map((c) => `<th>${esc(c)}</th>`).join("") + "</tr></thead><tbody>" +
    linhas.map((l) => "<tr>" + cols.map((c) => `<td>${esc(l[c])}</td>`).join("") + "</tr>").join("") + "</tbody></table>";
}

async function carregarRelatorios() {
  $("#rel-ocupacao").innerHTML = tabelaRel(await api("GET", "/relatorios/ocupacao-aulas"));
  $("#rel-planos").innerHTML = tabelaRel(await api("GET", "/relatorios/alunos-por-plano"));
}

document.querySelector('[data-tab="arquivos"]').addEventListener("click", () => acao(carregarArqTela));
document.querySelector('[data-tab="relatorios"]').addEventListener("click", () => acao(carregarRelatorios));
