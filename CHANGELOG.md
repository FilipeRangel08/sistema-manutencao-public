# 📋 Changelog — Dashboard de Manutenção

Registro de funcionalidades implementadas para evitar duplicação de código.

## v0.6.7 — Persistência SQLite e Motor de Dados
- **[NEW]** `core/database.py`: implementação de camada de persistência com SQLite (UPSERT via `ON CONFLICT`).
- **[MOD]** `app/main.py`: fluxo de carga refatorado para priorizar o banco de dados; upload agora sincroniza e recarrega automaticamente.
- **[MOD]** `core/processamento.py`: 
  - `processar_planilha_horas()`: adicionado tratamento de nulos (`fillna`) em datas/horas para chaves do banco.
  - `unificar_dados_sap()`: simplificada e otimizada para operar sobre dados persistidos.
- **[FIX]** `components/ordens_pendentes.py`: corrigida quebra de indentação e lógica de filtros após refatoração global.

## v0.6.6 — Arquitetura de Componentes (Modularização)
- **[NEW]** Diretório `components/`: implementação de lógica de UI segmentada por arquivos.
- **[MOD]** `app/main.py`: agora atua como orquestrador central, importando e chamando componentes isolados.
- **[DEL]** `app/visoes.py`: arquivo deletado (seu conteúdo foi redistribuído em componentes).

## v0.6.5 — Segmentação de Análise (Corretivas vs Preventivas)
- **[MOD]** `core/processamento.py`: adicionada função `obter_top_n_por_tipo()` para suporte a análises segmentadas.
- **[MOD]** `app/visoes.py`: seção de Maus Atores dividida em dois gráficos lado a lado: "Maus Atores (Corretivas)" e "Saúde do Ativo (Preventivas)".
- **[MOD]** `app/visoes.py`: unificada interatividade de clique (drill-down) para ambos os gráficos, sincronizando com a tabela de detalhes.

## v0.6.4 — Refinamento Visual e Interatividade (Bad Actors)
- **[MOD]** `app/visoes.py`: gráfico de Maus Atores refinado com `bargap=0.4`, rótulos de dados e eixo X com ticks inteiros.
- **[FIX]** `app/visoes.py`: corrigida interatividade do drill-down sincronizando o clique no gráfico com o `st.session_state` do seletor manual.

## v0.6.3 — Correções no Dashboard de Maus Atores
- **[MOD]** `core/processamento.py`: corrigida contagem de ordens em `analisar_bad_actors()` usando `.nunique('Ordem')` para evitar inflação por apontamentos de horas.
- **[MOD]** `app/visoes.py`: tabela de detalhamento agora agrupa dados por Ordem, somando as horas (`sum`) e concatenando executantes.
- **[MOD]** `app/visoes.py`: incluída coluna de Data formatada no detalhamento de ordens.
- **[FIX]** `app/visoes.py`: removido código residual e melhorada a estrutura de renderização do detalhamento.

## v0.6.2 — Memória Nativa no Agente IA
- **[MOD]** `core/ia_agente.py`: integrada memória nativa `ConversationBufferWindowMemory` (k=3) do pacote `langchain_classic` para compatibilidade com LangChain 1.x.
- **[MOD]** `core/ia_agente.py`: prefixo do sistema atualizado para incluir o placeholder `{chat_history}`, permitindo que o agente responda perguntas de acompanhamento (follow-up).
- **[MOD]** `core/ia_agente.py`: refatorada função `renderizar_chat` para utilizar o `agente.invoke` de forma simplificada, delegando a gestão de histórico ao executor nativo.

## v0.6.1 — Melhoria de Contexto IA e Dashboard Interativo
- **[MOD]** `core/ia_agente.py`: atualizado o prompt do sistema com diretrizes explícitas de filtragem por status (`Status_SAP`) para evitar alucinações.
- **[MOD]** `core/processamento.py`: refatorada função `analisar_bad_actors()` para agrupar por local e tipo de ordem, permitindo visualizações empilhadas.
- **[MOD]** `app/visoes.py`: 
  - Gráfico de Maus Atores agora é um Bar Stacked (Corretivas vs Preventivas).
  - Implementado Drill-down interativo via clique no gráfico (`on_select`) com fallback para `st.selectbox`.
  - Adicionado detalhamento em tabela (`st.dataframe`) com Número da Ordem, Descrição, Status, Executante e Horas.

---

## v0.5.0 — Unificação de Dados para IA (Cross-Analysis)
- **[NOVO]** `core/processamento.py` → `unificar_dados_sap()`: une abas de Horas, Ordens Abertas e Encerradas via Merge (Left Join).
- **[MOD]** `app/main.py`: agora gera o `df_sap_completo` após o upload e o repassa ao assistente de IA.
- **[MOD]** `core/ia_agente.py`: prompt do sistema atualizado para reconhecer a base unificada.
- **[MOD]** `ARQUITETURA_REGRAS.md`: adicionada diretriz sobre Data Prep unificado.

## v0.4.0 — Integração do Chat com IA (LangChain + Gemini)
- **[NOVO]** `core/ia_agente.py` — Módulo completo do assistente de IA.
  - `renderizar_chat(df)`: componente de chat reutilizável (histórico via `st.session_state`).
  - `_criar_agente(df)`: inicializa `ChatGoogleGenerativeAI` + `create_pandas_dataframe_agent`.
  - `_obter_agente(df)`: cache do agente no `session_state` com invalidação por shape do DF.
- **[MOD]** `app/main.py` — Aba "🤖 Assistente IA" agora chama `renderizar_chat()` (placeholder removido).
- **[MOD]** `requirements.txt` — Adicionados: `langchain`, `langchain-google-genai`, `langchain-experimental`, `google-generativeai`.

## v0.3.0 — Correção de Bug (Turno) e Cache
- **[MOD]** `core/processamento.py` — Dicionário `REGRAS_HORARIO` como fonte única de verdade para horas por regime.
- **[MOD]** `core/processamento.py` — Funções de leitura decoradas com `@st.cache_data`.

## v0.2.0 — Filtros de Tipos de Ordens e Métricas
- **[MOD]** `core/processamento.py` — `classificar_ordem()` identifica tipos (COR, PREV, IG, PP, CRI, INFRA, Fabricação) via descrição.
- **[MOD]** `app/main.py` — `st.multiselect` para tipo de ordem + `st.metric` com contagens (Realizadas e Pendentes).

## v0.1.0 — Refatoração Inicial (MVC + Unificação)
- **[MOD]** `core/processamento.py` — Toda lógica pesada de Pandas migrada da interface. Funções: `preparar_dados_efetivo`, `calcular_cruzamento_horas`, `agrupar_ordens_por_tempo`.
- **[MOD]** `app/main.py` — Single Page App com `st.tabs` (Dashboards + IA), upload na sidebar, session_state centralizado.
- **[DEL]** `app/pages/` — Pasta de navegação fragmentada removida.
