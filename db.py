"""
Turso database layer — all SQL lives here.
"""
import os
import json
import bcrypt
from turso_python import TursoConnection


def get_conn() -> TursoConnection:
    url = os.getenv("TURSO_DATABASE_URL")
    token = os.getenv("TURSO_AUTH_TOKEN")
    if not url or not token:
        raise RuntimeError("Configure TURSO_DATABASE_URL e TURSO_AUTH_TOKEN no .env")
    return TursoConnection(database_url=url, auth_token=token)


def _rows(result: dict) -> list[dict]:
    """Parse TursoConnection.execute_query result into list of dicts."""
    try:
        res = result.get("results", [{}])[0]
        cols = [c["name"] for c in res.get("response", {}).get("result", {}).get("cols", [])]
        rows = res.get("response", {}).get("result", {}).get("rows", [])
        out = []
        for row in rows:
            out.append({cols[i]: (v.get("value") if isinstance(v, dict) else v) for i, v in enumerate(row)})
        return out
    except Exception:
        return []


def _exec(conn: TursoConnection, sql: str, args=None):
    return conn.execute_query(sql, args or [])


# ─── SCHEMA ────────────────────────────────────────────────────────────────────

def init_schema():
    conn = get_conn()
    stmts = [
        """CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )""",
        """CREATE TABLE IF NOT EXISTS gastos (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            nome TEXT NOT NULL,
            valor REAL NOT NULL,
            data TEXT,
            categoria TEXT,
            tipo TEXT,
            mes INTEGER NOT NULL,
            ano INTEGER NOT NULL DEFAULT 2026,
            parcelas INTEGER DEFAULT 1,
            fixo INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        )""",
        """CREATE TABLE IF NOT EXISTS entradas (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            nome TEXT NOT NULL,
            valor REAL NOT NULL,
            data TEXT,
            mes INTEGER NOT NULL,
            ano INTEGER NOT NULL DEFAULT 2026,
            fixo INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        )""",
        """CREATE TABLE IF NOT EXISTS metas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            nome TEXT NOT NULL,
            total REAL NOT NULL,
            guardado REAL DEFAULT 0,
            data TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )""",
        """CREATE TABLE IF NOT EXISTS investimentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            mes INTEGER NOT NULL,
            ano INTEGER NOT NULL DEFAULT 2026,
            reserva REAL DEFAULT 0,
            fixa REAL DEFAULT 0,
            variavel REAL DEFAULT 0,
            UNIQUE(user_id, mes, ano)
        )""",
    ]
    for sql in stmts:
        _exec(conn, sql)


# ─── USERS ─────────────────────────────────────────────────────────────────────

def create_user(username: str, password: str) -> bool:
    try:
        conn = get_conn()
        h = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        _exec(conn, "INSERT INTO users (username, password_hash) VALUES (?, ?)", [username, h])
        return True
    except Exception:
        return False


def verify_user(username: str, password: str) -> dict | None:
    conn = get_conn()
    rows = _rows(_exec(conn, "SELECT id, username, password_hash FROM users WHERE username = ?", [username]))
    if not rows:
        return None
    user = rows[0]
    if bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        return {"id": user["id"], "username": user["username"]}
    return None


def user_exists(username: str) -> bool:
    conn = get_conn()
    rows = _rows(_exec(conn, "SELECT id FROM users WHERE username = ?", [username]))
    return len(rows) > 0


# ─── GASTOS ────────────────────────────────────────────────────────────────────

def get_gastos(user_id: int, mes: int, ano: int = 2026) -> list[dict]:
    conn = get_conn()
    return _rows(_exec(conn,
        "SELECT * FROM gastos WHERE user_id = ? AND mes = ? AND ano = ? ORDER BY created_at DESC",
        [user_id, mes, ano]
    ))


def get_fixos(user_id: int, mes: int, ano: int = 2026) -> list[dict]:
    """Returns fixos registered up to this month."""
    conn = get_conn()
    return _rows(_exec(conn,
        "SELECT * FROM gastos WHERE user_id = ? AND fixo = 1 AND ano = ? AND mes <= ? ORDER BY nome",
        [user_id, ano, mes]
    ))


