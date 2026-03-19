import pandas as pd
import numpy as np
import streamlit as st

# Dicionário central de regime → horas semanais (FONTE ÚNICA DE VERDADE)
REGRAS_HORARIO = {
    "ADM": 39.0,
    "Turno A": 32.5,
    "Turno B": 32.5,
    "Turno C": 32.5,
    "Turno D": 32.5,
}

@st.cache_data(show_spinner="Processando aba HORAS...")
def processar_planilha_horas(_arquivo):
    arquivo = _arquivo
    try:
        arquivo.seek(0)
        xls = pd.ExcelFile(arquivo)
        abas_encontradas = [str(aba).strip().upper() for aba in xls.sheet_names]
        nome_aba = next((aba for aba in xls.sheet_names if str(aba).strip().upper() == 'HORAS'), None)
        
        if not nome_aba:
            print(f"[!] ERRO: Aba 'HORAS' não localizada. Abas disponíveis: {xls.sheet_names}")
            st.error(f"Erro: Aba 'HORAS' não encontrada no arquivo. Abas detectadas: {', '.join(xls.sheet_names)}")
            return None
            
        df = pd.read_excel(xls, sheet_name=nome_aba)
        
        # 1. Normalização de Busca
        colunas_originais = df.columns
        df.columns = [str(c).strip().lower() for c in colunas_originais]
        
        # STRIP GERAL: Tira espaços invisíveis de todas as strings (Bugfix UX Gráficos)
        for col in df.select_dtypes(include=['object', 'string']).columns:
            df[col] = df[col].astype(str).str.strip()
        
        # 2. CAMADA ANTICORRUPÇÃO
        mapeamento = {}
        for col in df.columns:
            if 'pessoal' in col or 'matr' in col:
                mapeamento[col] = 'Matricula'
            elif 'ordem' in col:
                mapeamento[col] = 'Ordem'
            elif 'trabalho real' in col or 'horas' in col:
                mapeamento[col] = 'Trabalho_real'
            elif 'início real' in col or 'inicio real' in col:
                if 'data' in col:
                    mapeamento[col] = 'Data_do_início_real'
                elif 'hora' in col:
                    mapeamento[col] = 'Hora_do_início_real'
            elif 'fim real' in col:
                if 'data' in col:
                    mapeamento[col] = 'Data_do_fim_real'
                elif 'hora' in col:
                    mapeamento[col] = 'Hora_do_fim_real'

        df = df.rename(columns=mapeamento)

        # Validação de Colunas Obrigatórias
        colunas_faltantes = [col for col in ['Matricula', 'Ordem', 'Trabalho_real'] if col not in df.columns]
        if colunas_faltantes:
            msg_erro = f"Colunas obrigatórias não identificadas na aba HORAS: {', '.join(colunas_faltantes)}. Colunas presentes: {', '.join(colunas_originais)}"
            print(f"[!] ERRO: {msg_erro}")
            st.error(msg_erro)
            return None
        if 'Trabalho_real' in df.columns:
            def padronizar_horas(valor):
                if pd.isna(valor) or valor == '' or str(valor).strip() == 'nan': return 0.0
                valor_str = str(valor).strip().replace(',', '.')
                try: return float(valor_str)
                except ValueError: return 0.0
            df['Trabalho_real'] = df['Trabalho_real'].apply(padronizar_horas)

        if 'Matricula' in df.columns:
            df['Matricula'] = df['Matricula'].astype(str).str.replace('.0', '', regex=False).str.strip()
            df = df[df['Matricula'] != 'nan']
            
        if 'Ordem' in df.columns:
            df['Ordem'] = df['Ordem'].astype(str).str.replace('.0', '', regex=False).str.strip()

        # 4. Cálculo de Data e Semana de Trabalho na Camada Core
        coluna_data = None
        if 'Data_do_início_real' in df.columns:
            coluna_data = 'Data_do_início_real'
        else:
            for col in df.columns:
                if 'inicio' in col or 'início' in col:
                    coluna_data = col
                    break
        
        if coluna_data:
            df['Data_Calc'] = pd.to_datetime(df[coluna_data], errors='coerce', dayfirst=True)
            def definir_semana(dia):
                if pd.isna(dia): return 0
                if dia <= 7: return 1
                elif dia <= 14: return 2
                elif dia <= 21: return 3
                elif dia <= 28: return 4
                else: return 5
            df['Semana_Trabalho'] = df['Data_Calc'].dt.day.apply(definir_semana)
        else:
            df['Data_Calc'] = pd.NaT
            df['Semana_Trabalho'] = 0

        # Tratamento de nulos nas chaves do banco (v0.6.7)
        if 'Data_do_início_real' in df.columns:
            df['Data_do_início_real'] = df['Data_do_início_real'].fillna('1900-01-01').astype(str)
        if 'Hora_do_início_real' in df.columns:
            df['Hora_do_início_real'] = df['Hora_do_início_real'].fillna('00:00:00').astype(str)

        return df
        
    except Exception as e:
        print(f"[!] ERRO CRÍTICO no processamento de horas: {str(e)}")
        return None

