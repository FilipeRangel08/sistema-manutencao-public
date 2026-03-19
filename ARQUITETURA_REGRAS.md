# 🏗️ Arquitetura e Regras do Projeto (Dashboard de Manutenção + IA)

## 📌 1. Visão Geral e Tech Stack
- **Objetivo:** Aplicação web para análise e gestão de Ordens de Manutenção (Preventiva, Corretiva, etc) com um assistente de IA integrado.
- **Stack:** Python, Streamlit (UI), Pandas (Dados), LangChain (Orquestração de IA), Google Gemini (LLM).

## 📐 2. Princípios de Arquitetura (DRY - Don't Repeat Yourself)
- **Fonte Única de Verdade:** A lógica de limpeza, tradução de siglas e enriquecimento de dados deve existir em um único lugar.
- **Fluxo de Dados:** O arquivo bruto (Excel/CSV) é carregado e processado uma única vez. O DataFrame resultante (`df_processado`) é passado tanto para o módulo do Dashboard Visual quanto para o módulo de IA. Nunca reprocessar os dados para a IA.

## 🚀 3. Regras de Performance e Estado
- **Cache Obrigatório:** Toda função que lê arquivos do disco (`pd.read_excel`, `pd.read_csv`) ou faz processamento pesado de dados DEVE ser decorada com `@st.cache_data` para evitar recarregamento a cada interação no Streamlit.
- **Gerenciamento de Estado:** Alterações na interface (ex: mudar turno de ADM para Turno A) devem usar mapeamentos explícitos (dicionários) para garantir a consistência de mão dupla, atualizando o `st.session_state` ou o DataFrame imediatamente.

## 🤖 4. Regras do Módulo de IA (Chat)
- **Eficiência de Custo/Tokens:** O Chat DEVE utilizar o `create_pandas_dataframe_agent` (ou abordagem equivalente do LangChain) para interagir com os dados. **NUNCA** enviar o DataFrame inteiro como string no prompt. A IA deve gerar código Pandas/Python para consultar o `df` em memória.
- **Unificação de Dados (Data Prep)**: Para a IA, os dados de Horas e Ordens (Abertas/Encerradas) devem ser unificados em um `df_sap_completo` para permitir análises cruzadas (ex: horas por tipo de ordem). `df` em memória.
- **Memória:** O histórico da conversa deve ser mantido utilizando o `st.session_state` do Streamlit para manter o contexto.
