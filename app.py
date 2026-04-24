"""
Finanças 2026 — Streamlit Single-Page Application
Premium UX/UI
"""
import streamlit as st
import os
import uuid
import bcrypt
from datetime import datetime
from dotenv import load_dotenv
from turso_python import TursoConnection

load_dotenv()

# ==============================================================================
# 1. CONSTANTES E UTILITÁRIOS
# ==============================================================================
YEAR = 2026
MONTHS = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho',
          'Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']

CAT_ICONS = {
    'Mercado':'🛒','Necessidades':'🧴','Eletrônicos':'💻','Assinaturas':'📱',
    'Roupa':'👕','Beleza':'💄','Presentes':'🎁','Saúde':'💊',
    'Despesas eventuais':'⚡','Desenvolvimento':'📚','Uber/transporte':'🚗',
    'IFood/restaurante':'🍔','Lazer':'🎭','Aluguel':'🏠','Contas':'💡',
    'Fatura Cartão':'💳','Outros':'📦'
}

CATEGORIAS = list(CAT_ICONS.keys())
TIPOS = ['Débito','Pix','Dinheiro','Crédito 1','Crédito 2','Crédito 3','Crédito 4']

def uid() -> str:
    return str(uuid.uuid4())[:18]

def fmt(v) -> str:
    try:
        return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"

def card_html(title: str, value: str, sub: str = "", color: str = "inherit") -> str:
    return f"""
    <div class="fin-card">
        <div class="fin-card-title">{title}</div>
        <div style="font-size:1.8rem;font-weight:700;color:{color};letter-spacing:-0.5px;line-height:1">{value}</div>
        {f'<div style="font-size:12px;opacity:0.6;margin-top:6px">{sub}</div>' if sub else ''}
    </div>
    """

def progress_bar_html(pct: float, color: str = "#30d158", height: int = 6) -> str:
    pct = min(100, max(0, pct))
    return f"""
    <div style="height:{height}px;background:rgba(150,150,150,0.2);border-radius:{height//2}px;overflow:hidden;margin-top:8px">
        <div style="height:100%;width:{pct:.1f}%;background:{color};border-radius:{height//2}px;transition:width 0.5s ease"></div>
    </div>
    """

def section_header(title: str, subtitle: str = ""):
    st.markdown(f"""
    <div style="margin-bottom:1rem; margin-top: 1rem;">
        <div style="font-size:1.1rem;font-weight:700">{title}</div>
        {f'<div style="font-size:13px;opacity:0.6;margin-top:2px">{subtitle}</div>' if subtitle else ''}
    </div>
    """, unsafe_allow_html=True)