@st.cache_data(show_spinner="Extraindo dicionário de ordens...")
def extrair_dicionario_ordens(_arquivo_mestre):
    arquivo_mestre = _arquivo_mestre
    mapa_ordens = {}
    try:
        arquivo_mestre.seek(0)
        xls = pd.ExcelFile(arquivo_mestre)
        
        abas_alvo = [aba for aba in xls.sheet_names if str(aba).upper() in ['ABERTAS', 'ENCERRADAS']]
        
        for aba in abas_alvo:
            df = pd.read_excel(xls, sheet_name=aba)
            
            col_ordem = next((c for c in df.columns if str(c).upper().strip() == 'ORDEM'), None)
            
            nomes_desc = ['TEXTO BREVE', 'DESCRIÇÃO', 'DESCRICAO', 'TEXTO DA ORDEM']
            col_desc = next((c for c in df.columns if str(c).upper().strip() in nomes_desc), None)
            
            if col_ordem and col_desc:
                for _, row in df.dropna(subset=[col_ordem]).iterrows():
                    num_ordem = str(row[col_ordem]).replace('.0', '')
                    desc = str(row[col_desc])
                    mapa_ordens[num_ordem] = desc
                    
    except Exception as e:
        print(f"[!] Falha na extração de descrições: {e}")
        
    return mapa_ordens

def classificar_ordem(df):
    if df is None or df.empty:
        return df
    
    col_alvo = None
    
    # 1. Prioriza colunas de descrição/texto para achar as siglas
    for c in df.columns:
        c_lower = str(c).lower()
        if 'desc' in c_lower or 'texto' in c_lower or 'breve' in c_lower:
            col_alvo = c
            break
            
    # Se não achou descrição clara, caça qualquer coluna de texto grande (fallback)
    if not col_alvo:
        for c in df.select_dtypes(include=['object', 'string']).columns:
            if 'ordem' not in str(c).lower() and 'equip' not in str(c).lower() and 'loc' not in str(c).lower() and 'centro' not in str(c).lower():
                 col_alvo = c
                 break

    if col_alvo:
        def mapear_tipo(valor):
            v_str = str(valor).lower().strip()
            if v_str.startswith('cor'): return 'Corretiva'
            if v_str.startswith('prev'): return 'Preventiva'
            if v_str.startswith('ig'): return 'Inspeção Gerencial'
            if v_str.startswith('pp'): return 'Parada Programada'
            if v_str.startswith('cri'): return 'CRIQAS'
            if v_str.startswith('infra'): return 'Infraestrutura'
            if 'fabrica' in v_str or 'fabricação' in v_str: return 'Fabricação'
            return 'Outros'
            
        df['Classificacao_Ordem'] = df[col_alvo].apply(mapear_tipo)
    else:
        df['Classificacao_Ordem'] = 'Outros'
        
    return df

