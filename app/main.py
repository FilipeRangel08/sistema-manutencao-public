import os
import sys
import streamlit as st

# Configuração de Caminhos
pasta_atual = os.path.dirname(os.path.abspath(__file__))
pasta_raiz = os.path.abspath(os.path.join(pasta_atual, ".."))
if pasta_raiz not in sys.path:
    sys.path.append(pasta_raiz)

# Imports Core
from core.processamento import (
    processar_planilha_horas, 
    extrair_dicionario_ordens, 
    processar_planilha_ordens,
    unificar_dados_sap
)
from core.ia_agente import renderizar_chat

# Imports UI (Componentizados na v0.6.6)
from components.horas_efetivo import renderizar_horas
from components.maus_atores import renderizar_analise_ofensores
from components.ordens_realizadas import renderizar_ordens_realizadas
from components.ordens_pendentes import renderizar_ordens_pendentes
from components.planejamento_ia import renderizar_planejamento_semanal

# =========== CONFIGURAÇÃO DE PÁGINA ===========
st.set_page_config(page_title="Dashboard Inteligente & IA", page_icon="⚙️", layout="wide")
st.title("⚙️ Dashboard Integrado de Gestão & IA")

# =========== GERENCIAMENTO DE ESTADO (SESSION STATE) ===========
for chave in ['df_horas', 'df_encerradas', 'df_abertas', 'df_sap_completo', 'dicionario_ordens', 'coluna_data']:
    if chave not in st.session_state:
        st.session_state[chave] = None

# =========== BARRA LATERAL (SIDEBAR) ===========
st.sidebar.header("📂 Base de Dados")
st.sidebar.write("Faça o upload da Planilha Mestre (SAP) abaixo:")
arquivo_mestre = st.sidebar.file_uploader("", type=["xlsx", "xls"], key="up_mestre")

if arquivo_mestre is not None and st.session_state['df_horas'] is None:
    with st.spinner("Processando planilhas e extraindo dados do SAP..."):
        try:
            # 1. Processamento de Horas
            df_horas = processar_planilha_horas(arquivo_mestre)
            if df_horas is None or df_horas.empty:
                st.error("[!] Falha de Processamento: A aba de 'HORAS' não retornou dados válidos.")
                st.stop()
            
            # 2. Dicionário e Ordens
            dicionario_ordens = extrair_dicionario_ordens(arquivo_mestre)
            try:
                df_encerradas, df_abertas = processar_planilha_ordens(arquivo_mestre)
            except Exception as e:
                df_encerradas, df_abertas = None, None
                st.warning(f"Aviso: Não foi possível processar abas de Ordens. Erro: {e}")

            # 3. Unificação para IA
            df_sap_completo = unificar_dados_sap(df_horas, df_abertas, df_encerradas)

            # 4. Estado Central
            st.session_state['df_horas'] = df_horas
            st.session_state['dicionario_ordens'] = dicionario_ordens
            st.session_state['df_encerradas'] = df_encerradas
            st.session_state['df_abertas'] = df_abertas
            st.session_state['df_sap_completo'] = df_sap_completo
            st.session_state['coluna_data'] = 'Data_Calc' if 'Data_Calc' in df_horas.columns else None
            
            st.rerun()
        except Exception as e:
            st.error(f"Erro inesperado durante a carga: {e}")
            st.stop()

# =========== RENDERIZAÇÃO DA PÁGINA (ABAS) ===========
if st.session_state.get('df_horas') is not None:
    aba_dashboards, aba_plan, aba_ia = st.tabs(["📊 Dashboards Analíticos", "🗓️ Planejamento", "🤖 Assistente IA"])
    
    with aba_dashboards:
        st.write("### Controles de Exibição")
        col_chk1, col_chk2, _ = st.columns([1, 1, 3])
        if col_chk1.checkbox("Exibir Horas", value=True):
            st.markdown("---")
            renderizar_horas(st.session_state['df_horas'], st.session_state['dicionario_ordens'])
            
        if col_chk2.checkbox("Exibir Ordens", value=True):
            st.markdown("---")
            renderizar_analise_ofensores(st.session_state['df_sap_completo'])
            
            st.markdown("---")
            # --- FILTRO GLOBAL DE CENTRO DE TRABALHO (DRY) ---
            df_enc = st.session_state['df_encerradas']
            df_ab = st.session_state['df_abertas']
            
            centros_set = set()
            col_centro = 'Centro trab.respons.'
            if df_enc is not None and col_centro in df_enc.columns:
                centros_set.update(df_enc[col_centro].dropna().unique().tolist())
            if df_ab is not None and col_centro in df_ab.columns:
                centros_set.update(df_ab[col_centro].dropna().unique().tolist())
            
            centros_ordenados = sorted(list(centros_set))
            centros_selecionados = None
            
            if centros_ordenados:
                col_filt_1, _ = st.columns([2, 2])
                centros_selecionados = col_filt_1.multiselect(
                    " Filtrar Centro de Trabalho Responsável (Global):",
                    options=centros_ordenados,
                    default=centros_ordenados,
                    key="filtro_centro_global"
                )
                st.markdown("---")

            aba_enc, aba_abert = st.tabs(["✅ Ordens Realizadas", "⏳ Ordens Pendentes"])
            with aba_enc:
                renderizar_ordens_realizadas(df_enc, centros_selecionados)
            with aba_abert:
                renderizar_ordens_pendentes(df_ab, centros_selecionados)
            
    with aba_plan:
        renderizar_planejamento_semanal(st.session_state['df_abertas'])

    with aba_ia:
        renderizar_chat(st.session_state['df_sap_completo'])
else:
    st.info("Faça o upload da Planilha Mestre no menu lateral para iniciar seu sistema.")
    st.write("O sistema usa as abas: 'HORAS', 'ENCERRADAS' e 'ABERTAS'.")
