// Aula 4 - trecho acrescentado ao final do frontend/app.js publicado no S3 (RF-02 e RF-04).
// Usa os helpers que o app.js ja define: $, api, acao, esc.
// As secoes HTML correspondentes (#arquivos e #relatorios) estao em aula4-secoes.html.

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
    // 1) pede a URL pre-assinada; 2) envia direto ao S3; 3) espera a Lambda de miniatura processar
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