@st.cache_data(show_spinner="Processando abas de Ordens...")
def processar_planilha_ordens(_arquivo):
    arquivo = _arquivo
    try:
        arquivo.seek(0)
        xls = pd.ExcelFile(arquivo)
        
        df_encerradas = pd.DataFrame()
        df_abertas = pd.DataFrame()

        # Busca flexível por abas
        aba_enc = next((aba for aba in xls.sheet_names if str(aba).strip().upper() == 'ENCERRADAS'), None)
        aba_abert = next((aba for aba in xls.sheet_names if str(aba).strip().upper() == 'ABERTAS'), None)

        if aba_enc:
            df_encerradas = pd.read_excel(xls, sheet_name=aba_enc)
            
            # Normalização e STRIP GERAL
            df_encerradas.columns = [str(c).strip() for c in df_encerradas.columns]
            for col in df_encerradas.select_dtypes(include=['object', 'string']).columns:
                df_encerradas[col] = df_encerradas[col].astype(str).str.strip()
            
            # Normaliza coluna Ordem para o Merge
            col_ordem = next((c for c in df_encerradas.columns if str(c).upper() == 'ORDEM'), None)
            if col_ordem:
                df_encerradas = df_encerradas.rename(columns={col_ordem: 'Ordem'})
                df_encerradas['Ordem'] = df_encerradas['Ordem'].astype(str).str.replace('.0', '', regex=False).str.strip()
                # Normaliza coluna de Descrição para o Banco de Dados
                nomes_desc = ['TEXTO BREVE', 'DESCRIÇÃO', 'DESCRICAO', 'TEXTO DA ORDEM']
                col_desc = next((c for c in df_encerradas.columns if str(c).upper().strip() in nomes_desc), None)
                if col_desc:
                    df_encerradas = df_encerradas.rename(columns={col_desc: 'Descrição'})
                
            if 'Data da nota' in df_encerradas.columns:
                df_encerradas['Data_Calc'] = pd.to_datetime(df_encerradas['Data da nota'], errors='coerce', dayfirst=True)
                df_encerradas['Dia'] = df_encerradas['Data_Calc'].dt.date.astype(str)
                df_encerradas['Semana'] = df_encerradas['Data_Calc'].dt.isocalendar().week.astype(str)
                df_encerradas['Mês'] = df_encerradas['Data_Calc'].dt.to_period('M').astype(str)
                
            df_encerradas = classificar_ordem(df_encerradas)
        
        if aba_abert:
            df_abertas = pd.read_excel(xls, sheet_name=aba_abert)
            
            # Normalização e STRIP GERAL
            df_abertas.columns = [str(c).strip() for c in df_abertas.columns]
            for col in df_abertas.select_dtypes(include=['object', 'string']).columns:
                df_abertas[col] = df_abertas[col].astype(str).str.strip()
            
            # Normaliza coluna Ordem para o Merge
            col_ordem = next((c for c in df_abertas.columns if str(c).upper() == 'ORDEM'), None)
            if col_ordem:
                df_abertas = df_abertas.rename(columns={col_ordem: 'Ordem'})
                df_abertas['Ordem'] = df_abertas['Ordem'].astype(str).str.replace('.0', '', regex=False).str.strip()
                # Normaliza coluna de Descrição para o Banco de Dados
            nomes_desc = ['TEXTO BREVE', 'DESCRIÇÃO', 'DESCRICAO', 'TEXTO DA ORDEM']
            col_desc = next((c for c in df_abertas.columns if str(c).upper().strip() in nomes_desc), None)
            if col_desc:
                df_abertas = df_abertas.rename(columns={col_desc: 'Descrição'})

            

            df_abertas = classificar_ordem(df_abertas)
            
        return df_encerradas, df_abertas
    except Exception as e:
        print(f"[!] ERRO ao processar ordens: {e}")
        raise ValueError(f"Erro processar ordens: {e}")

def preparar_dados_efetivo(df_horas, df_memoria):
    """
    Prepara a base do efetivo cruzando matrículas com a memoria salva.
    Usa REGRAS_HORARIO como fonte única de verdade para corrigir horas
    SEMPRE que o regime mudar (ADM→Turno e Turno→ADM).
    """
    try:
        df_atuais = df_horas[['Matricula']].drop_duplicates().reset_index(drop=True)
        
        if df_memoria is not None and not df_memoria.empty:
            df_efetivo_base = pd.merge(df_atuais, df_memoria, on='Matricula', how='left')
        else:
            df_efetivo_base = df_atuais.copy()
            df_efetivo_base['Nome'] = ""
            df_efetivo_base['Regime'] = "ADM"
            df_efetivo_base['Horas Base (Semana)'] = REGRAS_HORARIO["ADM"]
            for i in range(1, 6): 
                df_efetivo_base[f'Exc_S{i}'] = 0.0
                
        # Tratamento de nulos
        df_efetivo_base['Nome'] = df_efetivo_base['Nome'].fillna("")
        df_efetivo_base['Regime'] = df_efetivo_base['Regime'].fillna("ADM")
        
        # CORREÇÃO CRÍTICA: Sobrescreve horas SEMPRE baseado no regime ATUAL
        # Isso garante que ao mudar de Turno→ADM, as horas voltem para 39.0
        df_efetivo_base['Horas Base (Semana)'] = df_efetivo_base['Regime'].map(REGRAS_HORARIO).fillna(REGRAS_HORARIO["ADM"])
        
        for i in range(1, 6): 
            if f'Exc_S{i}' not in df_efetivo_base.columns:
                df_efetivo_base[f'Exc_S{i}'] = 0.0
            df_efetivo_base[f'Exc_S{i}'] = df_efetivo_base[f'Exc_S{i}'].fillna(0.0)
            
        return df_efetivo_base
    except Exception as e:
        print(f"[!] Erro ao preparar dados de efetivo: {e}")
        return pd.DataFrame()