def get_parcelas_ativas(user_id: int, ano: int = 2026) -> list[dict]:
    conn = get_conn()
    return _rows(_exec(conn,
        "SELECT * FROM gastos WHERE user_id = ? AND parcelas > 1 AND ano = ? ORDER BY created_at DESC",
        [user_id, ano]
    ))


def insert_gasto(user_id: int, gasto: dict):
    conn = get_conn()
    _exec(conn,
        "INSERT INTO gastos (id, user_id, nome, valor, data, categoria, tipo, mes, ano, parcelas, fixo) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        [gasto["id"], user_id, gasto["nome"], gasto["valor"], gasto.get("data"), gasto.get("categoria"),
         gasto.get("tipo"), gasto["mes"], gasto.get("ano", 2026), gasto.get("parcelas", 1), 1 if gasto.get("fixo") else 0]
    )


def delete_gasto(gasto_id: str, user_id: int):
    conn = get_conn()
    _exec(conn, "DELETE FROM gastos WHERE id = ? AND user_id = ?", [gasto_id, user_id])


# ─── ENTRADAS ──────────────────────────────────────────────────────────────────

def get_entradas(user_id: int, mes: int, ano: int = 2026) -> list[dict]:
    conn = get_conn()
    return _rows(_exec(conn,
        "SELECT * FROM entradas WHERE user_id = ? AND ano = ? AND (mes = ? OR (fixo = 1 AND mes <= ?)) ORDER BY created_at DESC",
        [user_id, ano, mes, mes]
    ))


def insert_entrada(user_id: int, entrada: dict):
    conn = get_conn()
    _exec(conn,
        "INSERT INTO entradas (id, user_id, nome, valor, data, mes, ano, fixo) VALUES (?,?,?,?,?,?,?,?)",
        [entrada["id"], user_id, entrada["nome"], entrada["valor"], entrada.get("data"),
         entrada["mes"], entrada.get("ano", 2026), 1 if entrada.get("fixo") else 0]
    )


def delete_entrada(entrada_id: str, user_id: int):
    conn = get_conn()
    _exec(conn, "DELETE FROM entradas WHERE id = ? AND user_id = ?", [entrada_id, user_id])


# ─── METAS ─────────────────────────────────────────────────────────────────────

def get_metas(user_id: int) -> list[dict]:
    conn = get_conn()
    return _rows(_exec(conn, "SELECT * FROM metas WHERE user_id = ? ORDER BY created_at DESC", [user_id]))


def insert_meta(user_id: int, meta: dict):
    conn = get_conn()
    _exec(conn,
        "INSERT INTO metas (user_id, nome, total, guardado, data) VALUES (?,?,?,?,?)",
        [user_id, meta["nome"], meta["total"], meta.get("guardado", 0), meta.get("data")]
    )


def update_meta_guardado(meta_id: int, novo_valor: float, user_id: int):
    conn = get_conn()
    _exec(conn, "UPDATE metas SET guardado = ? WHERE id = ? AND user_id = ?", [novo_valor, meta_id, user_id])


def delete_meta(meta_id: int, user_id: int):
    conn = get_conn()
    _exec(conn, "DELETE FROM metas WHERE id = ? AND user_id = ?", [meta_id, user_id])


# ─── INVESTIMENTOS ─────────────────────────────────────────────────────────────

def get_investimentos(user_id: int, ano: int = 2026) -> list[dict]:
    conn = get_conn()
    return _rows(_exec(conn,
        "SELECT * FROM investimentos WHERE user_id = ? AND ano = ? ORDER BY mes",
        [user_id, ano]
    ))


def upsert_investimento(user_id: int, mes: int, ano: int, reserva: float, fixa: float, variavel: float):
    conn = get_conn()
    _exec(conn,
        """INSERT INTO investimentos (user_id, mes, ano, reserva, fixa, variavel)
           VALUES (?,?,?,?,?,?)
           ON CONFLICT(user_id, mes, ano) DO UPDATE SET
             reserva=excluded.reserva, fixa=excluded.fixa, variavel=excluded.variavel""",
        [user_id, mes, ano, reserva, fixa, variavel]
    )
