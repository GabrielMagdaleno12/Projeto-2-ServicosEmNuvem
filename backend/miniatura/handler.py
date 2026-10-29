"""Lambda `miniatura` (RF-03) - disparada pelo evento S3 ObjectCreated no prefixo uploads/.

Fluxo: lê o objeto -> (se imagem) gera miniatura 150x150 JPEG em thumbs/ -> grava chave e metadados no RDS.
PDF (atestado): só registra o tamanho.
Tabela `arquivo` (schema existente): atualiza chave_thumb, tamanho_bytes, largura, altura.
Erros: ficam no CloudWatch Logs (HU-07).

Variáveis de ambiente: DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
Roda na VPC. Acessa o S3 pelo VPC Gateway Endpoint (sem NAT).
"""
import io
import logging
import os
import traceback
import urllib.parse

import boto3
import pymysql
from PIL import Image, ImageOps

log = logging.getLogger()
log.setLevel(logging.INFO)

s3 = boto3.client("s3")
PREFIXO_ORIGEM = "uploads/"
PREFIXO_MINIATURA = "thumbs/"   # prefixo DIFERENTE do gatilho: evita loop infinito de eventos
TAMANHO_MINIATURA = (150, 150)
MAX_BYTES = 5 * 1024 * 1024

_conn = None


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
        autocommit=True,
    )
    return _conn


def gerar_miniatura(dados: bytes):
    """Recebe os bytes da imagem. Devolve (bytes_jpeg, largura_original, altura_original)."""
    img = Image.open(io.BytesIO(dados))
    img = ImageOps.exif_transpose(img)          # respeita a rotação da foto de celular
    largura, altura = img.size
    img = img.convert("RGB")                    # PNG com transparência -> JPEG
    img = ImageOps.fit(img, TAMANHO_MINIATURA)  # recorta e redimensiona para 150x150 exatos
    saida = io.BytesIO()
    img.save(saida, "JPEG", quality=85)
    return saida.getvalue(), largura, altura


def chave_da_miniatura(chave_original: str) -> str:
    # uploads/12/abc.png -> thumbs/12/abc.jpg
    resto = chave_original[len(PREFIXO_ORIGEM):]
    base = resto.rsplit(".", 1)[0]
    return f"{PREFIXO_MINIATURA}{base}.jpg"


def processar(bucket, chave):
    log.info("Novo objeto: s3://%s/%s", bucket, chave)

    if not chave.startswith(PREFIXO_ORIGEM):
        log.info("Ignorado (fora de %s): %s", PREFIXO_ORIGEM, chave)
        return

    head = s3.head_object(Bucket=bucket, Key=chave)
    tamanho = head["ContentLength"]
    tipo = head.get("ContentType", "")

    # A URL pré-assinada não limita o tamanho; a validação real do limite é aqui.
    if tamanho > MAX_BYTES:
        s3.delete_object(Bucket=bucket, Key=chave)
        n = conectar().cursor().execute("DELETE FROM arquivo WHERE chave_s3=%s", (chave,))
        log.error("Arquivo %s com %s bytes excede 5 MB: removido do S3 e do RDS (linhas: %s)", chave, tamanho, n)
        return

    cur = conectar().cursor()

    if tipo.startswith("image/"):
        try:
            corpo = s3.get_object(Bucket=bucket, Key=chave)["Body"].read()
            miniatura, largura, altura = gerar_miniatura(corpo)
        except Exception:
            # imagem corrompida: registra o tamanho (sai de "pendente") e deixa o erro no CloudWatch
            log.error("Falha ao gerar miniatura de %s:\n%s", chave, traceback.format_exc())
            cur.execute("UPDATE arquivo SET tamanho_bytes=%s WHERE chave_s3=%s", (tamanho, chave))
            return
        chave_mini = chave_da_miniatura(chave)
        s3.put_object(Bucket=bucket, Key=chave_mini, Body=miniatura, ContentType="image/jpeg")
        n = cur.execute(
            "UPDATE arquivo SET tamanho_bytes=%s, largura=%s, altura=%s, chave_thumb=%s WHERE chave_s3=%s",
            (tamanho, largura, altura, chave_mini, chave),
        )
        log.info("Miniatura criada: %s (%sx%s, %s bytes) | linhas atualizadas no RDS: %s",
                 chave_mini, largura, altura, tamanho, n)
    else:
        n = cur.execute("UPDATE arquivo SET tamanho_bytes=%s WHERE chave_s3=%s", (tamanho, chave))
        log.info("Arquivo não-imagem registrado: %s (%s bytes) | linhas atualizadas no RDS: %s", chave, tamanho, n)

    if n == 0:
        # objeto chegou ao S3 sem linha no RDS (ex.: upload manual pelo console)
        log.warning("Nenhuma linha em `arquivo` com chave_s3=%s - nada foi atualizado", chave)


def handler(event, context):
    for rec in event.get("Records", []):
        bucket = rec["s3"]["bucket"]["name"]
        chave = urllib.parse.unquote_plus(rec["s3"]["object"]["key"])  # S3 codifica espaços como '+'
        try:
            processar(bucket, chave)
        except Exception as e:
            log.error("Falha ao processar %s: %s: %s\n%s", chave, type(e).__name__, e, traceback.format_exc())
    return {"ok": True}
