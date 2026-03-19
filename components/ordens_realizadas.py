import streamlit as st
import plotly.express as px
from core.processamento import agrupar_ordens_por_tempo

def renderizar_ordens_realizadas(df_encerradas, centros_selecionados_externos=None):
    """Renderiza a aba de Ordens Realizadas com filtros e gráficos de volumetria."""
    st.write("#### Análise de Ordens Realizadas")
    
    if df_encerradas is None or df_encerradas.empty:
        st.warning("Não há dados de ordens encerradas.")
        return

    col_f0, col_f1, col_f2 = st.columns(3)
    visao_tempo = col_f0.selectbox("Agrupar gráfico por:", ["Dia", "Semana", "Mês"], index=2, key="visao_tempo_ordens")
    
    # Camada Anticorrupção/Filtro
    col_centro = 'Centro trab.respons.'
    
    if col_centro in df_encerradas.columns:
        # Se não vier de fora (carregamento inicial ou erro), calculamos aqui os totais para o multiselect
        centros_base = df_encerradas[col_centro].dropna().unique().tolist()
        
        # Filtro de Centro (Interno ou Externo)
        if centros_selecionados_externos is not None:
            centros_selecionados = centros_selecionados_externos
        else:
            centros_selecionados = col_f1.multiselect(
                "Filtrar Centro:", 
                options=centros_base, 
                default=centros_base, 
                key="filtro_centro_ordens_fallback"
            )

        tipos_existentes = df_encerradas['Classificacao_Ordem'].dropna().unique().tolist() if 'Classificacao_Ordem' in df_encerradas.columns else []
        tipos_selecionados = col_f2.multiselect("Filtrar Tipo de Ordem:", options=tipos_existentes, default=tipos_existentes, key="filtro_tipo_ordens") if tipos_existentes else None
        
        df_enc_filtrado, df_grafico = agrupar_ordens_por_tempo(df_encerradas, centros_selecionados, visao_tempo, tipos_selecionados)
        
        if not df_enc_filtrado.empty and 'Classificacao_Ordem' in df_enc_filtrado.columns:
            st.markdown("##### 📈 Volumetria por Tipo de Ordem")
            contagem = df_enc_filtrado['Classificacao_Ordem'].value_counts()
            col_metricas = st.columns(len(contagem) if len(contagem) > 0 else 1)
            for idx, (tipo, qtd) in enumerate(contagem.items()):
                col_metricas[idx % len(col_metricas)].metric(label=tipo, value=qtd)
            st.markdown("---")
        
        if not df_grafico.empty:
            fig = px.bar(df_grafico, x=visao_tempo, y='Quantidade', color='Centro trab.respons.',
                         title=f"Volumetria de Ordens por {visao_tempo}", text_auto=True, barmode='group', custom_data=['Centro trab.respons.'])
            fig.update_xaxes(type='category')
            
            try:
                selecao = st.plotly_chart(fig, use_container_width=True, on_select="rerun", selection_mode="points", key="chart_ordens_enc")
                pontos_clicados = selecao.get('selection', {}).get('points', []) if selecao else []
            except Exception:
                st.plotly_chart(fig, use_container_width=True, key="chart_ordens_enc_fallback")
                pontos_clicados = []

            if pontos_clicados:
                periodo_clicado = str(pontos_clicados[0].get('x'))
                centro_clicado = pontos_clicados[0].get('customdata', [None])[0]
                centro_clicado = centro_clicado.strip() if centro_clicado else None
                
                st.write(f"** Detalhamento: {centro_clicado} no período {periodo_clicado}**")
                df_detalhe = df_enc_filtrado[
                    (df_enc_filtrado[visao_tempo].astype(str).str.strip().str.startswith(periodo_clicado)) & 
                    (df_enc_filtrado['Centro trab.respons.'].astype(str).str.strip() == centro_clicado)
                ]
                colunas_mostrar_det = [c for c in ['Ordem', 'Classificacao_Ordem', 'Data da nota', 'Descrição', 'Localização', 'Equipamento'] if c in df_detalhe.columns]
                st.dataframe(df_detalhe[colunas_mostrar_det], use_container_width=True, hide_index=True)
        else:
            st.warning("Nenhum dado encontrado para o filtro selecionado.")
    else:
        st.dataframe(df_encerradas, use_container_width=True)