def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* Cards e Containers com estilo Glass/Tailwind */
    .fin-card {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(150, 150, 150, 0.2);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .fin-card:hover {
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.02);
    }
    .fin-card-title {
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        opacity: 0.6;
        margin-bottom: 0.75rem;
        font-weight: 600;
    }

    /* Linhas de listas */
    .fin-row {
        display: flex;
        align-items: center;
        padding: 12px 0;
        border-bottom: 1px solid rgba(150,150,150,0.1);
        font-size: 14px;
        gap: 12px;
    }
    .fin-row:last-child { border-bottom: none; }

    /* Ajustes Streamlit Nativos */
    [data-testid="stMetric"] {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(150, 150, 150, 0.2);
        border-radius: 16px;
        padding: 1.25rem !important;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
    }
    .stButton > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.2s;
    }
    [data-testid="stSidebar"] {
        border-right: 1px solid rgba(150, 150, 150, 0.1) !important;
    }
    
    /* Tags Tailwind-like */
    .badge {
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.025em;
    }
    .badge-green { background: rgba(48,209,88,0.15); color: #22c55e; }
    .badge-red { background: rgba(255,69,58,0.15); color: #ef4444; }
    
    #MainMenu, footer, header { visibility: hidden !important; }
    </style>
    """, unsafe_allow_html=True)


# ==============================================================================
# 2. CAMADA DE BANCO DE DADOS (TURSO)
# ==============================================================================
def get_conn() -> TursoConnection:
    url = os.getenv("TURSO_DATABASE_URL")
    token = os.getenv("TURSO_AUTH_TOKEN")
    if not url or not token:
        raise RuntimeError("Configure TURSO_DATABASE_URL e TURSO_AUTH_TOKEN no .env")
    return TursoConnection(database_url=url, auth_token=token)

def _rows(result: dict) -> list[dict]:
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

@st.cache_resource
def init_schema():
    try:
        conn = get_conn()
        stmts = [
            """CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, created_at TEXT DEFAULT (datetime('now')))""",
            """CREATE TABLE IF NOT EXISTS gastos (id TEXT PRIMARY KEY, user_id INTEGER NOT NULL, nome TEXT NOT NULL, valor REAL NOT NULL, data TEXT, categoria TEXT, tipo TEXT, mes INTEGER NOT NULL, ano INTEGER NOT NULL DEFAULT 2026, parcelas INTEGER DEFAULT 1, fixo INTEGER DEFAULT 0, created_at TEXT DEFAULT (datetime('now')))""",
            """CREATE TABLE IF NOT EXISTS entradas (id TEXT PRIMARY KEY, user_id INTEGER NOT NULL, nome TEXT NOT NULL, valor REAL NOT NULL, data TEXT, mes INTEGER NOT NULL, ano INTEGER NOT NULL DEFAULT 2026, fixo INTEGER DEFAULT 0, created_at TEXT DEFAULT (datetime('now')))""",
            """CREATE TABLE IF NOT EXISTS metas (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, nome TEXT NOT NULL, total REAL NOT NULL, guardado REAL DEFAULT 0, data TEXT, created_at TEXT DEFAULT (datetime('now')))""",
            """CREATE TABLE IF NOT EXISTS investimentos (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, mes INTEGER NOT NULL, ano INTEGER NOT NULL DEFAULT 2026, reserva REAL DEFAULT 0, fixa REAL DEFAULT 0, variavel REAL DEFAULT 0, UNIQUE(user_id, mes, ano))"""
        ]
        for sql in stmts: _exec(conn, sql)
        return True
    except Exception as e:
        return str(e)

# --- Autenticação ---
def create_user(username: str, password: str) -> bool:
    try:
        conn = get_conn()
        h = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        _exec(conn, "INSERT INTO users (username, password_hash) VALUES (?, ?)", [username, h])
        return True
    except Exception: return False

def verify_user(username: str, password: str) -> dict | None:
    conn = get_conn()
    rows = _rows(_exec(conn, "SELECT id, username, password_hash FROM users WHERE username = ?", [username]))
    if not rows: return None
    user = rows[0]
    if bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        return {"id": user["id"], "username": user["username"]}
    return None

def user_exists(username: str) -> bool:
    return len(_rows(_exec(get_conn(), "SELECT id FROM users WHERE username = ?", [username]))) > 0

# --- CRUD Financeiro ---
def get_gastos(user_id: int, mes: int, ano: int = 2026): return _rows(_exec(get_conn(), "SELECT * FROM gastos WHERE user_id = ? AND mes = ? AND ano = ? ORDER BY created_at DESC", [user_id, mes, ano]))
def get_fixos(user_id: int, mes: int, ano: int = 2026): return _rows(_exec(get_conn(), "SELECT * FROM gastos WHERE user_id = ? AND fixo = 1 AND ano = ? AND mes <= ? ORDER BY nome", [user_id, ano, mes]))
def get_parcelas_ativas(user_id: int, ano: int = 2026): return _rows(_exec(get_conn(), "SELECT * FROM gastos WHERE user_id = ? AND parcelas > 1 AND ano = ? ORDER BY created_at DESC", [user_id, ano]))
def insert_gasto(user_id: int, g: dict): _exec(get_conn(), "INSERT INTO gastos (id, user_id, nome, valor, data, categoria, tipo, mes, ano, parcelas, fixo) VALUES (?,?,?,?,?,?,?,?,?,?,?)", [g["id"], user_id, g["nome"], g["valor"], g.get("data"), g.get("categoria"), g.get("tipo"), g["mes"], g.get("ano", 2026), g.get("parcelas", 1), 1 if g.get("fixo") else 0])
def delete_gasto(gasto_id: str, user_id: int): _exec(get_conn(), "DELETE FROM gastos WHERE id = ? AND user_id = ?", [gasto_id, user_id])

def get_entradas(user_id: int, mes: int, ano: int = 2026): return _rows(_exec(get_conn(), "SELECT * FROM entradas WHERE user_id = ? AND ano = ? AND (mes = ? OR (fixo = 1 AND mes <= ?)) ORDER BY created_at DESC", [user_id, ano, mes, mes]))
def insert_entrada(user_id: int, e: dict): _exec(get_conn(), "INSERT INTO entradas (id, user_id, nome, valor, data, mes, ano, fixo) VALUES (?,?,?,?,?,?,?,?)", [e["id"], user_id, e["nome"], e["valor"], e.get("data"), e["mes"], e.get("ano", 2026), 1 if e.get("fixo") else 0])
def delete_entrada(entrada_id: str, user_id: int): _exec(get_conn(), "DELETE FROM entradas WHERE id = ? AND user_id = ?", [entrada_id, user_id])

def get_metas(user_id: int): return _rows(_exec(get_conn(), "SELECT * FROM metas WHERE user_id = ? ORDER BY created_at DESC", [user_id]))
def insert_meta(user_id: int, m: dict): _exec(get_conn(), "INSERT INTO metas (user_id, nome, total, guardado, data) VALUES (?,?,?,?,?)", [user_id, m["nome"], m["total"], m.get("guardado", 0), m.get("data")])
def update_meta_guardado(meta_id: int, novo_valor: float, user_id: int): _exec(get_conn(), "UPDATE metas SET guardado = ? WHERE id = ? AND user_id = ?", [novo_valor, meta_id, user_id])
def delete_meta(meta_id: int, user_id: int): _exec(get_conn(), "DELETE FROM metas WHERE id = ? AND user_id = ?", [meta_id, user_id])

def get_investimentos(user_id: int, ano: int = 2026): return _rows(_exec(get_conn(), "SELECT * FROM investimentos WHERE user_id = ? AND ano = ? ORDER BY mes", [user_id, ano]))
def upsert_investimento(user_id: int, mes: int, ano: int, res: float, fix: float, var: float): _exec(get_conn(), "INSERT INTO investimentos (user_id, mes, ano, reserva, fixa, variavel) VALUES (?,?,?,?,?,?) ON CONFLICT(user_id, mes, ano) DO UPDATE SET reserva=excluded.reserva, fixa=excluded.fixa, variavel=excluded.variavel", [user_id, mes, ano, res, fix, var])


# ==============================================================================
# 3. INTERFACE E TELAS (VIEWS)
# ==============================================================================
st.set_page_config(page_title=f"Finanças {YEAR}", page_icon="💰", layout="wide", initial_sidebar_state="expanded")
inject_css()
schema_ok = init_schema()

# --- Configuração de Sessão ---
if "user" not in st.session_state: st.session_state.user = None
if "mes_atual" not in st.session_state: st.session_state.mes_atual = datetime.now().month - 1
if "page" not in st.session_state: st.session_state.page = "dashboard"


def login_page():
    st.markdown("""
    <div style="text-align:center;padding:4rem 0 2rem">
        <div style="font-size:3.5rem;margin-bottom:0.5rem">💰</div>
        <div style="font-size:2.5rem;font-weight:800;letter-spacing:-1px">Finanças <span style="color:#30d158">2026</span></div>
        <div style="font-size:15px;opacity:0.6;margin-top:6px">Seu controle financeiro inteligente</div>
    </div>
    """, unsafe_allow_html=True)

    if schema_ok is not True:
        st.error(f"❌ Erro de BD: {schema_ok}")
        return

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        tab1, tab2 = st.tabs(["🔐 Entrar", "📝 Criar Conta"])
        with tab1:
            with st.form("form_login"):
                username = st.text_input("Usuário", placeholder="seu_usuario")
                password = st.text_input("Senha", type="password", placeholder="••••••••")
                if st.form_submit_button("Acessar Painel →", use_container_width=True, type="primary"):
                    user = verify_user(username, password)
                    if user:
                        st.session_state.user = user
                        st.rerun()
                    else: st.error("Dados incorretos.")
        with tab2:
            with st.form("form_register"):
                new_user = st.text_input("Usuário", key="reg_user")
                new_pass = st.text_input("Senha", type="password", key="reg_pass")
                if st.form_submit_button("Criar Conta", use_container_width=True):
                    if len(new_pass) < 6: st.error("Senha curta.")
                    elif user_exists(new_user): st.error("Usuário existe.")
                    else:
                        create_user(new_user, new_pass)
                        st.success("Conta criada! Faça login.")

def render_sidebar():
    user = st.session_state.user
    mes = st.session_state.mes_atual

    with st.sidebar:
        st.markdown(f"""
        <div style="padding:0.5rem 0 1.5rem">
            <div style="font-size:1.4rem;font-weight:800;letter-spacing:-0.5px">Finanças <span style="color:#30d158">2026</span></div>
            <div style="font-size:13px;opacity:0.6;margin-top:2px">👤 {user['username']}</div>
        </div>
        """, unsafe_allow_html=True)

        pages = {
            "🏠 Dashboard": "dashboard",
            "📅 Lançamentos": "mes",
            "💳 Parcelas": "parcelas",
            "🎯 Metas & Invest.": "metas",
            "🗓️ Anual": "anual",
        }

        for label, key in pages.items():
            if st.button(label, key=f"nav_{key}", use_container_width=True, type="primary" if st.session_state.page == key else "secondary"):
                st.session_state.page = key
                st.rerun()

        st.markdown("<hr style='opacity:0.2'>", unsafe_allow_html=True)
        st.markdown("**📆 Navegar nos Meses**")
        month_cols = st.columns(3)
        for i, m in enumerate(MONTHS):
            with month_cols[i % 3]:
                active = "🟢" if i == mes else ""
                if st.button(f"{active}{m[:3]}", key=f"m_{i}", use_container_width=True):
                    st.session_state.mes_atual = i
                    st.rerun()

        st.markdown("<hr style='opacity:0.2'>", unsafe_allow_html=True)
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.user = None
            st.rerun()


# --- View: Dashboard ---
def render_dashboard():
    user_id = st.session_state.user["id"]
    mes = st.session_state.mes_atual

    st.markdown(f"""
    <div style="padding:1rem 0 2rem">
        <div style="font-size:2.2rem;font-weight:800;letter-spacing:-1px">Visão Geral</div>
        <div style="font-size:15px;opacity:0.6;margin-top:4px">{MONTHS[mes]} de {YEAR}</div>
    </div>
    """, unsafe_allow_html=True)

    gastos = get_gastos(user_id, mes)
    fixos = get_fixos(user_id, mes)
    entradas = get_entradas(user_id, mes)
    parcelas_ativas = get_parcelas_ativas(user_id)

    tot_gastos = sum(float(g["valor"]) for g in gastos) + sum(float(f["valor"]) for f in fixos)
    tot_parc = sum(float(p["valor"])/int(p["parcelas"]) for p in parcelas_ativas if int(p["mes"]) <= mes < int(p["mes"])+int(p["parcelas"]))
    tot_despesas = tot_gastos + tot_parc
    tot_entradas = sum(float(e["valor"]) for e in entradas)
    saldo = tot_entradas - tot_despesas

    # KPIs
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Entradas", fmt(tot_entradas))
    k2.metric("Despesas", fmt(tot_despesas))
    k3.metric("Saldo Líquido", fmt(saldo), "Positivo" if saldo >= 0 else "Negativo", delta_color="normal" if saldo >= 0 else "inverse")
    k4.metric("Faturas/Cartão", fmt(tot_parc))

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns([2, 1])

    with c1:
        section_header("Adicionar Rápido")
        with st.form("quick_add", clear_on_submit=True):
            col_a, col_b, col_c = st.columns([3, 2, 2])
            nome = col_a.text_input("Descrição", placeholder="Ex: Supermercado")
            valor = col_b.number_input("Valor (R$)", min_value=0.00, step=10.0)
            tipo_mov = col_c.selectbox("Tipo", ["Gasto Avulso", "Gasto Fixo", "Entrada"])
            
            if st.form_submit_button("Salvar Lançamento", type="primary"):
                if nome and valor > 0:
                    if tipo_mov == "Entrada":
                        insert_entrada(user_id, {"id": uid(), "nome": nome, "valor": valor, "mes": mes, "ano": YEAR, "fixo": 0})
                    else:
                        insert_gasto(user_id, {"id": uid(), "nome": nome, "valor": valor, "mes": mes, "categoria": "Outros", "tipo": "Débito", "fixo": 1 if "Fixo" in tipo_mov else 0})
                    st.success("Registrado!")
                    st.rerun()

        section_header("Últimos Registros do Mês")
        if gastos or fixos or entradas:
            html = "<div class='fin-card' style='padding:0.5rem 1.5rem'>"
            for m in sorted(gastos + fixos + entradas, key=lambda x: x.get('created_at', ''), reverse=True)[:6]:
                is_entrada = 'categoria' not in m
                cor = "#22c55e" if is_entrada else "#ef4444"
                sinal = "+" if is_entrada else "-"
                html += f"""
                <div class="fin-row">
                    <span style="font-size:1.2rem">{'💰' if is_entrada else CAT_ICONS.get(m.get('categoria'), '📦')}</span>
                    <div style="flex:1">
                        <div style="font-weight:600">{m['nome']}</div>
                        <div style="font-size:12px;opacity:0.6">{'Entrada' if is_entrada else m.get('categoria','Gasto')}</div>
                    </div>
                    <span style="color:{cor};font-weight:600">{sinal} {fmt(m['valor'])}</span>
                </div>"""
            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)
        else:
            st.info("Nenhuma movimentação avulsa neste mês.")

    with c2:
        section_header("Saúde Financeira")
        score = 100
        if tot_entradas > 0:
            ratio = tot_despesas / tot_entradas
            if ratio > 0.9: score -= 40
            elif ratio > 0.7: score -= 20
            elif ratio > 0.5: score -= 10
        else: score = 50
        
        cor_score = "#22c55e" if score >= 70 else "#eab308" if score >= 40 else "#ef4444"
        st.markdown(f"""
        <div class="fin-card" style="text-align:center; padding:3rem 1rem;">
            <div style="font-size:4rem;font-weight:800;color:{cor_score};line-height:1">{score}</div>
            <div style="font-size:14px;font-weight:600;margin-top:10px;text-transform:uppercase;letter-spacing:1px;opacity:0.7">Pontuação do Mês</div>
        </div>
        """, unsafe_allow_html=True)


# --- View: Lançamentos Detalhados ---
def render_mes():
    user_id = st.session_state.user["id"]
    mes = st.session_state.mes_atual
    
    st.markdown(f"<h2>Lançamentos de {MONTHS[mes]}</h2>", unsafe_allow_html=True)
    
    t1, t2 = st.tabs(["🔴 Despesas", "🟢 Entradas"])
    with t1:
        gastos = get_gastos(user_id, mes)
        if gastos:
            for g in gastos:
                c1, c2, c3 = st.columns([3, 1, 1])
                c1.markdown(f"**{g['nome']}** <span class='badge badge-red'>{g.get('categoria','')}</span>", unsafe_allow_html=True)
                c2.write(fmt(g['valor']))
                if c3.button("Excluir", key=f"del_g_{g['id']}"):
                    delete_gasto(g['id'], user_id)
                    st.rerun()
        else: st.write("Nenhum gasto avulso.")
        
    with t2:
        entradas = get_entradas(user_id, mes)
        if entradas:
            for e in entradas:
                c1, c2, c3 = st.columns([3, 1, 1])
                c1.markdown(f"**{e['nome']}** <span class='badge badge-green'>Receita</span>", unsafe_allow_html=True)
                c2.write(fmt(e['valor']))
                if c3.button("Excluir", key=f"del_e_{e['id']}"):
                    delete_entrada(e['id'], user_id)
                    st.rerun()
        else: st.write("Nenhuma entrada.")


# --- View: Metas & Investimentos ---
def render_metas():
    user_id = st.session_state.user["id"]
    st.markdown("<h2>🎯 Metas e Investimentos</h2>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        with st.form("nova_meta"):
            st.write("**Criar Nova Meta**")
            nome = st.text_input("Nome da Meta")
            valor = st.number_input("Valor Alvo (R$)", min_value=1.0)
            if st.form_submit_button("Salvar Meta"):
                insert_meta(user_id, {"nome": nome, "total": valor})
                st.rerun()
                
    with c2:
        metas = get_metas(user_id)
        if metas:
            for m in metas:
                pct = (m['guardado'] / m['total']) * 100 if m['total'] > 0 else 0
                st.markdown(f"""
                <div class="fin-card" style="padding:1rem">
                    <div style="display:flex;justify-content:space-between;font-weight:600">
                        <span>{m['nome']}</span>
                        <span>{fmt(m['guardado'])} / {fmt(m['total'])}</span>
                    </div>
                    {progress_bar_html(pct)}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Você ainda não tem metas.")


# --- View: Parcelas ---
def render_parcelas():
    user_id = st.session_state.user["id"]
    st.markdown("<h2>💳 Compras Parceladas</h2>", unsafe_allow_html=True)
    
    parcelas = get_parcelas_ativas(user_id)
    if parcelas:
        for p in parcelas:
            val_parc = float(p['valor'])/int(p['parcelas'])
            st.markdown(f"""
            <div class="fin-card" style="padding:1rem; display:flex; justify-content:space-between">
                <div>
                    <div style="font-weight:600; font-size:1.1rem">{p['nome']}</div>
                    <div style="font-size:13px; opacity:0.6">Início: {MONTHS[int(p['mes'])]} | {p['parcelas']}x de {fmt(val_parc)}</div>
                </div>
                <div style="text-align:right; font-weight:700; color:#ef4444; font-size:1.2rem">
                    Total: {fmt(p['valor'])}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("Você não possui compras parceladas no momento!")


# --- View: Anual ---
def render_anual():
    st.markdown("<h2>🗓️ Panorama Anual (Em construção)</h2>", unsafe_allow_html=True)
    st.info("Aqui você verá o gráfico consolidado de todos os meses.")


# ==============================================================================
# 4. ROTEAMENTO PRINCIPAL
# ==============================================================================
if st.session_state.user is None:
    login_page()
else:
    render_sidebar()
    page = st.session_state.page
    
    if page == "dashboard": render_dashboard()
    elif page == "mes": render_mes()
    elif page == "parcelas": render_parcelas()
    elif page == "metas": render_metas()
    elif page == "anual": render_anual()
