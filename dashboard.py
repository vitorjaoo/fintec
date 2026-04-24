"""Dashboard — visão geral do mês."""
import streamlit as st
from datetime import datetime
import db
from utils import fmt, MONTHS, CAT_ICONS, uid, CATEGORIAS, TIPOS, YEAR, card_html, progress_bar_html, section_header


def render():
    user = st.session_state.user
    mes = st.session_state.mes_atual
    user_id = user["id"]

    st.markdown(f"""
    <div style="padding:1.5rem 0 0.5rem">
        <div style="font-size:2rem;font-weight:700;letter-spacing:-0.5px">Olá, {user['username']} 👋</div>
        <div style="font-size:14px;color:var(--text2);margin-top:4px">{MONTHS[mes]} {YEAR} — visão geral das suas finanças</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Ações rápidas ──
    ca, cb, cc = st.columns([1, 1, 4])
    with ca:
        if st.button("➕ Novo Gasto", use_container_width=True, type="primary"):
            st.session_state.show_modal_gasto = True
    with cb:
        if st.button("💰 Nova Entrada", use_container_width=True):
            st.session_state.show_modal_entrada = True

    # ── Carrega dados ──
    gastos = db.get_gastos(user_id, mes)
    fixos = db.get_fixos(user_id, mes)
    entradas = db.get_entradas(user_id, mes)
    parcelas_ativas = db.get_parcelas_ativas(user_id)

    total_gastos = sum(float(g["valor"]) for g in gastos)
    total_fixos = sum(float(g["valor"]) for g in fixos)
    total_parc_mes = sum(
        float(p["valor"]) / int(p["parcelas"])
        for p in parcelas_ativas
        if int(p["mes"]) <= mes < int(p["mes"]) + int(p["parcelas"])
    )
    total_entradas = sum(float(e["valor"]) for e in entradas)
    total_despesas = total_gastos + total_fixos + total_parc_mes
    saldo = total_entradas - total_despesas

    # ── KPIs ──
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("💚 Entradas", fmt(total_entradas), f"{len(entradas)} lançamento(s)")
    with k2:
        st.metric("🔴 Despesas", fmt(total_despesas), f"{len(gastos)+len(fixos)} lançamento(s)")
    with k3:
        delta_label = "Positivo ✓" if saldo >= 0 else "Negativo ✗"
        st.metric("⚖️ Saldo", fmt(saldo), delta_label, delta_color="normal" if saldo >= 0 else "inverse")
    with k4:
        st.metric("💳 Parcelado/mês", fmt(total_parc_mes), f"{len(parcelas_ativas)} compra(s) ativa(s)")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Linha 2: categorias + cards direita ──
    col_left, col_right = st.columns([3, 2], gap="medium")

    with col_left:
        section_header("Gastos por Categoria")
        todos_gastos = gastos + fixos + [
            {**p, "valor": float(p["valor"]) / int(p["parcelas"]), "categoria": "Fatura Cartão"}
            for p in parcelas_ativas
            if int(p["mes"]) <= mes < int(p["mes"]) + int(p["parcelas"])
        ]
        cat_totals: dict[str, float] = {}
        for g in todos_gastos:
            cat = g.get("categoria") or "Outros"
            cat_totals[cat] = cat_totals.get(cat, 0) + float(g["valor"])

        if cat_totals:
            sorted_cats = sorted(cat_totals.items(), key=lambda x: -x[1])
            total_ref = max(sum(cat_totals.values()), 0.01)
            html = "<div class='fin-card'>"
            for cat, val in sorted_cats[:8]:
                pct = val / total_ref * 100
                icon = CAT_ICONS.get(cat, "📦")
                html += f"""
                <div style="margin-bottom:12px">
                    <div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:4px">
                        <span>{icon} {cat}</span>
                        <div style="display:flex;gap:12px;align-items:center">
                            <span style="color:var(--text3);font-size:11px">{pct:.1f}%</span>
                            <span style="font-weight:600">{fmt(val)}</span>
                        </div>
                    </div>
                    {progress_bar_html(pct)}
                </div>"""
            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)
        else:
            st.markdown("""<div class='fin-card' style='text-align:center;color:var(--text3);padding:2rem'>
                📊 Nenhum gasto registrado este mês
            </div>""", unsafe_allow_html=True)

    with col_right:
        # Próximas parcelas
        section_header("Próximas Faturas")
        prox_mes = (mes + 1) % 12
        prox_parc = [
            p for p in parcelas_ativas
            if int(p["mes"]) <= prox_mes < int(p["mes"]) + int(p["parcelas"])
        ]
        if prox_parc:
            html = "<div class='fin-card'>"
            for p in prox_parc[:5]:
                parc_atual = prox_mes - int(p["mes"]) + 1
                val_parc = float(p["valor"]) / int(p["parcelas"])
                html += f"""
                <div class="fin-row">
                    <span style="font-size:1.3rem">💳</span>
                    <div style="flex:1">
                        <div style="font-size:13px;font-weight:600">{p['nome']}</div>
                        <div style="font-size:11px;color:var(--text2)">{MONTHS[prox_mes]} — {parc_atual}/{p['parcelas']}</div>
                    </div>
                    <span style="color:var(--orange);font-weight:700;font-size:14px">{fmt(val_parc)}</span>
                </div>"""
            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)
        else:
            st.markdown("<div class='fin-card' style='color:var(--text3);font-size:13px;text-align:center;padding:1.5rem'>🎉 Sem parcelas no próximo mês!</div>", unsafe_allow_html=True)

        # Fixos
        section_header("Gastos Fixos")
        if fixos:
            html = "<div class='fin-card'>"
            for f in fixos[:5]:
                icon = CAT_ICONS.get(f.get("categoria", ""), "📌")
                html += f"""
                <div class="fin-row">
                    <span style="font-size:1.2rem">{icon}</span>
                    <div style="flex:1">
                        <div style="font-size:13px;font-weight:600">{f['nome']}</div>
                        <div style="font-size:11px;color:var(--text2)">{f.get('categoria','')}</div>
                    </div>
                    <span style="color:var(--orange);font-weight:600;font-size:14px">{fmt(f['valor'])}</span>
                </div>"""
            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)
        else:
            st.markdown("<div class='fin-card' style='color:var(--text3);font-size:13px;text-align:center;padding:1.5rem'>📌 Nenhum fixo cadastrado</div>", unsafe_allow_html=True)

    # ── Últimos gastos ──
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    section_header("Últimos Lançamentos")
    if gastos:
        cols_header = st.columns([3, 2, 2, 1, 1])
        for col, h in zip(cols_header, ["Nome", "Categoria", "Tipo", "Valor", ""]):
            col.markdown(f"<span style='font-size:11px;color:var(--text3);text-transform:uppercase;letter-spacing:0.5px'>{h}</span>", unsafe_allow_html=True)
        st.markdown("<hr style='margin:4px 0 8px'>", unsafe_allow_html=True)

        for g in reversed(gastos[-10:]):
            c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 1, 1])
            icon = CAT_ICONS.get(g.get("categoria", ""), "📦")
            c1.markdown(f"**{g['nome']}**")
            c2.markdown(f"{icon} {g.get('categoria','—')}")
            c3.markdown(f"<span style='color:var(--text2)'>{g.get('tipo','—')}</span>", unsafe_allow_html=True)
            c4.markdown(f"<span style='color:var(--red);font-weight:600'>{fmt(g['valor'])}</span>", unsafe_allow_html=True)
            with c5:
                if st.button("✕", key=f"del_dash_{g['id']}", help="Remover"):
                    db.delete_gasto(g["id"], user_id)
                    st.rerun()
    else:
        st.markdown("<div style='color:var(--text3);text-align:center;padding:2rem'>Nenhum gasto avulso registrado este mês</div>", unsafe_allow_html=True)

    # ── Modal Gasto ──
    if st.session_state.get("show_modal_gasto"):
        with st.expander("➕ Novo Gasto", expanded=True):
            _form_gasto(user_id, mes)

    # ── Modal Entrada ──
    if st.session_state.get("show_modal_entrada"):
        with st.expander("💰 Nova Entrada", expanded=True):
            _form_entrada(user_id, mes)


def _form_gasto(user_id, mes):
    with st.form("form_gasto_dashboard"):
        nome = st.text_input("Nome / Descrição", placeholder="Ex: Supermercado")
        c1, c2 = st.columns(2)
        with c1:
            valor = st.number_input("Valor (R$)", min_value=0.01, step=0.01)
            categoria = st.selectbox("Categoria", CATEGORIAS)
        with c2:
            data = st.date_input("Data")
            tipo = st.selectbox("Tipo de Pagamento", TIPOS)
        c3, c4 = st.columns(2)
        with c3:
            parcelas = st.number_input("Parcelas (1 = à vista)", min_value=1, max_value=48, value=1)
        with c4:
            fixo = st.selectbox("Recorrente todo mês?", ["Não", "Sim"]) == "Sim"

        col_a, col_b = st.columns(2)
        with col_a:
            if st.form_submit_button("💾 Salvar", type="primary", use_container_width=True):
                if nome and valor:
                    db.insert_gasto(user_id, {
                        "id": uid(), "nome": nome, "valor": valor,
                        "data": str(data), "categoria": categoria, "tipo": tipo,
                        "mes": mes, "ano": YEAR, "parcelas": int(parcelas), "fixo": fixo
                    })
                    st.session_state.show_modal_gasto = False
                    st.success("Gasto salvo!")
                    st.rerun()
                else:
                    st.error("Preencha nome e valor")
        with col_b:
            if st.form_submit_button("Cancelar", use_container_width=True):
                st.session_state.show_modal_gasto = False
                st.rerun()


def _form_entrada(user_id, mes):
    with st.form("form_entrada_dashboard"):
        nome = st.text_input("Descrição", placeholder="Ex: Salário, Freela...")
        c1, c2 = st.columns(2)
        with c1:
            valor = st.number_input("Valor (R$)", min_value=0.01, step=0.01)
        with c2:
            data = st.date_input("Data")
        fixo = st.selectbox("Recorrente todo mês?", ["Não", "Sim"]) == "Sim"

        col_a, col_b = st.columns(2)
        with col_a:
            if st.form_submit_button("💾 Salvar", type="primary", use_container_width=True):
                if nome and valor:
                    db.insert_entrada(user_id, {
                        "id": uid(), "nome": nome, "valor": valor,
                        "data": str(data), "mes": mes, "ano": YEAR, "fixo": fixo
                    })
                    st.session_state.show_modal_entrada = False
                    st.success("Entrada salva!")
                    st.rerun()
                else:
                    st.error("Preencha nome e valor")
        with col_b:
            if st.form_submit_button("Cancelar", use_container_width=True):
                st.session_state.show_modal_entrada = False
                st.rerun()
