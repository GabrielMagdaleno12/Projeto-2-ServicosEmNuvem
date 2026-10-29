"""Lambda `presign` (RF-02).

Rotas (API Gateway HTTP API, payload v2):
  POST /alunos/{id}/arquivos/presign  -> valida, registra a linha em `arquivo` e devolve URL PUT pré-assinada
  GET  /alunos/{id}/arquivos          -> lista arquivos do aluno com URLs GET pré-assinadas (bucket é privado)

Tabela `arquivo` (schema existente do projeto): id, aluno_id, tipo ('foto'|'atestado'), chave_s3,
chave_thumb, tamanho_bytes, largura, altura, criado_em.
Uma linha é considerada PROCESSADA quando a Lambda `miniatura` preencheu `tamanho_bytes`.

Variáveis de ambiente: UPLOAD_BUCKET, DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
Roda na VPC (precisa falar com o RDS). Assinar uma URL é um cálculo local: não precisa de internet.
"""
import json
import os
import uuid

import boto3
import pymysql
from botocore.config import Config

REGION = os.environ.get("AWS_REGION", "us-east-1")
BUCKET = os.environ["UPLOAD_BUCKET"]

# SigV4 + endereço "virtual" evita erro de redirect/CORS com buckets recém-criados.
s3 = boto3.client(
    "s3",
    region_name=REGION,
    config=Config(signature_version="s3v4", s3={"addressing_style": "virtual"}),
)

EXT_POR_TIPO = {"image/jpeg": "jpg", "image/png": "png", "application/pdf": "pdf"}
CATEGORIAS = {"foto", "atestado"}
MAX_BYTES = 5 * 1024 * 1024
EXPIRA_PUT = 300     # 5 min (igual ao design.md)
EXPIRA_GET = 900

HEADERS = {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"}

_conn = None  # reaproveitada entre invocações (ADR-001: reuso de conexão fora do handler)


def conectar():
    global _conn
    if _conn is not None:
        try:
            _conn.ping(reconnect=True)
            return _conn
        except Exception:
            _conn = None
    _conn = pymysql.connect(
        host=os.environ["DB_HOST"],
        user=os.environ["DB_USER"],
        password=os.environ.get("DB_PASSWORD") or os.environ["DB_PASS"],
        database=os.environ["DB_NAME"],
        connect_timeout=5,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )
    return _conn


def resp(status, corpo):
    return {"statusCode": status, "headers": HEADERS, "body": json.dumps(corpo, default=str)}


def validar(corpo):
    """Devolve (erro, dados). Mesmas regras da HU-06: JPG/PNG/PDF até 5 MB."""
    nome = (corpo.get("nome") or "").strip()
    tipo = (corpo.get("tipo") or "").strip().lower()          # tipo MIME enviado pelo navegador
    categoria = (corpo.get("categoria") or "foto").strip().lower()
    try:
        tamanho = int(corpo.get("tamanho") or 0)
    except (TypeError, ValueError):
        tamanho = 0

    if not nome:
        return "Informe o nome do arquivo", None
    if tipo not in EXT_POR_TIPO:
        return "Tipo não permitido (use JPG, PNG ou PDF)", None
    if categoria not in CATEGORIAS:
        return "Categoria inválida (foto ou atestado)", None
    if categoria == "foto" and not tipo.startswith("image/"):
        return "A foto precisa ser JPG ou PNG", None
    if tamanho <= 0 or tamanho > MAX_BYTES:
        return "Arquivo vazio ou maior que 5 MB", None
    return None, {"nome": nome, "tipo": tipo, "categoria": categoria, "tamanho": tamanho}


def criar_presign(aluno_id, corpo):
    erro, d = validar(corpo)
    if erro:
        return resp(400, {"erro": erro})

    cur = conectar().cursor()
    cur.execute("SELECT id FROM aluno WHERE id=%s", (aluno_id,))
    if not cur.fetchone():
        return resp(404, {"erro": "Aluno não encontrado"})

    # uuid evita sobrescrever; sem o nome do usuário na chave evita caracteres estranhos
    chave = f"uploads/{aluno_id}/{uuid.uuid4().hex}.{EXT_POR_TIPO[d['tipo']]}"

    cur.execute(
        "INSERT INTO arquivo (aluno_id, tipo, chave_s3) VALUES (%s,%s,%s)",
        (aluno_id, d["categoria"], chave),
    )
    arquivo_id = cur.lastrowid

    url = s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": BUCKET, "Key": chave, "ContentType": d["tipo"]},
        ExpiresIn=EXPIRA_PUT,
    )
    print(f"presign ok aluno={aluno_id} arquivo={arquivo_id} chave={chave}")
    return resp(200, {"arquivo_id": arquivo_id, "url": url, "chave": chave,
                      "content_type": d["tipo"], "expira_em": EXPIRA_PUT})


def listar_arquivos(aluno_id):
    cur = conectar().cursor()
    cur.execute(
        "SELECT id, tipo AS categoria, chave_s3, chave_thumb, tamanho_bytes, largura, altura, criado_em "
        "FROM arquivo WHERE aluno_id=%s ORDER BY id DESC",
        (aluno_id,),
    )
    itens = cur.fetchall()
    for a in itens:
        a["status"] = "PROCESSADO" if a["tamanho_bytes"] is not None else "PENDENTE"
        a["url"] = s3.generate_presigned_url(
            "get_object", Params={"Bucket": BUCKET, "Key": a["chave_s3"]}, ExpiresIn=EXPIRA_GET)
        a["url_miniatura"] = (
            s3.generate_presigned_url(
                "get_object", Params={"Bucket": BUCKET, "Key": a["chave_thumb"]}, ExpiresIn=EXPIRA_GET)
            if a["chave_thumb"] else None
        )
        del a["chave_s3"], a["chave_thumb"]  # não expõe chaves internas
    return resp(200, itens)


def handler(event, context):
    try:
        if event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
            return resp(204, {})

        rota = event.get("routeKey", "")
        aluno_id = int((event.get("pathParameters") or {}).get("id", 0))
        if not aluno_id:
            return resp(400, {"erro": "id do aluno inválido"})

        if rota.startswith("POST") and rota.endswith("/arquivos/presign"):
            corpo = json.loads(event.get("body") or "{}")
            return criar_presign(aluno_id, corpo)
        if rota.startswith("GET") and rota.endswith("/arquivos"):
            return listar_arquivos(aluno_id)
        return resp(404, {"erro": f"rota não tratada: {rota}"})
    except json.JSONDecodeError:
        return resp(400, {"erro": "JSON inválido"})
    except Exception as e:  # vai para o CloudWatch com stack trace
        print(f"ERRO presign: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return resp(500, {"erro": "erro interno"})
