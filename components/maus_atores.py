import streamlit as st
import pandas as pd
import plotly.express as px
from core.db_equipe import carregar_banco_equipe
from core.processamento import obter_top_n_por_tipo

def renderizar_analise_ofensores(df_sap_completo):
    """Renderiza a análise de Maus Atores e Preventivas com drill-down."""
    st.subheader("🛠️ Análise de Maus Atores & Preventivas")
    
    if df_sap_completo is None or df_sap_completo.empty:
        st.info("Aguardando carga de dados para análise.")
        return

    with st.expander("🚨 Ranking de Equipamentos (Maus Atores vs Preventivas)", expanded=True):
        # 1. Preparação dos Dados
        dados_cor = obter_top_n_por_tipo(df_sap_completo, 'Corretiva')
        dados_prev = obter_top_n_por_tipo(df_sap_completo, 'Preventiva')
        
        col_local_cor = dados_cor.columns[0] if not dados_cor.empty else 'Local'
        col_local_prev = dados_prev.columns[0] if not dados_prev.empty else 'Local'

        col_graf1, col_graf2 = st.columns(2)

        # --- GRÁFICO 1: MAUS ATORES (CORRETIVAS) ---
        with col_graf1:
            if not dados_cor.empty:
                fig_cor = px.bar(dados_cor, y=col_local_cor, x='Qtd_Ordens', orientation='h',
                                 title="Top 5 Maus Atores (Mais Corretivas)",
                                 color_discrete_sequence=['#EF553B'])
                fig_cor.update_layout(bargap=0.4, showlegend=False, height=350, yaxis={'categoryorder':'total ascending'})
                fig_cor.update_traces(texttemplate='%{x}', textposition='auto')
                fig_cor.update_xaxes(dtick=1)

                selecao_cor = st.plotly_chart(fig_cor, use_container_width=True, on_select="rerun", 
                                             selection_mode="points", key="chart_corretivas")
                ponto_cor = selecao_cor.get('selection', {}).get('points', []) if selecao_cor else []
                if ponto_cor:
                    st.session_state["select_bad_actor_manual"] = ponto_cor[0].get('y')
            else:
                st.info("Sem dados de Corretivas.")

        # --- GRÁFICO 2: FOCO EM PREVENÇÃO (PREVENTIVAS) ---
        with col_graf2:
            if not dados_prev.empty:
                fig_prev = px.bar(dados_prev, y=col_local_prev, x='Qtd_Ordens', orientation='h',
                                  title="Top 5 Equipamentos (Mais Preventivas)",
                                  color_discrete_sequence=['#636EFA'])
                fig_prev.update_layout(bargap=0.4, showlegend=False, height=350, yaxis={'categoryorder':'total ascending'})
                fig_prev.update_traces(texttemplate='%{x}', textposition='auto')
                fig_prev.update_xaxes(dtick=1)

                selecao_prev = st.plotly_chart(fig_prev, use_container_width=True, on_select="rerun", 
                                              selection_mode="points", key="chart_preventivas")
                ponto_prev = selecao_prev.get('selection', {}).get('points', []) if selecao_prev else []
                if ponto_prev:
                    st.session_state["select_bad_actor_manual"] = ponto_prev[0].get('y')
            else:
                st.info("Sem dados de Preventivas.")

        # --- DETALHAMENTO (DRILL-DOWN) ---
        lista_ofensores = pd.concat([dados_cor[col_local_cor] if not dados_cor.empty else pd.Series(dtype=str), 
                                     dados_prev[col_local_prev] if not dados_prev.empty else pd.Series(dtype=str)]).unique().tolist()
        
        col_sel1, col_sel2 = st.columns([2, 1])
        with col_sel1:
            local_selecionado = st.selectbox(
                "Selecione um equipamento para ver os detalhes:", 
                options=["-- Clique no gráfico ou selecione aqui --"] + lista_ofensores,
                key="select_bad_actor_manual"
            )
        
        if local_selecionado != "-- Clique no gráfico ou selecione aqui --":
            st.markdown("---")
            st.markdown(f"####  Detalhamento de Ordens: `{local_selecionado}`")
            
            # Garante que usamos o nome da coluna correto da base SAP
            col_filtro = col_local_cor if col_local_cor in df_sap_completo.columns else col_local_prev
            df_detalhe = df_sap_completo[df_sap_completo[col_filtro] == local_selecionado].copy()
            
            try:
                df_equipe = carregar_banco_equipe()
                if df_equipe is not None and not df_equipe.empty:
                    df_detalhe = pd.merge(df_detalhe, df_equipe[['Matricula', 'Nome']], on='Matricula', how='left')
                    df_detalhe['Nome'] = df_detalhe['Nome'].fillna(df_detalhe['Matricula'])
                else:
                    df_detalhe['Nome'] = df_detalhe['Matricula']
            except:
                df_detalhe['Nome'] = df_detalhe.get('Matricula', 'N/A')

            operacoes = {
                'Classificacao_Ordem': 'first',
                'Descrição': 'first',
                'Status_SAP': 'first',
                'Data_Calc': 'first',
                'Trabalho_real': 'sum',
                'Nome': lambda x: ', '.join(sorted(list(set(str(v) for v in x if pd.notna(v)))))
            }
            operacoes_reais = {k: v for k, v in operacoes.items() if k in df_detalhe.columns}
            df_agrupado = df_detalhe.groupby('Ordem').agg(operacoes_reais).reset_index()

            if 'Data_Calc' in df_agrupado.columns:
                df_agrupado['Data'] = pd.to_datetime(df_agrupado['Data_Calc']).dt.strftime('%d/%m/%Y')

            colunas_show = {
                'Ordem': 'Nº Ordem',
                'Data': 'Data',
                'Classificacao_Ordem': 'Tipo',
                'Descrição': 'Descrição da Atividade',
                'Status_SAP': 'Status',
                'Nome': 'Executantes',
                'Trabalho_real': 'Total Horas (h)'
            }
            
            cols_presentes = [c for c in colunas_show.keys() if c in df_agrupado.columns]
            df_final = df_agrupado[cols_presentes].rename(columns={k: v for k, v in colunas_show.items() if k in cols_presentes})
            
            st.dataframe(df_final.sort_values(by='Total Horas (h)', ascending=False), 
                         use_container_width=True, hide_index=True)
