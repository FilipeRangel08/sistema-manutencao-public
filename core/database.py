import sqlite3
import pandas as pd
import streamlit as st
import os

DB_NAME = "manutencao.db"

def get_connection():
    """Retorna uma conexão com o banco de dados SQLite."""
    return sqlite3.connect(DB_NAME)

def inicializar_banco():
    """Cria as tabelas caso não existam."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tabela tb_ordens
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tb_ordens (
        ordem TEXT PRIMARY KEY,
        classificacao_ordem TEXT,
        centro_trabalho TEXT,
        data_nota TEXT,
        descricao TEXT,
        equipamento TEXT,
        local_instalacao TEXT,
        status_sap TEXT
    )
    """)
    
    # Tabela tb_horas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tb_horas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        matricula TEXT,
        ordem TEXT,
        trabalho_real REAL,
        data_inicio TEXT,
        hora_inicio TEXT,
        data_fim TEXT,
        hora_fim TEXT,
        data_calc TEXT,
        semana_trabalho INTEGER,
        UNIQUE(matricula, ordem, data_inicio, hora_inicio)
    )
    """)
    
    conn.commit()
    conn.close()

def upsert_ordens(df):
    """Realiza o UPSERT de ordens no banco."""
    if df is None or df.empty:
        return
    
    conn = get_connection()
    
    # Mapeamento para nomes do banco (Camada Anticorrupção)
    mapeamento = {
        'Ordem': 'ordem',
        'Classificacao_Ordem': 'classificacao_ordem',
        'Centro trab.respons.': 'centro_trabalho',
        'Data da nota': 'data_nota',
        'Descrição': 'descricao',
        'Equipamento': 'equipamento',
        'Denominação do loc.instalação': 'local_instalacao',
        'Status_SAP': 'status_sap'
    }
    
    df_db = df.rename(columns={k: v for k, v in mapeamento.items() if k in df.columns})
    colunas_banco = ['ordem', 'classificacao_ordem', 'centro_trabalho', 'data_nota', 'descricao', 'equipamento', 'local_instalacao', 'status_sap']
    
    # GARANTIA ANTI-ERRO: Cria a coluna em branco caso ela não exista na planilha
    for col in colunas_banco:
        if col not in df_db.columns:
            df_db[col] = None
            
    df_db = df_db[colunas_banco]

    # Usando tabela temporária para UPSERT
    df_db.to_sql("temp_ordens", conn, if_exists="replace", index=False)
    
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO tb_ordens (ordem, classificacao_ordem, centro_trabalho, data_nota, descricao, equipamento, local_instalacao, status_sap)
    SELECT ordem, classificacao_ordem, centro_trabalho, data_nota, descricao, equipamento, local_instalacao, status_sap FROM temp_ordens WHERE 1=1
    ON CONFLICT(ordem) DO UPDATE SET
        status_sap = excluded.status_sap,
        classificacao_ordem = excluded.classificacao_ordem,
        centro_trabalho = excluded.centro_trabalho,
        data_nota = excluded.data_nota,
        descricao = excluded.descricao,
        equipamento = excluded.equipamento,
        local_instalacao = excluded.local_instalacao
    """)
    
    cursor.execute("DROP TABLE temp_ordens")
    conn.commit()
    conn.close()

def upsert_horas(df):
    """Realiza o UPSERT de horas no banco."""
    if df is None or df.empty:
        return
        
    conn = get_connection()
    
    # Mapeamento para nomes do banco
    mapeamento = {
        'Matricula': 'matricula',
        'Ordem': 'ordem',
        'Trabalho_real': 'trabalho_real',
        'Data_do_início_real': 'data_inicio',
        'Hora_do_início_real': 'hora_inicio',
        'Data_do_fim_real': 'data_fim',
        'Hora_do_fim_real': 'hora_fim',
        'Data_Calc': 'data_calc',
        'Semana_Trabalho': 'semana_trabalho'
    }
    
    df_db = df.rename(columns={k: v for k, v in mapeamento.items() if k in df.columns})
    colunas_banco = ['matricula', 'ordem', 'trabalho_real', 'data_inicio', 'hora_inicio', 'data_fim', 'hora_fim', 'data_calc', 'semana_trabalho']
    
    # GARANTIA ANTI-ERRO
    for col in colunas_banco:
        if col not in df_db.columns:
            df_db[col] = None
            
    df_db = df_db[colunas_banco]

    df_db.to_sql("temp_horas", conn, if_exists="replace", index=False)
    
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO tb_horas (matricula, ordem, trabalho_real, data_inicio, hora_inicio, data_fim, hora_fim, data_calc, semana_trabalho)
    SELECT matricula, ordem, trabalho_real, data_inicio, hora_inicio, data_fim, hora_fim, data_calc, semana_trabalho FROM temp_horas WHERE 1=1
    ON CONFLICT(matricula, ordem, data_inicio, hora_inicio) DO UPDATE SET
        trabalho_real = excluded.trabalho_real,
        data_fim = excluded.data_fim,
        hora_fim = excluded.hora_fim,
        data_calc = excluded.data_calc,
        semana_trabalho = excluded.semana_trabalho
    """)
    
    cursor.execute("DROP TABLE temp_horas")
    conn.commit()
    conn.close()


@st.cache_data(show_spinner="Carregando dados do banco...")
def load_data_from_db():
    """Lê os dados do banco e retorna os DataFrames configurados."""
    if not os.path.exists(DB_NAME):
        inicializar_banco()
        return None, None
        
    conn = get_connection()
    try:
        df_ordens = pd.read_sql_query("SELECT * FROM tb_ordens", conn)
        df_horas = pd.read_sql_query("SELECT * FROM tb_horas", conn)
        
        # Mapeamento reverso para manter compatibilidade com UI
        map_ordens = {
            'ordem': 'Ordem',
            'classificacao_ordem': 'Classificacao_Ordem',
            'centro_trabalho': 'Centro trab.respons.',
            'data_nota': 'Data da nota',
            'descricao': 'Descrição',
            'equipamento': 'Equipamento',
            'local_instalacao': 'Denominação do loc.instalação',
            'status_sap': 'Status_SAP'
        }
        
        map_horas = {
            'matricula': 'Matricula',
            'ordem': 'Ordem',
            'trabalho_real': 'Trabalho_real',
            'data_inicio': 'Data_do_início_real',
            'hora_inicio': 'Hora_do_início_real',
            'data_fim': 'Data_do_fim_real',
            'hora_fim': 'Hora_do_fim_real',
            'data_calc': 'Data_Calc',
            'semana_trabalho': 'Semana_Trabalho'
        }
        
        df_ordens = df_ordens.rename(columns=map_ordens)
        df_horas = df_horas.rename(columns=map_horas)
        
        # Conversão de TIPOS (Crítico para Pandas)
        if not df_horas.empty:
            df_horas['Data_Calc'] = pd.to_datetime(df_horas['Data_Calc'], errors='coerce')
            
        if not df_ordens.empty and 'Data da nota' in df_ordens.columns:
            # Algumas ordens podem não ter data nota opcional no SAP
            df_ordens['Data_Calc'] = pd.to_datetime(df_ordens['Data da nota'], errors='coerce')
            
        return df_ordens, df_horas
    except Exception as e:
        print(f"Erro ao carregar banco: {e}")
        return None, None
    finally:
        conn.close()
