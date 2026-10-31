"""Lambda de uso único: aplica os scripts versionados em sql/ no RDS privado.

Como o RDS não tem acesso público, a própria Lambda (dentro da VPC, com sg-lambda)
roda o schema e o seed. Os .sql são copiados para o zip na criação da Lambda (ver README, passo 4).
Idempotente no schema (CREATE ... IF NOT EXISTS); o seed só roda se plano estiver vazio.
"""
import os
import pymysql

SQL_DIR = os.path.join(os.path.dirname(__file__), "sql")


def split_statements(text):
    lines = [l for l in text.splitlines() if not l.strip().startswith("--")]
    return [s.strip() for s in "\n".join(lines).split(";") if s.strip()]


def lambda_handler(event, context):
    conn = pymysql.connect(host=os.environ["DB_HOST"], user=os.environ["DB_USER"],
                           password=os.environ["DB_PASSWORD"], charset="utf8mb4",
                           autocommit=True, connect_timeout=10)
    done = []
    with conn.cursor() as cur:
        for name in sorted(os.listdir(SQL_DIR)):
            if not name.endswith(".sql"):
                continue
            if name.startswith("02_"):
                cur.execute("USE academia")
                cur.execute("SELECT COUNT(*) FROM plano")
                if cur.fetchone()[0] > 0:
                    done.append(name + " (ignorado: já há dados)")
                    continue
            with open(os.path.join(SQL_DIR, name), encoding="utf-8") as f:
                for stmt in split_statements(f.read()):
                    cur.execute(stmt)
            done.append(name)
    conn.close()
    return {"aplicados": done}
