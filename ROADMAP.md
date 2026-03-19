# 🏭 ROADMAP: Sistema Integrado de Manutenção

## 🎯 Visão Geral
Dashboard desenvolvido em Python (Streamlit + Pandas + Plotly) para cruzar dados de Manutenção (Ordens SAP) com apropriação de horas trabalhadas, gerando inteligência e visibilidade de custos e carga de trabalho.

## 🏗️ Arquitetura do Sistema (Multi-Page App)
- `app/main.py`: Porta de entrada e recepção do sistema.
- `app/pages/`: Módulos independentes da interface gráfica.
- `core/processamento.py`: O "Cérebro". Regras de negócio, limpeza de dados (ETL) e cache.
- `docs/`: Documentação e rastreamento do projeto.

## ✅ Progresso (O que já está pronto)
- [x] Criação do ambiente virtual (`venv`).
- [x] Separação da lógica (Backend) da interface (Frontend).
- [x] Transição de Script Único para Sistema Multi-Páginas.
- [x] **Página 1 (Ordens):** Motor de leitura e limpeza da planilha ENCERRADAS e ABERTAS.
- [x] **Página 1 (Ordens):** Criação da função de classificação de ordens (COR, PREV, etc).
- [x] Mapeamento dos desafios de dados da planilha de apontamento de horas (Tipagem, Decimais, Turnos).

## 🔄 Fazendo Agora (Sprint Atual)
- [ ] **Página 2 (Horas):** Criar o motor de ETL no `core/processamento.py` para ler a planilha de horas.
- [ ] **Página 2 (Horas):** Converter colunas problemáticas (Vírgula para Ponto, Ordem para String).
- [ ] **Página 2 (Horas):** Criar a interface para cruzar horas apontadas x funcionários x Ordens.

## 📌 Backlog (Próximos Passos e Dívidas Técnicas)
- [ ] **Dívida Técnica (Pág 1):** Restaurar os filtros avançados e a estilização original que foi temporariamente removida na refatoração.
- [ ] **O Santo Graal:** Unir a inteligência da Página 1 com a Página 2 (Ex: Quantas horas foram gastas em ordens PREVENTIVAS vs CORRETIVAS?).
- [ ] Análise de Carga de Trabalho: Identificar apontamentos anômalos (funcionário com menos de 8h ou com excesso de horas extras).
