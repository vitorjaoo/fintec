"""Shared constants, CSS injection, and utility functions."""
import streamlit as st
from datetime import datetime
import uuid

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


def month_diff(a: datetime, b: datetime) -> int:
    return max(0, (b.year - a.year) * 12 + b.month - a.month)


def inject_css():
    st.markdown("""
    <style>
    /* ── RESET & BASE ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    :root {
        --bg: #0a0a0a;
        --bg2: #111111;
        --bg3: #1a1a1a;
        --bg4: #222222;
        --border: rgba(255,255,255,0.08);
        --border2: rgba(255,255,255,0.14);
        --text: #f5f5f5;
        --text2: rgba(245,245,245,0.6);
        --text3: rgba(245,245,245,0.35);
        --green: #30d158;
        --red: #ff453a;
        --blue: #0a84ff;
        --yellow: #ffd60a;
        --purple: #bf5af2;
        --orange: #ff9f0a;
        --teal: #5ac8fa;
    }

    html, body, [data-testid="stApp"], [class*="main"] {
        background: var(--bg) !important;
        color: var(--text) !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: var(--bg2) !important;
        border-right: 1px solid var(--border) !important;
    }
    [data-testid="stSidebar"] * { color: var(--text) !important; }
    [data-testid="stSidebarContent"] { padding: 1rem 0.75rem !important; }

    /* Headers */
    h1 { font-size: 2rem !important; font-weight: 700 !important; letter-spacing: -0.5px !important; }
    h2 { font-size: 1.4rem !important; font-weight: 700 !important; }
    h3 { font-size: 1.1rem !important; font-weight: 600 !important; }

    /* Metric cards */
    [data-testid="stMetric"] {
        background: var(--bg3) !important;
        border: 1px solid var(--border) !important;
        border-radius: 14px !important;
        padding: 1rem 1.25rem !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 11px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.6px !important;
        color: var(--text3) !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.6rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.5px !important;
    }
    [data-testid="stMetricDelta"] { font-size: 12px !important; }

    /* Buttons */
    .stButton > button {
        background: var(--bg4) !important;
        color: var(--text) !important;
        border: 1px solid var(--border2) !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        transition: all 0.15s !important;
    }
    .stButton > button:hover {
        background: #333 !important;
        border-color: rgba(255,255,255,0.25) !important;
    }
    .stButton > button[kind="primary"] {
        background: var(--green) !important;
        color: #000 !important;
        border-color: var(--green) !important;
    }

    /* Inputs */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div,
    .stDateInput > div > div > input,
    .stTextArea textarea {
        background: var(--bg3) !important;
        border: 1px solid var(--border2) !important;
        border-radius: 10px !important;
        color: var(--text) !important;
        font-family: 'Inter', sans-serif !important;
    }
    .stSelectbox > div > div { border-radius: 10px !important; }
    [data-baseweb="select"] > div { background: var(--bg3) !important; border-color: var(--border2) !important; }
    [data-baseweb="menu"] { background: var(--bg3) !important; }
    [data-baseweb="option"] { background: var(--bg3) !important; color: var(--text) !important; }
    [data-baseweb="option"]:hover { background: var(--bg4) !important; }

    /* Dataframe */
    [data-testid="stDataFrame"], .dataframe {
        background: var(--bg3) !important;
        border: 1px solid var(--border) !important;
        border-radius: 14px !important;
    }

    /* Divider */
    hr { border-color: var(--border) !important; }

    /* Expander */
    [data-testid="stExpander"] {
        background: var(--bg3) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
    }
    [data-testid="stExpander"] summary { color: var(--text) !important; }

    /* Tabs */
    [data-testid="stTabs"] [role="tab"] {
        background: transparent !important;
        color: var(--text2) !important;
        border-bottom: 2px solid transparent !important;
        font-weight: 500 !important;
    }
    [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
        color: var(--text) !important;
        border-bottom-color: var(--green) !important;
    }

    /* Forms */
    [data-testid="stForm"] {
        background: var(--bg3) !important;
        border: 1px solid var(--border) !important;
        border-radius: 16px !important;
        padding: 1.5rem !important;
    }

    /* Labels */
    label, .stTextInput label, .stSelectbox label, .stNumberInput label { 
        color: var(--text2) !important; 
        font-size: 13px !important;
        font-weight: 500 !important;
    }

    /* Progress */
    .stProgress > div > div { background: var(--green) !important; }
    .stProgress > div { background: var(--bg4) !important; border-radius: 4px !important; }

    /* Info/success/error boxes */
    [data-testid="stNotification"] { border-radius: 12px !important; }
    .stSuccess { background: rgba(48,209,88,0.1) !important; border: 1px solid rgba(48,209,88,0.2) !important; border-radius: 10px !important; }
    .stError { background: rgba(255,69,58,0.1) !important; border: 1px solid rgba(255,69,58,0.2) !important; border-radius: 10px !important; }
    .stWarning { background: rgba(255,214,10,0.1) !important; border: 1px solid rgba(255,214,10,0.2) !important; border-radius: 10px !important; }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 4px; height: 4px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 2px; }

    /* Toggle/Radio */
    .stRadio > div { gap: 0.5rem !important; }
    .stRadio [data-testid="stMarkdownContainer"] { display: none; }

    /* Remove streamlit branding */
    #MainMenu, footer, header { visibility: hidden !important; }
    [data-testid="stToolbar"] { display: none !important; }

    /* Custom card */
    .fin-card {
        background: var(--bg3);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 1.25rem;
        margin-bottom: 1rem;
    }
    .fin-card-title {
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        color: var(--text3);
        margin-bottom: 0.75rem;
        font-weight: 600;
    }

    /* Tag badges */
    .tag {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 2px 8px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 600;
    }
    .tag-green { background: rgba(48,209,88,0.15); color: #30d158; }
    .tag-red { background: rgba(255,69,58,0.15); color: #ff453a; }
    .tag-blue { background: rgba(10,132,255,0.15); color: #0a84ff; }
    .tag-orange { background: rgba(255,159,10,0.15); color: #ff9f0a; }
    .tag-purple { background: rgba(191,90,242,0.15); color: #bf5af2; }
    .tag-yellow { background: rgba(255,214,10,0.12); color: #ffd60a; }

    /* Row item */
    .fin-row {
        display: flex;
        align-items: center;
        padding: 10px 0;
        border-bottom: 1px solid var(--border);
        font-size: 14px;
        gap: 10px;
    }
    .fin-row:last-child { border-bottom: none; }

    /* Score ring placeholder */
    .score-display {
        text-align: center;
        padding: 0.5rem 0;
    }
    .score-number {
        font-size: 2.5rem;
        font-weight: 700;
        line-height: 1;
    }

    /* Parcela progress */
    .parc-progress {
        display: flex;
        gap: 3px;
        margin-top: 6px;
        flex-wrap: wrap;
    }
    .parc-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
    }

    /* Login card */
    .login-container {
        max-width: 420px;
        margin: 4rem auto;
        background: var(--bg3);
        border: 1px solid var(--border2);
        border-radius: 20px;
        padding: 2.5rem;
    }

    /* Full width columns */
    [data-testid="column"] { gap: 0.5rem !important; }

    /* Number input arrows color */
    .stNumberInput button { color: var(--text2) !important; }

    </style>
    """, unsafe_allow_html=True)