def calcular_cruzamento_horas(df_horas, df_efetivo_editado):
    try:
        df_calc = df_efetivo_editado.copy()
        df_calc['Nome_Exibicao'] = df_calc.apply(
            lambda row: row['Nome'] if pd.notna(row['Nome']) and str(row['Nome']).strip() != "" else row['Matricula'], axis=1
        )
        
        for i in range(1, 6):
            df_calc[f'Plan_S{i}'] = df_calc['Horas Base (Semana)'] - df_calc[f'Exc_S{i}']
        df_calc['Plan_Mes'] = df_calc[[f'Plan_S{i}' for i in range(1, 5)]].sum(axis=1)
        
        if 'Semana_Trabalho' in df_horas.columns and 'Trabalho_real' in df_horas.columns:
            df_aprop_semana = df_horas.groupby(['Matricula', 'Semana_Trabalho'])['Trabalho_real'].sum().reset_index()
            df_aprop_pivot = df_aprop_semana.pivot(index='Matricula', columns='Semana_Trabalho', values='Trabalho_real').fillna(0)
            df_aprop_pivot.columns = [f'Aprop_S{int(c)}' if int(c) > 0 else 'Aprop_S0' for c in df_aprop_pivot.columns]
            df_aprop_pivot = df_aprop_pivot.reset_index()
            
            for i in range(1, 6):
                if f'Aprop_S{i}' not in df_aprop_pivot.columns:
                    df_aprop_pivot[f'Aprop_S{i}'] = 0.0
                    
            df_aprop_pivot['Aprop_Mes'] = df_horas.groupby('Matricula')['Trabalho_real'].sum().reset_index()['Trabalho_real']
            df_cruzamento = pd.merge(df_calc, df_aprop_pivot, on='Matricula', how='left').fillna(0)
        else:
            df_cruzamento = df_calc.copy()
            for i in range(1, 6): df_cruzamento[f'Aprop_S{i}'] = 0.0
            df_cruzamento['Aprop_Mes'] = 0.0
            
        return df_cruzamento
    except Exception as e:
        print(f"[!] Erro ao calcular cruzamento de horas: {e}")
        return pd.DataFrame()

def agrupar_ordens_por_tempo(df_encerradas, centros_selecionados, visao_tempo, tipos_selecionados=None):
    try:
        if df_encerradas is None or df_encerradas.empty:
            return pd.DataFrame(), pd.DataFrame()
            
        if 'Centro trab.respons.' not in df_encerradas.columns:
            return pd.DataFrame(), pd.DataFrame()
            
        if visao_tempo not in df_encerradas.columns:
            return pd.DataFrame(), pd.DataFrame()
            
        mascara = (df_encerradas['Centro trab.respons.'].isin(centros_selecionados)) & (df_encerradas[visao_tempo].notna())
        
        if tipos_selecionados is not None and 'Classificacao_Ordem' in df_encerradas.columns:
            mascara = mascara & (df_encerradas['Classificacao_Ordem'].isin(tipos_selecionados))
            
        df_filtrado = df_encerradas[mascara]
        
        if df_filtrado.empty:
            return pd.DataFrame(), pd.DataFrame()
            
        df_grafico = df_filtrado.groupby([visao_tempo, 'Centro trab.respons.']).size().reset_index(name='Quantidade')
        df_grafico = df_grafico.sort_values(by=visao_tempo)
        return df_filtrado, df_grafico
    except Exception as e:
        print(f"[!] Erro ao agrupar ordens: {e}")
        return pd.DataFrame(), pd.DataFrame()

