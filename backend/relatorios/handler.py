"""Lambda `relatorios` (RF-04).

Rotas (API Gateway HTTP API, payload v2):
  GET /relatorios/ocupacao-aulas    -> HU-08 (JOIN + GROUP BY)
  GET /relatorios/alunos-por-plano  -> HU-09 (JOIN + GROUP BY)

Variáveis de ambiente: DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
"""
import json
import os
from decimal import Decimal

import pymysql

HEADERS = {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"}

# LEFT JOIN: aula/plano sem ninguém aparece com 0 (exigência dos critérios de aceite).
SQL_OCUPACAO = """
SELECT a.id, a.modalidade, a.dia_semana, a.horario, a.vagas,
       COUNT(i.id) AS inscritos,
       ROUND(COUNT(i.id) / NULLIF(a.vagas, 0) * 100, 1) AS ocupacao_pct
FROM aula a
LEFT JOIN inscricao i ON i.aula_id = a.id
GROUP BY a.id, a.modalidade, a.dia_semana, a.horario, a.vagas
ORDER BY ocupacao_pct DESC, a.id
"""

SQL_ALUNOS_POR_PLANO = """
SELECT p.id, p.nome, p.valor_mensal,
       COUNT(al.id) AS alunos,
       COUNT(al.id) * p.valor_mensal AS receita_estimada
FROM plano p
LEFT JOIN aluno al ON al.plano_id = p.id
GROUP BY p.id, p.nome, p.valor_mensal
ORDER BY alunos DESC, p.nome
"""

ROTAS = {
    "/relatorios/ocupacao-aulas": SQL_OCUPACAO,
    "/relatorios/alunos-por-plano": SQL_ALUNOS_POR_PLANO,
}

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
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )
    return _conn


def para_json(o):
    if isinstance(o, Decimal):
        return float(o)   # DECIMAL do MySQL -> número (e não string) no JSON
    return str(o)         # time, date, datetime


def resp(status, corpo):
    return {"statusCode": status, "headers": HEADERS, "body": json.dumps(corpo, default=para_json)}


def handler(event, context):
    caminho = event.get("rawPath", "")
    # se houver stage na URL (ex.: /prod/relatorios/...), pega só a parte da rota
    for rota, sql in ROTAS.items():
        if caminho.endswith(rota):
            try:
                cur = conectar().cursor()
                cur.execute(sql)
                linhas = cur.fetchall()
                print(f"relatorio {rota}: {len(linhas)} linhas")
                return resp(200, linhas)
            except Exception as e:
                print(f"ERRO relatorios {rota}: {type(e).__name__}: {e}")
                return resp(500, {"erro": "erro ao gerar relatório"})
    return resp(404, {"erro": f"rota não encontrada: {caminho}"})
