"""
Notas da Nuvem — aplicação de exemplo da Aula 06 (Segurança de Rede em Nuvem I)

Uma aplicação Flask minimalista, propositalmente simples, para o desafio de
containerização e infraestrutura da disciplina Segurança para Computação em
Nuvem (CESAR School). Ela guarda "notas" (texto curto) em uma tabela
PostgreSQL — o objetivo NÃO é a aplicação em si, é a infraestrutura AWS que
vai hospedá-la (EC2 em subnet privada, RDS PostgreSQL em subnet privada,
acesso via bastion host, imagem puxada do ECR via VPC Endpoint de Interface).

Toda a configuração de banco de dados vem de variáveis de ambiente — é isso
que você vai apontar para o seu RDS quando configurar a instância EC2.
Nenhuma credencial fica gravada no código-fonte (revise a Aula 05 se tiver
dúvida sobre por que isso importa).
"""
import os
import time
from datetime import datetime, timezone

import psycopg2
import psycopg2.extras
from flask import Flask, jsonify, redirect, render_template, request, url_for

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Configuração via variáveis de ambiente (nunca hardcode credenciais aqui)
# ---------------------------------------------------------------------------
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "notasdb")
DB_USER = os.environ.get("DB_USER", "notas_app")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
APP_PORT = int(os.environ.get("APP_PORT", "8080"))


def get_connection():
    """Abre uma nova conexão com o PostgreSQL (RDS em produção)."""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        connect_timeout=5,
    )


def wait_for_db(max_attempts=10, delay_seconds=3):
    """Tenta conectar ao banco várias vezes antes de desistir.

    Útil tanto localmente (o container do Postgres pode demorar alguns
    segundos para aceitar conexões) quanto na AWS (a instância RDS pode
    ainda estar terminando de inicializar quando a EC2 sobe pela primeira
    vez).
    """
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            conn = get_connection()
            conn.close()
            print(f"[notas-da-nuvem] conexão com o banco OK (tentativa {attempt})")
            return True
        except Exception as exc:  # noqa: BLE001 — log simples é suficiente aqui
            last_error = exc
            print(f"[notas-da-nuvem] tentativa {attempt}/{max_attempts} falhou: {exc}")
            time.sleep(delay_seconds)
    print(f"[notas-da-nuvem] não foi possível conectar ao banco: {last_error}")
    return False


def ensure_schema():
    """Cria a tabela de notas se ela ainda não existir."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS notas (
                    id SERIAL PRIMARY KEY,
                    texto TEXT NOT NULL,
                    criada_em TIMESTAMPTZ NOT NULL DEFAULT now()
                );
                """
            )
        conn.commit()


@app.route("/health")
def health():
    """Health-check simples: confirma que a app está de pé e fala com o banco.

    Bom endpoint para testar via túnel SSH pelo bastion antes de se
    preocupar com a interface web completa.
    """
    db_status = "ok"
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                cur.fetchone()
    except Exception as exc:  # noqa: BLE001
        db_status = f"erro: {exc}"

    return jsonify(
        {
            "app": "notas-da-nuvem",
            "status": "up",
            "database": db_status,
            "db_host": DB_HOST,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


@app.route("/")
def index():
    notas = []
    erro = None
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT id, texto, criada_em FROM notas ORDER BY id DESC;")
                notas = cur.fetchall()
    except Exception as exc:  # noqa: BLE001
        erro = str(exc)

    return render_template("index.html", notas=notas, erro=erro, db_host=DB_HOST)


@app.route("/notas", methods=["POST"])
def criar_nota():
    texto = request.form.get("texto", "").strip()
    if texto:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO notas (texto) VALUES (%s);", (texto,))
            conn.commit()
    return redirect(url_for("index"))


# Executado tanto em desenvolvimento (`python3 app.py`) quanto em produção
# (gunicorn importa este módulo e usa o objeto `app` — o bloco abaixo roda
# nos dois casos, porque fica no nível do módulo, não dentro do "__main__").
wait_for_db()
try:
    ensure_schema()
except Exception as exc:  # noqa: BLE001
    print(f"[notas-da-nuvem] aviso: não consegui garantir o schema ainda: {exc}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=APP_PORT)