def card_html(title: str, value: str, sub: str = "", color: str = "var(--text)") -> str:
    return f"""
    <div class="fin-card" style="margin-bottom:0">
        <div class="fin-card-title">{title}</div>
        <div style="font-size:1.8rem;font-weight:700;color:{color};letter-spacing:-0.5px;line-height:1">{value}</div>
        {f'<div style="font-size:12px;color:var(--text2);margin-top:6px">{sub}</div>' if sub else ''}
    </div>
    """


def progress_bar_html(pct: float, color: str = "var(--green)", height: int = 6) -> str:
    pct = min(100, max(0, pct))
    return f"""
    <div style="height:{height}px;background:var(--bg4);border-radius:{height//2}px;overflow:hidden;margin-top:8px">
        <div style="height:100%;width:{pct:.1f}%;background:{color};border-radius:{height//2}px;transition:width 0.5s ease"></div>
    </div>
    """


def section_header(title: str, subtitle: str = ""):
    st.markdown(f"""
    <div style="margin-bottom:1rem">
        <div style="font-size:1.1rem;font-weight:700">{title}</div>
        {f'<div style="font-size:13px;color:var(--text2);margin-top:2px">{subtitle}</div>' if subtitle else ''}
    </div>
    """, unsafe_allow_html=True)
