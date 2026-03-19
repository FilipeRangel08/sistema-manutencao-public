import os
import sys
import streamlit as st
import pandas as pd

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
from core.database import load_data_from_db, upsert_ordens, upsert_horas

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

# =========== CARGA INICIAL DO BANCO (v0.6.7) ===========
if st.session_state['df_horas'] is None:
    df_ordens_db, df_horas_db = load_data_from_db()
    
    # TRAVA 1: Verificar se HORAS não está vazio (antes verificava ordens)
    if df_horas_db is not None and not df_horas_db.empty:
        st.session_state['df_horas'] = df_horas_db
        st.session_state['df_sap_completo'] = unificar_dados_sap(df_horas_db, df_ordens_db)
        
        # Filtra abertas/encerradas para a UI legada
        if df_ordens_db is not None and not df_ordens_db.empty:
            st.session_state['df_abertas'] = df_ordens_db[df_ordens_db['Status_SAP'] == 'Aberta']
            st.session_state['df_encerradas'] = df_ordens_db[df_ordens_db['Status_SAP'] == 'Encerrada']
            st.session_state['dicionario_ordens'] = dict(zip(df_ordens_db['Ordem'], df_ordens_db['Descrição']))
        else:
            st.session_state['df_abertas'] = pd.DataFrame()
            st.session_state['df_encerradas'] = pd.DataFrame()
            st.session_state['dicionario_ordens'] = {}
            
        st.session_state['coluna_data'] = 'Data_Calc'


# =========== BARRA LATERAL (SIDEBAR) ===========
st.sidebar.header("📂 Base de Dados")
st.sidebar.write("Faça o upload da Planilha Mestre (SAP) abaixo:")
arquivo_mestre = st.sidebar.file_uploader("", type=["xlsx", "xls"], key="up_mestre")

if arquivo_mestre is not None:
    # CRIANDO A TRAVA: Gera um ID único para saber se este arquivo já foi lido
    id_arquivo = f"{arquivo_mestre.name}_{arquivo_mestre.size}"
    
    # Só entra no processamento se este arquivo for NOVO (quebra o loop infinito)
    if st.session_state.get('ultimo_arquivo') != id_arquivo:
        with st.spinner("Processando SAP e sincronizando Banco de Dados..."):
            try:
                # 1. Processamento de Horas
                df_horas = processar_planilha_horas(arquivo_mestre)
                if df_horas is None or df_horas.empty:
                    st.error("[!] Falha de Processamento: A aba de 'HORAS' não retornou dados válidos.")
                    st.stop()
                
                # 2. Processamento de Ordens
                df_encerradas, df_abertas = processar_planilha_ordens(arquivo_mestre)
                
                # 3. Sincronização com SQLite (v0.6.7)
                upsert_horas(df_horas)
                
                # Prepara união para persistência
                ordens_list = []
                if df_abertas is not None and not df_abertas.empty:
                    df_ab = df_abertas.copy(); df_ab['Status_SAP'] = 'Aberta'
                    ordens_list.append(df_ab)
                if df_encerradas is not None and not df_encerradas.empty:
                    df_enc = df_encerradas.copy(); df_enc['Status_SAP'] = 'Encerrada'
                    ordens_list.append(df_enc)
                
                if ordens_list:
                    df_ordens_merged = pd.concat(ordens_list, ignore_index=True)
                    upsert_ordens(df_ordens_merged)
                
                # SINALIZA QUE O ARQUIVO FOI PROCESSADO (Salva a trava)
                st.session_state['ultimo_arquivo'] = id_arquivo
                
                st.success("Dados sincronizados com sucesso!")
                st.cache_data.clear() # Limpa cache para forçar recarga do banco
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
