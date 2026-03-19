"""
Módulo de IA - Assistente de Manutenção (LangChain + Google Gemini)
Responsabilidade Única: orquestrar o agente de IA e renderizar a interface de chat.
"""
import streamlit as st
import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain_classic.memory import ConversationBufferWindowMemory


# =========== CONFIGURAÇÃO DO AGENTE ===========

def _criar_agente(df: pd.DataFrame):
    """
    Instancia o LLM e o agente Pandas do LangChain com Memória.
    Função interna — chamada apenas uma vez e cacheada no session_state.
    """
    try:
        api_key = st.secrets.get("GOOGLE_API_KEY")
        if not api_key:
            st.error("Chave GOOGLE_API_KEY não encontrada em .streamlit/secrets.toml.")
            return None

        llm = ChatGoogleGenerativeAI(
            model="gemini-3.1-flash-lite-preview", 
            google_api_key=api_key,
            temperature=0.1,
        )

        # Configuração da Memória Nativa (Buffer Window para economia de tokens)
        memoria = ConversationBufferWindowMemory(
            memory_key="chat_history", 
            return_messages=True, 
            k=3
        )

        agente = create_pandas_dataframe_agent(
            llm,
            df,
            verbose=False,
            allow_dangerous_code=True,
            prefix=_PREFIXO_SISTEMA,
            agent_executor_kwargs={
                "handle_parsing_errors": True,
                "memory": memoria
            },
        )
        return agente
    except Exception as e:
        st.error(f"Erro ao inicializar o agente de IA: {e}")
        return None


def _obter_agente(df: pd.DataFrame):
    """
    Retorna o agente cacheado no session_state.
    Recria apenas se ainda não existir ou se o DataFrame mudou de tamanho.
    """
    if 'ia_agente' not in st.session_state:
        st.session_state['ia_agente'] = None
    if 'ia_df_shape' not in st.session_state:
        st.session_state['ia_df_shape'] = None

    shape_atual = df.shape if df is not None else None
    
    # Se mudar o DF, resetamos o agente e a memória
    if st.session_state['ia_agente'] is None or st.session_state['ia_df_shape'] != shape_atual:
        with st.spinner("Inicializando o agente de IA com memória..."):
            st.session_state['ia_agente'] = _criar_agente(df)
            st.session_state['ia_df_shape'] = shape_atual

    return st.session_state['ia_agente']


# =========== INTERFACE DE CHAT ===========

# Prompt de sistema para contextualizar o agente sobre o domínio
_PREFIXO_SISTEMA = (
    "Você é um Engenheiro de Confiabilidade e Especialista em PCM (Planejamento e Controle de Manutenção) Sênior. "
    "Seu objetivo não é apenas descrever dados, mas fornecer insights técnicos proativos. "
    "Os dados analisados são UNIFICADOS: cruzam horas apropriadas com detalhes de ordens SAP.\n\n"
    
    "DIRETRIZES DE FILTRAGEM E CONTAGEM (OBRIGATÓRIO):\n"
    "1. CONTAGEM ÚNICA: Como o DataFrame cruza ordens com horas ('Matricula', 'Trabalho_real'), uma mesma ordem aparece em múltiplas linhas. Para contar 'Quantas ordens', NUNCA conte as linhas do DataFrame (ex: não use len() ou .count() solto). Use SEMPRE a contagem de valores únicos da coluna 'Ordem' (ex: df['Ordem'].nunique()).\n"
    "2. FILTRO DE STATUS: Quando o usuário perguntar sobre ordens 'PARA REALIZAR', 'PENDENTES', 'ABERTAS', 'BACKLOG' ou simplesmente 'QUANTAS TEMOS', você DEVE filtrar o DataFrame onde 'Status_SAP' == 'Aberta'. Só filtre 'Status_SAP' == 'Encerrada' se pedirem 'REALIZADAS', 'HISTÓRICO' ou 'FEITAS'.\n"
    "3. FILTRO DE TIPO: Se o usuário pedir 'Corretivas', você DEVE aplicar o filtro 'Classificacao_Ordem' == 'Corretiva'. Não some com Preventivas ou outras classificações.\n\n"
    
    "Você deve usar jargões técnicos como MTBF (Tempo Médio Entre Falhas), MTTR (Tempo Médio para Reparo) e Bad Actors. "
    "Ao identificar falhas repetitivas em um local de instalação ('Denominação do loc.instalação'), sugira Análise de Causa Raiz (RCA) usando técnicas como 5 Porquês ou Diagrama de Ishikawa. "
    "Seja opinativo: se notar excesso de corretivas em relação a preventivas, alerte sobre o risco de quebras catastróficas. "
    "Colunas disponíveis: 'Matricula', 'Trabalho_real', 'Ordem', 'Classificacao_Ordem', 'Centro trab.respons.', 'Status_SAP' e 'Denominação do loc.instalação'.\n"
    "Responda em português brasileiro, de forma analítica e profissional. "
    "Nunca invente dados; baseie-se estritamente no DataFrame.\n\n"
    "HISTÓRICO DA CONVERSA:\n"
    "{chat_history}"
)


def renderizar_chat(df_manutencao: pd.DataFrame):
    """
    Componente completo de chat com IA.
    Recebe o DataFrame limpo e renderiza a interface de conversa.
    Deve ser chamado dentro de um container do Streamlit (tab, expander, etc).
    """
    if df_manutencao is None or df_manutencao.empty:
        st.warning("Nenhum dado carregado para análise pela IA. Faça o upload da planilha primeiro.")
        return

    # Inicializa histórico de mensagens no session_state
    if 'mensagens_chat' not in st.session_state:
        st.session_state['mensagens_chat'] = [
            {"role": "assistant", "content": (
                "Olá! Sou o assistente de IA do sistema de Manutenção. "
                "Posso analisar suas ordens, horas apropriadas e muito mais. "
                "Pergunte o que precisar! 🔧\n\n"
                "**Exemplos de perguntas:**\n"
                "- Quantas ordens corretivas temos no período?\n"
                "- Qual colaborador mais apropriou horas?\n"
                "- Mostre um resumo das ordens por centro de trabalho."
            )}
        ]

    # Renderiza histórico de mensagens
    for msg in st.session_state['mensagens_chat']:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input do usuário
    pergunta = st.chat_input("Pergunte algo sobre os dados de manutenção...")

    if pergunta:
        # Exibe a pergunta do usuário
        st.session_state['mensagens_chat'].append({"role": "user", "content": pergunta})
        with st.chat_message("user"):
            st.markdown(pergunta)

        # Processa a resposta via agente
        with st.chat_message("assistant"):
            with st.spinner("Analisando os dados..."):
                try:
                    agente = _obter_agente(df_manutencao)
                    if agente is None:
                        resposta = "Desculpe, não consegui inicializar o agente de IA. Verifique sua chave de API."
                    else:
                        # Extrai a memória do agente para garantir sincronia (se necessário)
                        # O create_pandas_dataframe_agent gerencia isso via executor
                        resultado = agente.invoke({"input": pergunta})
                        resposta = resultado.get("output", "Não consegui gerar uma resposta.")
                except Exception as e:
                    resposta = f"Ocorreu um erro ao processar sua pergunta: {str(e)}"

            st.markdown(resposta)

        # Salva a resposta no histórico
        st.session_state['mensagens_chat'].append({"role": "assistant", "content": resposta})
