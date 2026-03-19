# core/db_equipe.py

import os
import json
import pandas as pd

def _get_caminho_db():
    """Retorna o caminho absoluto e seguro do arquivo JSON do banco de dados."""
    pasta_atual = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(pasta_atual, "equipe_db.json")

def carregar_banco_equipe():
    """
    Lê o histórico de funcionários. 
    Se não existir, retorna um DataFrame vazio com a estrutura correta (S1 a S5).
    """
    caminho = _get_caminho_db()
    
    if os.path.exists(caminho):
        with open(caminho, 'r', encoding='utf-8') as f:
            df = pd.DataFrame(json.load(f))
            
            # Blindagem: Garante que as colunas de semanas existam para não quebrar sistemas antigos
            for semana in ['Exc_S1', 'Exc_S2', 'Exc_S3', 'Exc_S4', 'Exc_S5']:
                if semana not in df.columns:
                    df[semana] = 0.0
            return df
            
    # Retorna estrutura padrão se for a primeira vez rodando o app
    return pd.DataFrame(columns=[
        'Matricula', 'Nome', 'Regime', 'Horas Base (Semana)', 
        'Exc_S1', 'Exc_S2', 'Exc_S3', 'Exc_S4', 'Exc_S5'
    ])

def salvar_banco_equipe(df_atualizado):
    """
    Recebe o DataFrame da tela e salva apenas as colunas estruturais e as matrizes de falta.
    As horas da semana atual (importadas do SAP) NÂO são salvas aqui.
    """
    caminho = _get_caminho_db()
    colunas_salvar = [
        'Matricula', 'Nome', 'Regime', 'Horas Base (Semana)', 
        'Exc_S1', 'Exc_S2', 'Exc_S3', 'Exc_S4', 'Exc_S5'
    ]
    
    df_salvar = df_atualizado[colunas_salvar].copy()
    
    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump(df_salvar.to_dict(orient='records'), f, ensure_ascii=False, indent=4)
