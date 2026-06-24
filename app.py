"""
OGREEN — Agente Comercial de IA
App Streamlit: Upload de leads + Dashboard de resultados
"""

import streamlit as st
import pandas as pd
import requests
import uuid
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
MAKE_WEBHOOK_URL = st.secrets["make"]["webhook_url"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# --- Estilos ---
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        color: #2E7D32;
    }
    .metric-card {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 16px;
        border-left: 4px solid #2E7D32;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
    }
</style>
""", unsafe_allow_html=True)


# --- Sidebar ---
with st.sidebar:
    st.markdown("### ♻️ OGREEN")
    st.markdown("**Advanced Waste Technologies**")
    st.divider()
    pagina = st.radio(
        "Navegação",
        ["📤 Upload de Leads", "📊 Dashboard", "📋 Histórico de Contactos"],
        label_visibility="collapsed"
    )


# === PÁGINA: Upload de Leads ===
def pagina_upload():
    st.markdown('<p class="main-header">📤 Upload de Leads</p>', unsafe_allow_html=True)
    st.markdown("Carregue um ficheiro Excel com os leads a contactar pelo agente.")

    # Template de exemplo
    with st.expander("📄 Ver formato esperado do Excel"):
        st.markdown("""
        O ficheiro Excel deve ter as seguintes colunas:

        | nome | empresa | telefone | email | notas | canal | origem |
        |------|---------|----------|-------|-------|-------|--------|
        | João Silva | Restaurante X | +351912345678 | joao@x.pt | Notas... | sms | website |

        - **canal**: \`telefone\`, \`sms\` ou \`email\` (obrigatório)
        - **telefone**: formato internacional (+351...) — obrigatório para SMS e telefone
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
        st.download_button(
            "⬇️ Descarregar template Excel",
            template_df.to_excel(index=False, engine="openpyxl"),
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
        colunas_obrigatorias = ["nome", "empresa", "canal"]
        colunas_em_falta = [c for c in colunas_obrigatorias if c not in df.columns]

        if colunas_em_falta:
            st.error(f"Colunas em falta: {', '.join(colunas_em_falta)}")
            return

        # Normalizar nomes de colunas
        df.columns = df.columns.str.strip().str.lower()

        # Validar canal
        canais_validos = ["telefone", "sms", "email"]
        df["canal"] = df["canal"].str.strip().str.lower()
        canais_invalidos = df[~df["canal"].isin(canais_validos)]

        if not canais_invalidos.empty:
            st.warning(f"⚠️ {len(canais_invalidos)} leads com canal inválido (ignoradas).")
            df = df[df["canal"].isin(canais_validos)]

        # Validar contactos por canal
        erros = []
        for idx, row in df.iterrows():
            if row["canal"] in ["sms", "telefone"] and pd.isna(row.get("telefone", None)):
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

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("SMS", len(df[df["canal"] == "sms"]))
        with col2:
            st.metric("Email", len(df[df["canal"] == "email"]))
        with col3:
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
                    lead = {
                        "nome": str(row.get("nome", "")),
                        "empresa": str(row.get("empresa", "")),
                        "telefone": str(row.get("telefone", "")) if pd.notna(row.get("telefone")) else None,
                        "email": str(row.get("email", "")) if pd.notna(row.get("email")) else None,
                        "notas": str(row.get("notas", "")) if pd.notna(row.get("notas")) else None,
                        "canal": str(row["canal"]),
                        "origem": str(row.get("origem", "")) if pd.notna(row.get("origem")) else None,
                        "batch_id": batch_id,
                        "status": "pendente"
                    }
                    leads_data.append(lead)

                supabase.table("leads").insert(leads_data).execute()

                # 3. Enviar cada lead para o Make webhook
                enviados = 0
                erros_envio = 0

                progress = st.progress(0)
                for i, lead in enumerate(leads_data):
                    try:
                        resp = requests.post(
                            MAKE_WEBHOOK_URL,
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

                st.info(f"**Batch ID:** \`{batch_id}\` — use este ID para acompanhar no dashboard.")


# === PÁGINA: Dashboard ===
def pagina_dashboard():
    st.markdown('<p class="main-header">📊 Dashboard</p>', unsafe_allow_html=True)

    # Período
    col_filtro1, col_filtro2 = st.columns(2)
    with col_filtro1:
        periodo = st.selectbox("Período", [
            "Últimos 7 dias", "Últimos 30 dias", "Últimos 90 dias", "Tudo"
        ])
    with col_filtro2:
        filtro_canal = st.multiselect("Canal", ["sms", "email", "telefone"], default=["sms", "email", "telefone"])

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
            st.bar_chart(chart_df, x="Classificação", y="Total", color="#2E7D32")

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
            st.bar_chart(canal_df, x="Canal", y="Total", color="#1565C0")

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
        st.bar_chart(nivel_df, x="Nível", y="Total", color="#FF8F00")

    else:
        st.info("Ainda não há contactos registados para este período.")


# === PÁGINA: Histórico ===
def pagina_historico():
    st.markdown('<p class="main-header">📋 Histórico de Contactos</p>', unsafe_allow_html=True)

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
        filtro_canal = st.selectbox("Canal", ["Todos", "sms", "email", "telefone"])
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

    # Tabela
    rows = []
    for c in contactos:
        lead = c.get("leads", {}) or {}
        rows.append({
            "Data": c.get("data_hora", "")[:16].replace("T", " "),
            "Nome": lead.get("nome", "—"),
            "Empresa": lead.get("empresa", "—"),
            "Canal": c.get("canal_usado", "—"),
            "Classificação": c.get("classificacao", "—"),
            "Interesse": c.get("nivel_interesse", "—"),
            "Resumo": c.get("resumo_interacao", "—"),
            "Próxima Acção": c.get("proxima_acao", "—"),
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Export
    st.download_button(
        "⬇️ Exportar para Excel",
        df.to_excel(index=False, engine="openpyxl"),
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
