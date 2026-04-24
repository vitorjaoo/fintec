"""
Finanças 2026 — Streamlit App
Entry point: streamlit run app.py
"""
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from utils import inject_css, YEAR, MONTHS
import db

st.set_page_config(
    page_title=f"Finanças {YEAR}",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

# ─── INIT SCHEMA ───────────────────────────────────────────────────────────────

@st.cache_resource
def init_db():
    try:
        db.init_schema()
        return True
    except Exception as e:
        return str(e)


schema_ok = init_db()


# ─── SESSION STATE ─────────────────────────────────────────────────────────────

if "user" not in st.session_state:
    st.session_state.user = None
if "auth_tab" not in st.session_state:
    st.session_state.auth_tab = "login"
if "mes_atual" not in st.session_state:
    st.session_state.mes_atual = 3  # April (0-indexed)


# ─── LOGIN / REGISTER ─────────────────────────────────────────────────────────

def login_page():
    st.markdown("""
    <div style="text-align:center;padding:3rem 0 2rem">
        <div style="font-size:3rem;margin-bottom:0.5rem">💰</div>
        <div style="font-size:2rem;font-weight:700;letter-spacing:-0.5px">Finanças <span style="color:var(--green)">2026</span></div>
        <div style="font-size:14px;color:var(--text2);margin-top:6px">Controle financeiro completo</div>
    </div>
    """, unsafe_allow_html=True)

    if schema_ok is not True:
        st.error(f"❌ Erro ao conectar ao banco: {schema_ok}")
        st.info("Configure as variáveis TURSO_DATABASE_URL e TURSO_AUTH_TOKEN no arquivo .env")
        with st.expander("📋 Como configurar"):
            st.code("""# .env
TURSO_DATABASE_URL=libsql://seu-banco.turso.io
TURSO_AUTH_TOKEN=seu_token_aqui""")
        return

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        tab1, tab2 = st.tabs(["🔐 Entrar", "📝 Criar Conta"])

        with tab1:
            with st.form("form_login"):
                username = st.text_input("Usuário", placeholder="seu_usuario")
                password = st.text_input("Senha", type="password", placeholder="••••••••")
                submitted = st.form_submit_button("Entrar →", use_container_width=True, type="primary")
                if submitted:
                    if not username or not password:
                        st.error("Preencha usuário e senha")
                    else:
                        with st.spinner("Verificando..."):
                            user = db.verify_user(username, password)
                        if user:
                            st.session_state.user = user
                            st.success(f"Bem-vindo, {user['username']}! 👋")
                            st.rerun()
                        else:
                            st.error("Usuário ou senha incorretos")

        with tab2:
            with st.form("form_register"):
                new_user = st.text_input("Usuário", placeholder="seu_usuario", key="reg_user")
                new_pass = st.text_input("Senha", type="password", placeholder="mínimo 6 caracteres", key="reg_pass")
                new_pass2 = st.text_input("Confirmar senha", type="password", placeholder="••••••••", key="reg_pass2")
                submitted2 = st.form_submit_button("Criar Conta →", use_container_width=True, type="primary")
                if submitted2:
                    if not new_user or not new_pass:
                        st.error("Preencha todos os campos")
                    elif len(new_pass) < 6:
                        st.error("Senha deve ter no mínimo 6 caracteres")
                    elif new_pass != new_pass2:
                        st.error("As senhas não coincidem")
                    elif db.user_exists(new_user):
                        st.error("Este usuário já existe")
                    else:
                        with st.spinner("Criando conta..."):
                            ok = db.create_user(new_user, new_pass)
                        if ok:
                            st.success("Conta criada! Faça o login.")
                        else:
                            st.error("Erro ao criar conta. Tente novamente.")


# ─── SIDEBAR (AUTENTICADO) ─────────────────────────────────────────────────────

def render_sidebar():
    user = st.session_state.user
    mes = st.session_state.mes_atual

    with st.sidebar:
        st.markdown(f"""
        <div style="padding:0.5rem 0 1rem">
            <div style="font-size:1.3rem;font-weight:700">Finanças <span style="color:var(--green)">2026</span></div>
            <div style="font-size:12px;color:var(--text3);margin-top:2px">👤 {user['username']}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("**📍 Navegação**")

        pages = {
            "🏠 Dashboard": "dashboard",
            "📅 Mês Atual": "mes",
            "💳 Parcelas": "parcelas",
            "🎯 Metas": "metas",
            "📈 Investimentos": "investimentos",
            "🗓️ Panorama Anual": "anual",
        }

        if "page" not in st.session_state:
            st.session_state.page = "dashboard"

        for label, key in pages.items():
            if st.button(label, key=f"nav_{key}", use_container_width=True):
                st.session_state.page = key
                st.rerun()

        st.markdown("---")
        st.markdown("**📆 Ir para mês**")

        month_cols = st.columns(3)
        for i, m in enumerate(MONTHS):
            with month_cols[i % 3]:
                active = "🟢" if i == mes else ""
                if st.button(f"{active}{m[:3]}", key=f"m_{i}", use_container_width=True):
                    st.session_state.mes_atual = i
                    st.session_state.page = "mes"
                    st.rerun()

        st.markdown("---")

        # Health score
        uid = user["id"]
        try:
            gastos_m = db.get_gastos(uid, mes) + db.get_fixos(uid, mes)
            entradas_m = db.get_entradas(uid, mes)
            total_g = sum(float(g["valor"]) for g in gastos_m)
            total_e = sum(float(e["valor"]) for e in entradas_m)
            parcelas = db.get_parcelas_ativas(uid)
            total_parc = sum(float(p["valor"]) / int(p["parcelas"]) for p in parcelas)
            total_g += total_parc

            score = 100
            if total_e > 0:
                ratio = total_g / total_e
                if ratio > 0.9: score -= 40
                elif ratio > 0.7: score -= 20
                elif ratio > 0.5: score -= 10
            metas = db.get_metas(uid)
            if not metas: score -= 10
            investimentos = db.get_investimentos(uid)
            total_inv = sum(float(i.get("reserva", 0)) + float(i.get("fixa", 0)) + float(i.get("variavel", 0)) for i in investimentos)
            if total_inv == 0: score -= 15
            score = max(0, min(100, score))

            cor = "#30d158" if score >= 70 else "#ffd60a" if score >= 40 else "#ff453a"
            label = "Excelente! 🎯" if score >= 70 else "Pode melhorar ⚠️" if score >= 40 else "Atenção! 🚨"

            st.markdown(f"""
            <div style="text-align:center;padding:0.75rem;background:var(--bg3);border:1px solid var(--border);border-radius:12px">
                <div style="font-size:11px;color:var(--text3);text-transform:uppercase;letter-spacing:0.6px;margin-bottom:6px">Saúde Financeira</div>
                <div style="font-size:2rem;font-weight:700;color:{cor}">{score}</div>
                <div style="font-size:12px;color:var(--text2)">{label}</div>
            </div>
            """, unsafe_allow_html=True)
        except Exception:
            pass

        st.markdown("---")
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.user = None
            st.rerun()


# ─── MAIN APP ─────────────────────────────────────────────────────────────────

if st.session_state.user is None:
    login_page()
else:
    render_sidebar()

    page = st.session_state.get("page", "dashboard")

    # AQUI ESTÃO AS CORREÇÕES: Imports diretos sem o "from pages"
    if page == "dashboard":
        import dashboard
        dashboard.render()
    elif page == "mes":
        import mes
        mes.render()
    elif page == "parcelas":
        import parcelas
        parcelas.render()
    elif page == "metas":
        import metas
        metas.render()
    elif page == "investimentos":
        import investimentos
        investimentos.render()
    elif page == "anual":
        import anual
        anual.render()
