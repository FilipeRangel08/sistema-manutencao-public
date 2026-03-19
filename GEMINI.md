# PROJETO: Sistema de Apropriação de Horas (Integração SAP)

## 1. Contexto do Sistema
- Linguagem: Python 3.10+
- Framework de Interface: Streamlit
- Motor de Dados: Pandas e Numpy
- Objetivo: Processamento, limpeza e análise de planilhas exportadas do SAP.

## 2. Padrões de Arquitetura (A Regra de Ouro)
- Separação de Responsabilidades (MVC/Adapter):
  - Diretório `core/`: Deve conter TODA a lógica pesada, tratamento de exceções do Pandas, limpeza de strings e matemática. A interface NUNCA deve limpar dados.
  - Diretório `pages/`: Deve focar EXCLUSIVAMENTE em renderizar componentes visuais do Streamlit (`st.dataframe`, `st.button`, `st.metric`) e gerenciar o fluxo do usuário.

## 3. Diretrizes de Código e Prevenção de Falhas
- **Camada Anticorrupção:** Qualquer dado vindo do SAP deve ter suas colunas padronizadas em `core/` antes de chegar no Streamlit. Não confie em nomes de colunas com espaços ou letras maiúsculas/minúsculas.
- **Tratamento de Estado:** NUNCA modifique ou acesse uma variável no `st.session_state` sem antes verificar se ela existe usando `if 'variavel' not in st.session_state:`.
- **Falhas Elegantes:** Evite quebrar o sistema com erros fatais. Use blocos `try/except` lógicos. Se um processamento falhar, retorne `None` ou um DataFrame vazio e use `st.error()` ou `st.warning()` na interface para avisar o usuário amigavelmente.
- **Tipagem e Conversão:** Em planilhas brasileiras, converta strings com vírgula (ex: '4,500') para floats ('4.5') estritamente na camada `core`.

## 4. Estilo de Comunicação da IA
- Ao criar ou refatorar funcionalidades, escreva código limpo, comentado em português, mantendo nomes de variáveis e funções descritivas (ex: `processar_planilha_horas` em vez de `proc_plan`).
- Pense como um Engenheiro de Software: Sempre preveja como o código pode falhar ao receber dados inválidos do usuário.
