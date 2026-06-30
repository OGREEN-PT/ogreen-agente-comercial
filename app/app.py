"""
OGREEN — Agente Comercial de IA
App Streamlit: Upload de leads + Dashboard de resultados
"""

import streamlit as st
import pandas as pd
import requests
import uuid
import io
from datetime import datetime, timedelta
from supabase import create_client

# --- Configuração ---
st.set_page_config(
    page_title="OGREEN Agente Comercial",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Supabase
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
WEBHOOKS = {
    "sms": st.secrets["make"]["webhook_sms"],
    "email": st.secrets["make"]["webhook_email"],
    "telefone": st.secrets["make"]["webhook_telefone"],
    "whatsapp": st.secrets["make"]["webhook_whatsapp"],
}

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Cores OGREEN ---
OGREEN_PRIMARY = "#2E7D32"
OGREEN_DARK = "#1B5E20"
OGREEN_LIGHT = "#4CAF50"
OGREEN_ACCENT = "#81C784"
OGREEN_BG = "#F1F8E9"
OGREEN_WHITE = "#FFFFFF"
OGREEN_GREY = "#424242"
OGREEN_LOGO = "https://ogreen.pt/wp-content/themes/ogreen/assets/logo.svg"

# --- Estilos ---
st.markdown(f"""
<style>
    /* --- Global --- */
    .stApp {{
        background-color: #FAFDF7;
    }}

    /* --- Sidebar --- */
    section[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {OGREEN_DARK} 0%, {OGREEN_PRIMARY} 100%);
    }}
    section[data-testid="stSidebar"] * {{
        color: {OGREEN_WHITE} !important;
    }}
    section[data-testid="stSidebar"] .stRadio label {{
        color: {OGREEN_WHITE} !important;
        font-weight: 500;
    }}
    section[data-testid="stSidebar"] .stRadio label:hover {{
        background-color: rgba(255, 255, 255, 0.12);
        border-radius: 6px;
    }}
    section[data-testid="stSidebar"] hr {{
        border-color: rgba(255, 255, 255, 0.2) !important;
    }}

    /* --- Headers --- */
    .main-header {{
        font-size: 2rem;
        font-weight: 700;
        color: {OGREEN_DARK};
        margin-bottom: 0.5rem;
    }}
    .sub-header {{
        font-size: 1rem;
        color: #757575;
        margin-top: -0.5rem;
        margin-bottom: 1.5rem;
    }}

    /* --- Metric cards --- */
    [data-testid="stMetric"] {{
        background: {OGREEN_WHITE};
        border-radius: 10px;
        padding: 16px 20px;
        border-left: 4px solid {OGREEN_PRIMARY};
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
    }}
    [data-testid="stMetricLabel"] {{
        color: #757575 !important;
        font-size: 0.85rem !important;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }}
    [data-testid="stMetricValue"] {{
        color: {OGREEN_DARK} !important;
        font-weight: 700 !important;
    }}

    /* --- Buttons --- */
    .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, {OGREEN_PRIMARY} 0%, {OGREEN_DARK} 100%);
        border: none;
        border-radius: 8px;
        font-weight: 600;
        letter-spacing: 0.02em;
        padding: 0.6rem 1.5rem;
        transition: all 0.2s ease;
    }}
    .stButton > button[kind="primary"]:hover {{
        box-shadow: 0 4px 12px rgba(46, 125, 50, 0.35);
        transform: translateY(-1px);
    }}

    /* --- Download buttons --- */
    .stDownloadButton > button {{
        background: {OGREEN_WHITE} !important;
        color: {OGREEN_PRIMARY} !important;
        border: 2px solid {OGREEN_PRIMARY} !important;
        border-radius: 8px;
        font-weight: 600;
    }}
    .stDownloadButton > button:hover {{
        background: {OGREEN_BG} !important;
    }}

    /* --- Dataframe --- */
    .stDataFrame {{
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
    }}

    /* --- Expander --- */
    .streamlit-expanderHeader {{
        background: {OGREEN_BG};
        border-radius: 8px;
        font-weight: 600;
        color: {OGREEN_DARK};
    }}

    /* --- File uploader --- */
    [data-testid="stFileUploader"] {{
        border: 2px dashed {OGREEN_ACCENT};
        border-radius: 10px;
        padding: 1rem;
        background: {OGREEN_WHITE};
    }}

    /* --- Tabs --- */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
    }}
    .stTabs [data-baseweb="tab"] {{
        padding: 8px 16px;
        border-radius: 8px 8px 0 0;
    }}

    /* --- Selectbox --- */
    .stSelectbox [data-baseweb="select"] {{
        border-radius: 8px;
    }}

    /* --- Divider --- */
    hr {{
        border-color: {OGREEN_BG} !important;
    }}

    /* --- Logo sidebar --- */
    .sidebar-logo {{
        text-align: center;
        padding: 1.5rem 1rem 0.5rem;
    }}
    .sidebar-logo img {{
        width: 160px;
        filter: brightness(0) invert(1);
    }}
    .sidebar-title {{
        text-align: center;
        font-size: 0.8rem;
        opacity: 0.8;
        margin-top: 0.3rem;
        letter-spacing: 0.08em;
    }}
    .sidebar-agent {{
        text-align: center;
        background: rgba(255, 255, 255, 0.15);
        border-radius: 20px;
        padding: 6px 12px;
        font-size: 0.75rem;
        margin: 0.8rem auto 0.5rem;
        display: inline-block;
        width: auto;
    }}
    .sidebar-agent-wrapper {{
        text-align: center;
    }}
</style>
""", unsafe_allow_html=True)


# --- Sidebar ---
with st.sidebar:
    st.markdown(f"""
        <div class="sidebar-logo">
            <img src="{OGREEN_LOGO}" alt="OGREEN">
        </div>
        <div class="sidebar-title">ADVANCED WASTE TECHNOLOGIES</div>
        <div class="sidebar-agent-wrapper">
            <span class="sidebar-agent">🤖 Agente Comercial IA</span>
        </div>
    """, unsafe_allow_html=True)
    st.divider()
    pagina = st.radio(
        "Navegação",
        ["📤 Upload de Leads", "📊 Dashboard", "📋 Histórico de Contactos"],
        label_visibility="collapsed"
    )


# === PÁGINA: Upload de Leads ===
def pagina_upload():
    st.markdown('<p class="main-header">📤 Upload de Leads</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Carregue um ficheiro Excel com os leads a contactar pelo agente.</p>', unsafe_allow_html=True)

    # Template de exemplo
    with st.expander("📄 Ver formato esperado do Excel"):
        st.markdown("""
        O ficheiro Excel deve ter as seguintes colunas:

        | nome | empresa | telefone | email | notas | canal | origem |
        |------|---------|----------|-------|-------|-------|--------|
        | João Silva | Restaurante X | +351912345678 | joao@x.pt | Notas... | sms | website |

        - **canal**: `telefone`, `sms`, `email` ou `whatsapp` (obrigatório)
        - **telefone**: formato internacional (+351...) — obrigatório para SMS, telefone e WhatsApp
        - **email**: obrigatório para canal email
        """)

        # Botão para descarregar template
        template_df = pd.DataFrame({
            "nome": ["João Silva"],
            "empresa": ["Restaurante Exemplo"],
            "telefone": ["+351912345678"],
            "email": ["joao@exemplo.pt"],
            "notas": ["Lead de exemplo"],
            "canal": ["sms"],
            "origem": ["website"]
        })
        buffer_template = io.BytesIO()
        template_df.to_excel(buffer_template, index=False, engine="openpyxl")
        st.download_button(
            "⬇️ Descarregar template Excel",
            buffer_template.getvalue(),
            file_name="template_leads_ogreen.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    st.divider()

    # Upload
    ficheiro = st.file_uploader(
        "Escolher ficheiro Excel",
        type=["xlsx", "xls"],
        help="Ficheiro .xlsx com as colunas: nome, empresa, telefone, email, notas, canal, origem"
    )

    if ficheiro:
        try:
            df = pd.read_excel(ficheiro)
        except Exception as e:
            st.error(f"Erro ao ler o ficheiro: {e}")
            return

        # Validação de colunas
        colunas_obrigatorias = ["empresa", "canal"]
        colunas_em_falta = [c for c in colunas_obrigatorias if c not in df.columns]

        if colunas_em_falta:
            st.error(f"Colunas em falta: {', '.join(colunas_em_falta)}")
            return

        # Normalizar nomes de colunas
        df.columns = df.columns.str.strip().str.lower()

        # Validar canal
        canais_validos = ["telefone", "sms", "email", "whatsapp"]
        df["canal"] = df["canal"].str.strip().str.lower()
        canais_invalidos = df[~df["canal"].isin(canais_validos)]

        if not canais_invalidos.empty:
            st.warning(f"⚠️ {len(canais_invalidos)} leads com canal inválido (ignoradas).")
            df = df[df["canal"].isin(canais_validos)]

        # Validar contactos por canal
        erros = []
        for idx, row in df.iterrows():
            if row["canal"] in ["sms", "telefone", "whatsapp"] and pd.isna(row.get("telefone", None)):
                erros.append(f"Linha {idx+2}: canal '{row['canal']}' sem telefone")
            if row["canal"] == "email" and pd.isna(row.get("email", None)):
                erros.append(f"Linha {idx+2}: canal 'email' sem email")

        if erros:
            st.warning(f"⚠️ {len(erros)} leads com dados incompletos:")
            for e in erros[:5]:
                st.text(f"  • {e}")
            if len(erros) > 5:
                st.text(f"  ... e mais {len(erros)-5}")

        # Preview
        st.markdown(f"### Pré-visualização ({len(df)} leads)")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("SMS", len(df[df["canal"] == "sms"]))
        with col2:
            st.metric("Email", len(df[df["canal"] == "email"]))
        with col3:
            st.metric("WhatsApp", len(df[df["canal"] == "whatsapp"]))
        with col4:
            st.metric("Telefone", len(df[df["canal"] == "telefone"]))

        st.dataframe(df, use_container_width=True, hide_index=True)

        st.divider()

        # Confirmar e enviar
        if st.button("🚀 Enviar leads para o agente", type="primary", use_container_width=True):
            batch_id = str(uuid.uuid4())

            with st.spinner("A processar..."):
                # 1. Registar upload no Supabase
                supabase.table("uploads").insert({
                    "id": batch_id,
                    "nome_ficheiro": ficheiro.name,
                    "total_leads": len(df),
                    "utilizador": "OGREEN"
                }).execute()

                # 2. Inserir leads no Supabase
                leads_data = []
                for _, row in df.iterrows():
                    nome_raw = row.get("nome", "")
                    empresa_raw = row.get("empresa", "")
                    # Fallback: se nome vazio, usa "Contacto da [empresa]"
                    if pd.isna(nome_raw) or str(nome_raw).strip() == "":
                        nome_final = f"Contacto da {empresa_raw}" if pd.notna(empresa_raw) and str(empresa_raw).strip() else ""
                    else:
                        nome_final = str(nome_raw)
                    lead = {
                        "nome": nome_final,
                        "empresa": str(empresa_raw) if pd.notna(empresa_raw) else "",
                        "telefone": str(row.get("telefone", "")).replace(" ", "") if pd.notna(row.get("telefone")) else "",
                        "email": str(row.get("email", "")) if pd.notna(row.get("email")) else "",
                        "notas": str(row.get("notas", "")) if pd.notna(row.get("notas")) else "",
                        "canal": str(row["canal"]),
                        "origem": str(row.get("origem", "")) if pd.notna(row.get("origem")) else "",
                        "batch_id": batch_id,
                        "status": "pendente"
                    }
                    leads_data.append(lead)

                try:
                    supabase.table("leads").insert(leads_data).execute()
                except Exception as db_err:
                    st.error(f"Erro Supabase: {db_err}")
                    st.json(leads_data[0] if leads_data else {})
                    return

                # 3. Enviar cada lead para o Make webhook
                enviados = 0
                erros_envio = 0

                progress = st.progress(0)
                for i, lead in enumerate(leads_data):
                    try:
                        canal = lead.get("canal", "sms")
                        webhook_url = WEBHOOKS.get(canal)
                        if not webhook_url:
                            erros_envio += 1
                            progress.progress((i + 1) / len(leads_data))
                            continue
                        resp = requests.post(
                            webhook_url,
                            json={
                                "lead_id": lead.get("id", ""),
                                "batch_id": batch_id,
                                **{k: v for k, v in lead.items() if k not in ["batch_id", "status"]}
                            },
                            timeout=10
                        )
                        if resp.status_code == 200:
                            enviados += 1
                        else:
                            erros_envio += 1
                    except Exception:
                        erros_envio += 1

                    progress.progress((i + 1) / len(leads_data))

                # Resultado
                if erros_envio == 0:
                    st.success(f"✅ {enviados} leads enviadas para o agente com sucesso!")
                else:
                    st.warning(f"⚠️ {enviados} enviadas, {erros_envio} com erro. Verifique o webhook Make.")

                st.info("**Batch ID:** " + batch_id + " — use este ID para acompanhar no dashboard.")


# === PÁGINA: Dashboard ===
def pagina_dashboard():
    st.markdown('<p class="main-header">📊 Dashboard</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Visão geral do desempenho do agente comercial.</p>', unsafe_allow_html=True)

    # Período
    col_filtro1, col_filtro2 = st.columns(2)
    with col_filtro1:
        periodo = st.selectbox("Período", [
            "Últimos 7 dias", "Últimos 30 dias", "Últimos 90 dias", "Tudo"
        ])
    with col_filtro2:
        filtro_canal = st.multiselect("Canal", ["sms", "email", "whatsapp", "telefone"], default=["sms", "email", "whatsapp", "telefone"])

    # Calcular data de corte
    if periodo == "Últimos 7 dias":
        data_corte = (datetime.now() - timedelta(days=7)).isoformat()
    elif periodo == "Últimos 30 dias":
        data_corte = (datetime.now() - timedelta(days=30)).isoformat()
    elif periodo == "Últimos 90 dias":
        data_corte = (datetime.now() - timedelta(days=90)).isoformat()
    else:
        data_corte = "2000-01-01"

    # Buscar dados
    try:
        contactos_resp = supabase.table("contactos") \
            .select("*, leads(nome, empresa, canal, origem)") \
            .gte("data_hora", data_corte) \
            .execute()
        contactos = contactos_resp.data or []

        leads_resp = supabase.table("leads") \
            .select("*") \
            .in_("canal", filtro_canal) \
            .execute()
        leads = leads_resp.data or []
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return

    # Filtrar contactos por canal
    contactos_filtrados = [
        c for c in contactos
        if c.get("canal_usado") in filtro_canal
    ]

    # --- KPIs ---
    total_leads = len(leads)
    total_contactos = len(contactos_filtrados)
    interessados = len([c for c in contactos_filtrados if c.get("classificacao") == "Interessado"])
    encaminhar = len([c for c in contactos_filtrados if c.get("classificacao") == "Encaminhar para equipa comercial"])
    sem_resposta = len([c for c in contactos_filtrados if c.get("classificacao") == "Sem resposta"])
    opt_out = len([c for c in contactos_filtrados if c.get("classificacao") == "Pedido de remoção de contactos"])

    taxa_interesse = f"{((interessados + encaminhar) / total_contactos * 100):.0f}%" if total_contactos > 0 else "—"

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Leads", total_leads)
    with col2:
        st.metric("Contactados", total_contactos)
    with col3:
        st.metric("Interessados", interessados + encaminhar)
    with col4:
        st.metric("Taxa de Interesse", taxa_interesse)
    with col5:
        st.metric("Opt-out", opt_out)

    st.divider()

    # --- Gráficos ---
    if contactos_filtrados:
        col_chart1, col_chart2 = st.columns(2)

        with col_chart1:
            st.markdown("#### Classificação dos Contactos")
            class_counts = {}
            for c in contactos_filtrados:
                cls = c.get("classificacao", "Desconhecido")
                class_counts[cls] = class_counts.get(cls, 0) + 1

            chart_df = pd.DataFrame({
                "Classificação": list(class_counts.keys()),
                "Total": list(class_counts.values())
            })
            st.bar_chart(chart_df, x="Classificação", y="Total", color=OGREEN_PRIMARY)

        with col_chart2:
            st.markdown("#### Contactos por Canal")
            canal_counts = {}
            for c in contactos_filtrados:
                canal = c.get("canal_usado", "—")
                canal_counts[canal] = canal_counts.get(canal, 0) + 1

            canal_df = pd.DataFrame({
                "Canal": list(canal_counts.keys()),
                "Total": list(canal_counts.values())
            })
            st.bar_chart(canal_df, x="Canal", y="Total", color=OGREEN_LIGHT)

        # Nível de interesse
        st.markdown("#### Nível de Interesse")
        nivel_counts = {}
        for c in contactos_filtrados:
            nivel = c.get("nivel_interesse", "—")
            nivel_counts[nivel] = nivel_counts.get(nivel, 0) + 1

        nivel_df = pd.DataFrame({
            "Nível": list(nivel_counts.keys()),
            "Total": list(nivel_counts.values())
        })
        st.bar_chart(nivel_df, x="Nível", y="Total", color=OGREEN_ACCENT)

    else:
        st.info("Ainda não há contactos registados para este período.")


# === PÁGINA: Histórico ===
def pagina_historico():
    st.markdown('<p class="main-header">📋 Histórico de Contactos</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Registo detalhado de todas as interacções com leads.</p>', unsafe_allow_html=True)

    # Filtros
    col1, col2, col3 = st.columns(3)
    with col1:
        filtro_class = st.selectbox("Classificação", [
            "Todas",
            "Interessado",
            "Talvez / contactar mais tarde",
            "Não interessado",
            "Encaminhar para equipa comercial",
            "Pedido de remoção de contactos",
            "Sem resposta"
        ])
    with col2:
        filtro_canal = st.selectbox("Canal", ["Todos", "sms", "email", "whatsapp", "telefone"])
    with col3:
        filtro_nivel = st.selectbox("Nível de Interesse", ["Todos", "Alto", "Médio", "Baixo", "Nenhum"])

    # Query
    try:
        query = supabase.table("contactos") \
            .select("*, leads(nome, empresa, telefone, email, canal, origem)") \
            .order("data_hora", desc=True)

        if filtro_class != "Todas":
            query = query.eq("classificacao", filtro_class)
        if filtro_canal != "Todos":
            query = query.eq("canal_usado", filtro_canal)
        if filtro_nivel != "Todos":
            query = query.eq("nivel_interesse", filtro_nivel)

        resp = query.limit(200).execute()
        contactos = resp.data or []
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return

    if not contactos:
        st.info("Nenhum contacto encontrado com os filtros seleccionados.")
        return

    st.markdown(f"**{len(contactos)} contactos encontrados**")

    # Helper para valores nulos
    def val(v, fallback="—"):
        if v is None or str(v).strip() == "" or str(v).strip().lower() == "none":
            return fallback
        return str(v)

    # Construir tabela
    rows = []
    contacto_ids = []
    lead_ids = []
    for c in contactos:
        lead = c.get("leads") or {}
        contacto_ids.append(c.get("id"))
        lead_ids.append(c.get("lead_id"))
        rows.append({
            "Data": (c.get("data_hora", "") or "")[:16].replace("T", " "),
            "Nome": val(lead.get("nome")),
            "Empresa": val(lead.get("empresa")),
            "Canal": val(c.get("canal_usado")),
            "Classificação": val(c.get("classificacao")),
            "Interesse": val(c.get("nivel_interesse")),
            "Resumo": val(c.get("resumo_interacao")),
            "Próxima Acção": val(c.get("proxima_acao")),
        })

    df = pd.DataFrame(rows)

    # Tabela com selecção para apagar
    event = st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="multi-row",
    )

    # Botão apagar seleccionados
    selected_rows = event.selection.rows if event.selection else []
    if selected_rows:
        if st.button(f"🗑️ Apagar {len(selected_rows)} registo(s) seleccionado(s)", type="primary"):
            erros_del = 0
            for idx in selected_rows:
                try:
                    cid = contacto_ids[idx]
                    lid = lead_ids[idx]
                    supabase.table("contactos").delete().eq("id", cid).execute()
                    if lid:
                        supabase.table("leads").delete().eq("id", lid).execute()
                except Exception:
                    erros_del += 1
            if erros_del == 0:
                st.success(f"✅ {len(selected_rows)} registo(s) apagado(s).")
            else:
                st.warning(f"⚠️ {erros_del} erro(s) ao apagar.")
            st.rerun()

    # Transcrição da conversa (WhatsApp)
    if len(selected_rows) == 1:
        idx = selected_rows[0]
        c = contactos[idx]
        lead = c.get("leads") or {}
        telefone = lead.get("telefone", "")
        canal = c.get("canal_usado", "")

        # Tentar obter telefone: do lead, ou directamente do contacto
        if not telefone:
            telefone = c.get("telefone", "")

        if canal == "whatsapp" and telefone:
            st.divider()
            st.markdown("#### 💬 Transcrição da Conversa")
            try:
                hist_resp = supabase.rpc("get_chat_history", {"p_phone": telefone}).execute()
                hist_text = str(hist_resp.data) if hist_resp.data else ""

                if hist_text and hist_text != "None":
                    for line in hist_text.split("\n"):
                        line = line.strip()
                        if not line:
                            continue
                        if line.startswith("Lead:"):
                            with st.chat_message("user", avatar="👤"):
                                st.write(line[5:].strip())
                        elif line.startswith("Eva:"):
                            with st.chat_message("assistant", avatar="🤖"):
                                st.write(line[4:].strip())
                else:
                    st.info("Sem histórico de conversa disponível.")
            except Exception as e:
                st.error(f"Erro ao carregar transcrição: {e}")
        elif canal != "whatsapp":
            st.divider()
            st.info("Transcrição disponível apenas para o canal WhatsApp.")

    st.divider()

    # Export
    buffer_export = io.BytesIO()
    df.to_excel(buffer_export, index=False, engine="openpyxl")
    st.download_button(
        "⬇️ Exportar para Excel",
        buffer_export.getvalue(),
        file_name=f"ogreen_contactos_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# --- Router ---
if pagina == "📤 Upload de Leads":
    pagina_upload()
elif pagina == "📊 Dashboard":
    pagina_dashboard()
elif pagina == "📋 Histórico de Contactos":
    pagina_historico()

# --- Footer ---
st.markdown(f"""
<div style="text-align: center; padding: 2rem 0 1rem; color: #BDBDBD; font-size: 0.75rem;">
    OGREEN Advanced Waste Technologies &copy; 2026 &mdash; Agente Comercial IA
</div>
""", unsafe_allow_html=True) Exception as e:
                st.error(f"Erro ao carregar transcrição: {e}")
        elif canal != "whatsapp":
            st.divider()
            st.info("Transcrição disponível apenas para o canal WhatsApp.")

    st.divider()

    # Export
    buffer_export = io.BytesIO()
    df.to_excel(buffer_export, index=False, engine="openpyxl")
    st.download_button(
        "⬇️ Exportar para Excel",
        buffer_export.getvalue(),
        file_name=f"ogreen_contactos_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# --- Router ---
if pagina == "📤 Upload de Leads":
    pagina_upload()
elif pagina == "📊 Dashboard":
    pagina_dashboard()
elif pagina == "📋 Histórico de Contactos":
    pagina_historico()

# --- Footer ---
st.markdown(f"""
<div style="text-align: center; padding: 2rem 0 1rem; color: #BDBDBD; font-size: 0.75rem;">
    OGREEN Advanced Waste Technologies &copy; 2026 &mdash; Agente Comercial IA
</div>
""", unsafe_allow_html=True)
