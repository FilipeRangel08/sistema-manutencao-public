Auditoria de ETL e Dicionário de Dados (v0.6.7)
Este documento detalha o estado atual do processamento de dados (ETL) para subsidiar o desenho do banco de dados SQLite.

1. Dicionário de Dados (Transformação Final)
A. Base de Horas (Apontamentos)
Processada por 
processar_planilha_horas

Coluna	Tipo (Pandas)	Origem / Regra
Matricula	object (String)	Mapeada de 'pessoal' ou 'matr'. Strip geral.
Ordem	object (String)	Mapeada de 'ordem'. Strip geral.
Trabalho_real	float64	Mapeada de 'trabalho real' ou 'horas'. Vírgula convertida para ponto.
Data_do_início_real	object	Data original da planilha.
Hora_do_início_real	object	Hora original da planilha.
Data_do_fim_real	object	Data de fim original.
Hora_do_fim_real	object	Hora de fim original.
Data_Calc	datetime64[ns]	to_datetime (dayfirst=True).
Semana_Trabalho	int64	Semana do mês (1 a 5) baseada no dia da Data_Calc.
B. Base de Ordens (Abertas e Encerradas)
Processada por 
processar_planilha_ordens

Coluna	Tipo (Pandas)	Origem / Regra
Ordem (PK)	object (String)	Identificador único da Ordem.
Classificacao_Ordem	object (String)	Calculado via 
classificar_ordem
 (Corretiva, Preventiva, etc).
Centro trab.respons.	object (String)	Centro de trabalho (Civil, Mecânica, Elétrica).
Data da nota	datetime/obj	Data de criação da ordem.
Texto breve / Descrição	object (String)	Descrição da atividade.
Equipamento	object (String)	ID/Nome do equipamento.
Denominação do loc.instalação	object (String)	Localização técnica (Usado no ranking de Bad Actors).
Status_SAP	object (String)	'Aberta' ou 'Encerrada' (Adicionado no merge final).
2. Identificação de Chaves (Primary Keys)
IMPORTANT

Tabela de Ordens: A coluna Ordem é a chave primária natural (UNIQUE). Atualmente, o sistema remove duplicatas de ordem antes do merge para garantir integridade.

Tabela de Horas: Não possui PK natural. Uma linha é definida pela combinação de Matricula + Ordem + Data/Hora Início. Para o SQLite, recomenda-se uma id (INTEGER PRIMARY KEY AUTOINCREMENT).

3. Transformações Críticas (Business Logic)
Limpeza de Strings: O sistema aplica .astype(str).str.strip() em TODAS as colunas de texto para evitar erros de casamento em merges e filtros (espaços invisíveis no fim de nomes de centros, etc).
Padronização Numérica: Conversão de strings com vírgula ('4,5') para float ('4.5'). Fundamental para o SQLite não interpretar como texto.
Classificação Heurística: A função 
classificar_ordem
 é a "alma" do dashboard. Ela varre colunas de descrição procurando prefixos (COR, PREV, IG) para categorizar a ordem. No banco, essa classificação deve ser persistida para evitar re-processamento caro.
Janelas de Tempo: O cálculo de Semana_Trabalho e as colunas de Mês e Ano derivadas da Data_Calc são essenciais para os dashboards. Sugere-se armazenar a data pura e usar funções de data do SQLite ou colunas geradas.
4. Candidatos a Tabelas SQLite
tb_horas: Dados de apontamento (Muitos para Um com Ordens).
tb_ordens: Cadastro mestre de ordens (Um para Muitos com Horas).
tb_efetivo: Cadastro de matrículas, nomes e regimes de trabalho (Atualmente gerado em memória).