@st.cache_data(show_spinner="Analisando Bad Actors...")
def analisar_bad_actors(df):
    """
    Identifica os top 5 'Bad Actors' (locais de instalação com mais corretivas).
    Retorna o volume total por tipo de ordem para esses top 5 locais.
    """
    try:
        if df is None or df.empty:
            return pd.DataFrame()

        # Garante classificação (DRY)
        if 'Classificacao_Ordem' not in df.columns:
            df = classificar_ordem(df)
            
        col_local = 'Denominação do loc.instalação'
        if col_local not in df.columns:
            for col in df.columns:
                if 'localiz' in col.lower() or 'loc.inst' in col.lower():
                    col_local = col
                    break
        
        if col_local not in df.columns:
            return pd.DataFrame()

        # 1. Identifica os Top 5 baseados APENAS em Corretivas
        df_cor = df[df['Classificacao_Ordem'] == 'Corretiva'].copy()
        if df_cor.empty:
            # Ranking genérico se não houver corretivas
            top_5_locais = df.groupby(col_local).size().sort_values(ascending=False).head(5).index.tolist()
        else:
            top_5_locais = df_cor.groupby(col_local).size().sort_values(ascending=False).head(5).index.tolist()

        if not top_5_locais:
            return pd.DataFrame()

        # 2. Filtra o DataFrame original para conter apenas esses 5 locais
        df_top_5 = df[df[col_local].isin(top_5_locais)].copy()

        # 3. Agrupa por Local E Tipo de Ordem para o gráfico empilhado
        # IMPORTANTE: Usamos nunique('Ordem') para não contar duplicatas de apontamentos de horas
        bad_actors_grouped = df_top_5.groupby([col_local, 'Classificacao_Ordem'])['Ordem'].nunique().reset_index(name='Qtd_Ordens')
        
        # Adiciona uma coluna de 'Total_Corretivas' para manter a ordenação original no gráfico
        total_cor = df_cor.groupby(col_local)['Ordem'].nunique().reset_index(name='Total_Corretivas')
        bad_actors_grouped = pd.merge(bad_actors_grouped, total_cor, on=col_local, how='left').fillna(0)
        
        # Ordena pelo volume de corretivas (descendente)
        bad_actors_grouped = bad_actors_grouped.sort_values(by=['Total_Corretivas', 'Qtd_Ordens'], ascending=[False, False])

        return bad_actors_grouped
    except Exception as e:
        print(f"[!] Erro na análise de Bad Actors: {e}")
        return pd.DataFrame()

@st.cache_data(show_spinner="Analisando Equipamentos...")
def obter_top_n_por_tipo(df, tipo_ordem, n=5):
    """
    Retorna os Top N locais de instalação para um tipo específico de ordem,
    contando apenas ordens ÚNICAS para evitar inflação por apontamentos.
    """
    try:
        if df is None or df.empty:
            return pd.DataFrame()

        # Garante classificação
        if 'Classificacao_Ordem' not in df.columns:
            df = classificar_ordem(df)
            
        col_local = 'Denominação do loc.instalação'
        if col_local not in df.columns:
            for col in df.columns:
                if 'localiz' in col.lower() or 'loc.inst' in col.lower():
                    col_local = col
                    break
        
        if col_local not in df.columns:
            return pd.DataFrame()

        # Filtra pelo tipo
        df_filtrado = df[df['Classificacao_Ordem'] == tipo_ordem].copy()
        if df_filtrado.empty:
            return pd.DataFrame()

        # Agrupa por local e conta ordens únicas
        top_n = df_filtrado.groupby(col_local)['Ordem'].nunique().reset_index(name='Qtd_Ordens')
        top_n = top_n.sort_values(by='Qtd_Ordens', ascending=False).head(n)

        return top_n
    except Exception as e:
        print(f"[!] Erro ao obter Top {n} para {tipo_ordem}: {e}")
        return pd.DataFrame()

def unificar_dados_sap(df_horas, df_ordens):
    """
    Une a base de Horas com a base de Ordens (ambas vindas do banco).
    """
    try:
        if df_horas is None or df_ordens is None:
            return df_horas
        
        # Merge simples (v0.6.7) - Lógica de união de abas movida para o Banco (Upsert)
        df_completo = pd.merge(
            df_horas, 
            df_ordens, 
            on='Ordem', 
            how='left',
            suffixes=('', '_sap')
        )
        
        # Limpeza final
        for col in df_completo.select_dtypes(include=['object', 'string']).columns:
            df_completo[col] = df_completo[col].replace('nan', np.nan)
            
        return df_completo
        
    except Exception as e:
        print(f"[!] Erro na unificação de dados: {e}")
        return df_horas
