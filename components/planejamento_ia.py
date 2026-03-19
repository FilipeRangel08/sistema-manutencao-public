import streamlit as st
import pandas as pd
import numpy as np
import io

def renderizar_planejamento_semanal(df_abertas):
    """Componente: Planejamento Semanal Automático (Estilo Visual + Excel)."""
    
    st.subheader("🗓️ Planejamento Semanal de Manutenção")
    
    if df_abertas is None or df_abertas.empty:
        st.warning("É necessário carregar as Ordens Pendentes (Aba ABERTAS) primeiro.")
        return

    st.info(" O sistema agrupa e prioriza as ordens por Equipe. Baixe a planilha para atribuir os executantes.")
    
    if st.button(" Gerar Planejamento por Equipe"):
        with st.spinner("Organizando as ordens e montando as tabelas..."):
            try:
                df_plan = df_abertas.copy()
                
                # 1. Identificar Colunas
                col_centro = next((c for c in ['Centro trab.respons.', 'Equipe'] if c in df_plan.columns), None)
                col_prio = next((c for c in ['Prioridade'] if c in df_plan.columns), None)
                col_ordem = next((c for c in ['Ordem'] if c in df_plan.columns), None)
                col_nota = next((c for c in ['Nota'] if c in df_plan.columns), None)
                col_desc = next((c for c in ['Descrição', 'Texto breve'] if c in df_plan.columns), None)
                col_prio_txt = next((c for c in ['Prioridade Texto', 'TextPrioridade'] if c in df_plan.columns), None)
                col_data = next((c for c in ['Data de entrada', 'Início programado', 'Data', 'Criado em', 'Data ref.'] if c in df_plan.columns), None)
                
                if not col_centro:
                    st.error("Coluna de Equipe/Centro de Trabalho não encontrada no arquivo.")
                    return

                # Trata casos sem equipe
                df_plan[col_centro] = df_plan[col_centro].fillna('NÃO ATRIBUÍDA')
                
                # --- SOLUÇÃO DA ORDEM vs NOTA e NOTAÇÃO CIENTÍFICA ---
                # Transforma Ordem e Nota em texto puro e remove o ".0" caso o Pandas tenha lido como float
                if col_ordem:
                    df_plan[col_ordem] = df_plan[col_ordem].astype(str).str.replace(r'\.0$', '', regex=True).replace(['nan', 'None', '', '0'], np.nan)
                if col_nota:
                    df_plan[col_nota] = df_plan[col_nota].astype(str).str.replace(r'\.0$', '', regex=True).replace(['nan', 'None', '', '0'], np.nan)
                
                # Mescla: Pega Ordem. Se for nulo, pega a Nota.
                if col_ordem and col_nota:
                    df_plan['Ordem_Final'] = df_plan[col_ordem].fillna(df_plan[col_nota])
                elif col_ordem:
                    df_plan['Ordem_Final'] = df_plan[col_ordem]
                elif col_nota:
                    df_plan['Ordem_Final'] = df_plan[col_nota]
                else:
                    df_plan['Ordem_Final'] = '-'
                
                # Força como string definitiva para o Excel não transformar em E+11
                df_plan['Ordem_Final'] = df_plan['Ordem_Final'].fillna('-').astype(str)
                # -----------------------------------------------------

                # Limpa os "nan" que apareceram na sua imagem na Prioridade Texto
                if col_prio_txt:
                    df_plan[col_prio_txt] = df_plan[col_prio_txt].astype(str).replace(['nan', 'None'], '-')

                # Ordenação pela Prioridade (1, 2, 3...)
                if col_prio:
                    df_plan[col_prio] = pd.to_numeric(df_plan[col_prio], errors='ignore')
                    df_plan[col_prio] = df_plan[col_prio].fillna(99) 
                    df_plan = df_plan.sort_values(by=[col_centro, col_prio], ascending=[True, True])
                else:
                    df_plan = df_plan.sort_values(by=[col_centro])

                # Formatação da Data (DD/MM/AAAA)
                if col_data and pd.api.types.is_datetime64_any_dtype(df_plan[col_data]):
                    df_plan[col_data] = df_plan[col_data].dt.strftime('%d/%m/%Y').replace('NaT', '-')

                # 3. Separa os DataFrames em um Dicionário
                tabelas_equipes = {}
                equipes = df_plan[col_centro].unique()
                
                for equipe in equipes:
                    df_eq = df_plan[df_plan[col_centro] == equipe].head(15).copy()
                    
                    # Monta a estrutura da tabela limpa
                    df_final_eq = pd.DataFrame()
                    
                    if col_prio: df_final_eq['Prioridade'] = df_eq[col_prio].replace(99, "") 
                    
                    # Coluna Unificada e formatada em texto
                    df_final_eq['Ordem / Nota'] = df_eq['Ordem_Final']
                    
                    if col_desc: df_final_eq['Descrição'] = df_eq[col_desc]
                    if col_data: df_final_eq['Data'] = df_eq[col_data]
                    if col_prio_txt: df_final_eq['Prioridade Texto'] = df_eq[col_prio_txt]
                    
                    # Coluna do Executante
                    df_final_eq['Quem vai fazer (Executante)'] = ""
                    
                    tabelas_equipes[equipe] = df_final_eq

                # Salva no Session State
                st.session_state['tabelas_equipes'] = tabelas_equipes
                
            except Exception as e:
                st.error("Erro ao gerar as tabelas.")
                st.exception(e)

    # 4. Renderiza na tela e disponibiliza Download
    if 'tabelas_equipes' in st.session_state:
        st.markdown("---")
        
        # Gera Excel com as abas mantendo o formato texto nas ordens
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            for equipe, df_eq in st.session_state['tabelas_equipes'].items():
                nome_aba = str(equipe).replace('/', '-').replace('\\', '-')[:31]
                df_eq.to_excel(writer, index=False, sheet_name=nome_aba)
        
        # Layout e Botões
        col1, col2 = st.columns([0.7, 0.3])
        with col1:
            st.success("✅ Planejamento gerado! Ordens corrigidas e separadas por equipe.")
        with col2:
            st.download_button(
                label="📥 Baixar Excel (.xlsx)",
                data=buffer.getvalue(),
                file_name="plano_semanal_manutencao.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True
            )
        
        st.write("") 
        
        # Exibe as tabelas
        for equipe, df_eq in st.session_state['tabelas_equipes'].items():
            st.markdown(f"### Equipe: {equipe}")
            st.dataframe(df_eq, use_container_width=True, hide_index=True)
"""
        # Gera o Excel em memória (TUDO NA MESMA ABA, UMA EMBAIXO DA OUTRA)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            linha_atual = 0
            for equipe, df_eq in st.session_state['tabelas_equipes'].items():
                
                # Escreve a tabela deixando um espaço para o título
                df_eq.to_excel(writer, index=False, sheet_name='Plano Semanal', startrow=linha_atual + 1)
                
                # Escreve o nome da Equipe em cima da tabela
                worksheet = writer.sheets['Plano Semanal']
                worksheet.cell(row=linha_atual + 1, column=1, value=f"➡️ EQUIPE: {equipe}")
                
                # Pula as linhas da tabela atual + 3 linhas em branco para começar a próxima equipe
                linha_atual += len(df_eq) + 4 

"""