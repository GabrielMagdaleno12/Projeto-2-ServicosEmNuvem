"""Lambda CRUD (RF-01): planos, alunos, aulas e inscrições.

Handler único atrás de um API Gateway HTTP API (payload v2.0).
Configuração via variáveis de ambiente da Lambda (nada de segredo no Git):
  DB_HOST, DB_USER, DB_PASSWORD, DB_NAME (padrão: academia)
Dependência: PyMySQL (empacotar no zip, ver README, passos 4 e 5).
"""
import json
import os
import re
from decimal import Decimal
from datetime import date, datetime, time, timedelta

import pymysql
from pymysql.err import IntegrityError

HEADERS = {
    "Content-Type": "application/json; charset=utf-8",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}

# Conexão criada fora do handler para ser reaproveitada entre invocações (ADR-001).
_conn = None


def get_conn():
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
        password=os.environ["DB_PASSWORD"],
        database=os.environ.get("DB_NAME", "academia"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
        connect_timeout=5,
    )
    return _conn


def _default(o):
    if isinstance(o, Decimal):
        return float(o)
    if isinstance(o, (datetime, date)):
        return o.isoformat()
    if isinstance(o, (time, timedelta)):
        total = int(o.total_seconds()) if isinstance(o, timedelta) else o.hour * 3600 + o.minute * 60
        return "%02d:%02d" % (total // 3600, (total % 3600) // 60)
    raise TypeError(type(o))


def resp(status, body=None):
    return {
        "statusCode": status,
        "headers": HEADERS,
        "body": "" if body is None else json.dumps(body, default=_default, ensure_ascii=False),
    }


class HttpError(Exception):
    def __init__(self, status, msg):
        self.status, self.msg = status, msg


def required(data, fields):
    missing = [f for f in fields if data.get(f) in (None, "")]
    if missing:
        raise HttpError(400, "Campo(s) obrigatório(s): " + ", ".join(missing))


def valid_cpf(cpf):
    cpf = re.sub(r"\D", "", cpf or "")
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return None
    for n in (9, 10):
        s = sum(int(cpf[i]) * (n + 1 - i) for i in range(n))
        if int(cpf[n]) != (s * 10 % 11) % 10:
            return None
    return cpf


# ---------------------------------------------------------------- planos
def planos_list(cur, **_):
    cur.execute("SELECT * FROM plano ORDER BY id")
    return 200, cur.fetchall()


def _check_plano(data):
    required(data, ["nome", "valor_mensal"])
    try:
        valor = Decimal(str(data["valor_mensal"]))
        meses = int(data.get("duracao_meses") or 1)
    except Exception:
        raise HttpError(400, "valor_mensal/duracao_meses inválidos")
    if valor <= 0 or meses <= 0:
        raise HttpError(400, "valor_mensal e duracao_meses devem ser positivos")
    return data["nome"].strip(), valor, meses


def planos_create(cur, body, **_):
    nome, valor, meses = _check_plano(body)
    cur.execute("INSERT INTO plano (nome, valor_mensal, duracao_meses) VALUES (%s,%s,%s)",
                (nome, valor, meses))
    return 201, {"id": cur.lastrowid}


def planos_update(cur, body, id, **_):
    nome, valor, meses = _check_plano(body)
    cur.execute("UPDATE plano SET nome=%s, valor_mensal=%s, duracao_meses=%s WHERE id=%s",
                (nome, valor, meses, id))
    return 200, {"id": id}


def planos_delete(cur, id, **_):
    cur.execute("SELECT COUNT(*) AS n FROM aluno WHERE plano_id=%s", (id,))
    n = cur.fetchone()["n"]
    if n:
        raise HttpError(409, "Plano em uso por %d aluno(s)" % n)
    cur.execute("DELETE FROM plano WHERE id=%s", (id,))
    return 204, None


# ---------------------------------------------------------------- alunos
def alunos_list(cur, query, **_):
    busca = (query or {}).get("busca")
    sql = ("SELECT a.id, a.nome, a.cpf, a.email, a.telefone, a.plano_id, p.nome AS plano "
           "FROM aluno a JOIN plano p ON p.id = a.plano_id")
    args = ()
    if busca:
        sql += " WHERE a.nome LIKE %s"
        args = ("%" + busca + "%",)
    cur.execute(sql + " ORDER BY a.nome", args)
    return 200, cur.fetchall()


def alunos_get(cur, id, **_):
    cur.execute("SELECT a.*, p.nome AS plano FROM aluno a "
                "JOIN plano p ON p.id=a.plano_id WHERE a.id=%s", (id,))
    aluno = cur.fetchone()
    if not aluno:
        raise HttpError(404, "Aluno não encontrado")
    cur.execute("SELECT * FROM arquivo WHERE aluno_id=%s", (id,))
    aluno["arquivos"] = cur.fetchall()
    cur.execute("SELECT i.id, au.modalidade, au.dia_semana, au.horario FROM inscricao i "
                "JOIN aula au ON au.id=i.aula_id WHERE i.aluno_id=%s", (id,))
    aluno["inscricoes"] = cur.fetchall()
    return 200, aluno


def _check_aluno(data):
    required(data, ["nome", "cpf", "plano_id"])
    cpf = valid_cpf(data["cpf"])
    if not cpf:
        raise HttpError(400, "CPF inválido")
    return cpf


def alunos_create(cur, body, **_):
    cpf = _check_aluno(body)
    try:
        cur.execute("INSERT INTO aluno (nome, cpf, email, telefone, plano_id) VALUES (%s,%s,%s,%s,%s)",
                    (body["nome"].strip(), cpf, body.get("email"), body.get("telefone"), body["plano_id"]))
    except IntegrityError as e:
        if e.args[0] == 1062:
            raise HttpError(409, "CPF já cadastrado")
        if e.args[0] == 1452:
            raise HttpError(400, "Plano inexistente")
        raise
    return 201, {"id": cur.lastrowid}


def alunos_update(cur, body, id, **_):
    cpf = _check_aluno(body)
    try:
        cur.execute("UPDATE aluno SET nome=%s, cpf=%s, email=%s, telefone=%s, plano_id=%s WHERE id=%s",
                    (body["nome"].strip(), cpf, body.get("email"), body.get("telefone"), body["plano_id"], id))
    except IntegrityError as e:
        if e.args[0] == 1062:
            raise HttpError(409, "CPF já cadastrado")
        if e.args[0] == 1452:
            raise HttpError(400, "Plano inexistente")
        raise
    return 200, {"id": id}


def alunos_delete(cur, id, **_):
    # inscrições e arquivos saem junto por ON DELETE CASCADE
    cur.execute("DELETE FROM aluno WHERE id=%s", (id,))
    if cur.rowcount == 0:
        raise HttpError(404, "Aluno não encontrado")
    return 204, None


# ---------------------------------------------------------------- aulas
def aulas_list(cur, **_):
    cur.execute("SELECT a.*, a.vagas - COUNT(i.id) AS vagas_restantes "
                "FROM aula a LEFT JOIN inscricao i ON i.aula_id=a.id "
                "GROUP BY a.id ORDER BY a.id")
    return 200, cur.fetchall()


def _check_aula(data):
    required(data, ["modalidade", "dia_semana", "horario", "vagas"])
    try:
        vagas = int(data["vagas"])
    except Exception:
        raise HttpError(400, "vagas inválido")
    if vagas <= 0:
        raise HttpError(400, "vagas deve ser maior que zero")
    return vagas


def aulas_create(cur, body, **_):
    vagas = _check_aula(body)
    cur.execute("INSERT INTO aula (modalidade, dia_semana, horario, instrutor, vagas) VALUES (%s,%s,%s,%s,%s)",
                (body["modalidade"], body["dia_semana"], body["horario"], body.get("instrutor"), vagas))
    return 201, {"id": cur.lastrowid}


def aulas_update(cur, body, id, **_):
    vagas = _check_aula(body)
    cur.execute("UPDATE aula SET modalidade=%s, dia_semana=%s, horario=%s, instrutor=%s, vagas=%s WHERE id=%s",
                (body["modalidade"], body["dia_semana"], body["horario"], body.get("instrutor"), vagas, id))
    return 200, {"id": id}


def aulas_delete(cur, id, **_):
    cur.execute("DELETE FROM aula WHERE id=%s", (id,))
    if cur.rowcount == 0:
        raise HttpError(404, "Aula não encontrada")
    return 204, None


# ---------------------------------------------------------------- inscrições
def inscricoes_create(cur, body, id, **_):
    required(body, ["aluno_id"])
    # trava a linha da aula: a checagem de vagas e o INSERT ficam atômicos
    cur.execute("SELECT vagas FROM aula WHERE id=%s FOR UPDATE", (id,))
    aula = cur.fetchone()
    if not aula:
        raise HttpError(404, "Aula não encontrada")
    cur.execute("SELECT COUNT(*) AS n FROM inscricao WHERE aula_id=%s", (id,))
    if cur.fetchone()["n"] >= aula["vagas"]:
        raise HttpError(409, "Aula lotada")
    try:
        cur.execute("INSERT INTO inscricao (aluno_id, aula_id) VALUES (%s,%s)", (body["aluno_id"], id))
    except IntegrityError as e:
        if e.args[0] == 1062:
            raise HttpError(409, "Aluno já inscrito nesta aula")
        if e.args[0] == 1452:
            raise HttpError(400, "Aluno inexistente")
        raise
    return 201, {"id": cur.lastrowid}


def inscricoes_delete(cur, id, **_):
    cur.execute("DELETE FROM inscricao WHERE id=%s", (id,))
    if cur.rowcount == 0:
        raise HttpError(404, "Inscrição não encontrada")
    return 204, None


# ---------------------------------------------------------------- rotas
ROUTES = {
    ("GET", "/planos"): planos_list,
    ("POST", "/planos"): planos_create,
    ("PUT", "/planos/{id}"): planos_update,
    ("DELETE", "/planos/{id}"): planos_delete,
    ("GET", "/alunos"): alunos_list,
    ("GET", "/alunos/{id}"): alunos_get,
    ("POST", "/alunos"): alunos_create,
    ("PUT", "/alunos/{id}"): alunos_update,
    ("DELETE", "/alunos/{id}"): alunos_delete,
    ("GET", "/aulas"): aulas_list,
    ("POST", "/aulas"): aulas_create,
    ("PUT", "/aulas/{id}"): aulas_update,
    ("DELETE", "/aulas/{id}"): aulas_delete,
    ("POST", "/aulas/{id}/inscricoes"): inscricoes_create,
    ("DELETE", "/inscricoes/{id}"): inscricoes_delete,
}


def lambda_handler(event, context):
    method = event["requestContext"]["http"]["method"]
    if method == "OPTIONS":
        return resp(204)

    # routeKey vem como "GET /alunos/{id}"
    route_key = event.get("routeKey", "")
    path = route_key.split(" ", 1)[1] if " " in route_key else event.get("rawPath", "")
    fn = ROUTES.get((method, path))
    if not fn:
        return resp(404, {"erro": "Rota não encontrada"})

    try:
        body = json.loads(event["body"]) if event.get("body") else {}
    except ValueError:
        return resp(400, {"erro": "JSON inválido"})

    params = event.get("pathParameters") or {}
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            status, payload = fn(cur=cur, body=body, query=event.get("queryStringParameters"),
                                 id=params.get("id"))
        conn.commit()
        return resp(status, payload)
    except HttpError as e:
        if _conn:
            _conn.rollback()
        return resp(e.status, {"erro": e.msg})
    except Exception as e:  # vai para o CloudWatch Logs
        print("ERRO:", repr(e))
        if _conn:
            try:
                _conn.rollback()
            except Exception:
                pass
        return resp(500, {"erro": "Erro interno"})
