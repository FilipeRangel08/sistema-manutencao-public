import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from core.db_equipe import carregar_banco_equipe, salvar_banco_equipe
from core.processamento import (
    preparar_dados_efetivo,
    calcular_cruzamento_horas
)

def renderizar_horas(df_horas, dicionario_ordens):
    """Renderiza a seção de Apropriação de Horas & Efetivo."""
    if df_horas is None or df_horas.empty:
        st.warning("Dados de horas não disponíveis.")
        return

    st.subheader("Apropriação de Horas & Efetivo")
    st.markdown("### ⚙️ 1. Matriz de Planejamento (Semanas e Exceções)")
    
    try:
        df_memoria = carregar_banco_equipe()
        df_efetivo_base = preparar_dados_efetivo(df_horas, df_memoria)
        
        df_efetivo_editado = st.data_editor(
            df_efetivo_base,
            column_config={
                "Matricula": st.column_config.TextColumn("Matrícula SAP", disabled=True),
                "Nome": st.column_config.TextColumn("👤 Nome"),
                "Regime": st.column_config.SelectboxColumn("Regime", options=["ADM", "Turno A", "Turno B", "Turno C", "Turno D"]),
                "Horas Base (Semana)": st.column_config.NumberColumn("Base Semanal", format="%.1f h", disabled=True),
            },
            use_container_width=True,
            hide_index=True,
            key="editor_efetivo"
        )
        salvar_banco_equipe(df_efetivo_editado) 
        
        df_cruzamento = calcular_cruzamento_horas(df_horas, df_efetivo_editado)
        
        st.markdown("---")
        st.markdown("### 📊 2. Acompanhamento de Capacidade")
        
        visao_grafico = st.radio(
            "Selecione o período de análise:", 
            ["Visão Mensal (Total)", "Semana 1", "Semana 2", "Semana 3", "Semana 4", "Semana 5"],
            horizontal=True,
            key="radio_grafico_horas"
        )
        
        if visao_grafico == "Visão Mensal (Total)":
            coluna_planejado, coluna_apropriado = 'Plan_Mes', 'Aprop_Mes'
            filtro_semana = 0 
        else:
            num_semana = visao_grafico.split()[-1] 
            coluna_planejado, coluna_apropriado = f'Plan_S{num_semana}', f'Aprop_S{num_semana}'
            filtro_semana = int(num_semana)

        if coluna_planejado in df_cruzamento.columns and coluna_apropriado in df_cruzamento.columns:
            df_cruzamento['Saldo_Grafico'] = df_cruzamento[coluna_apropriado] - df_cruzamento[coluna_planejado]

            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df_cruzamento['Nome_Exibicao'], y=df_cruzamento[coluna_planejado],
                name='Planejado', marker_color='lightslategray', text=df_cruzamento[coluna_planejado].round(1), textposition='auto'
            ))
            fig.add_trace(go.Bar(
                x=df_cruzamento['Nome_Exibicao'], y=df_cruzamento[coluna_apropriado],
                name='Apropriado', marker_color='coral', text=df_cruzamento[coluna_apropriado].round(1), textposition='auto'
            ))

            fig.update_layout(barmode='group', title=f"{visao_grafico}", xaxis_title="Colaborador", yaxis_title="Horas")
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            st.markdown(f"###  3. Raio-X do Colaborador ({visao_grafico})")
            col1, col2 = st.columns([1, 3])
            
            with col1:
                nome_selecionado = st.selectbox("Selecione o Colaborador:", df_cruzamento['Nome_Exibicao'].tolist(), key="select_colaborador")
                dados_colab = df_cruzamento[df_cruzamento['Nome_Exibicao'] == nome_selecionado].iloc[0]
                mat_selecionada = dados_colab['Matricula']
                
                st.metric("Regime", dados_colab['Regime'])
                st.metric("Planejado", f"{dados_colab[coluna_planejado]:.1f}h")
                st.metric("Apropriado", f"{dados_colab[coluna_apropriado]:.1f}h")
                saldo = dados_colab['Saldo_Grafico']
                st.metric("Saldo do Período", f"{saldo:.1f}h", delta=f"{saldo:.1f}h", delta_color="normal" if saldo <= 0 else "inverse")

            with col2:
                st.write(f"**Ordens apontadas por {nome_selecionado} no período:**")
                df_ordens_do_cara = df_horas[df_horas['Matricula'] == mat_selecionada].copy()
                if filtro_semana > 0 and 'Semana_Trabalho' in df_ordens_do_cara.columns:
                    df_ordens_do_cara = df_ordens_do_cara[df_ordens_do_cara['Semana_Trabalho'] == filtro_semana]
                
                if not df_ordens_do_cara.empty:
                    df_completo = st.session_state.get('df_sap_completo')
                    if df_completo is not None:
                        df_info_extra = df_completo[['Ordem', 'Denominação do loc.instalação']].drop_duplicates(subset=['Ordem'])
                        df_ordens_do_cara = pd.merge(df_ordens_do_cara, df_info_extra, on='Ordem', how='left')

                    df_ordens_do_cara['Ordem_Str'] = df_ordens_do_cara['Ordem'].astype(str).str.replace(r'\.0$', '', regex=True)
                    df_ordens_do_cara['Descrição da Ordem'] = df_ordens_do_cara['Ordem_Str'].map(dicionario_ordens).fillna("Descrição não encontrada")
                    
                    colunas_mostrar = ['Ordem', 'Descrição da Ordem', 'Denominação do loc.instalação']
                    colunas_dict = {
                        'Ordem': 'Número da Ordem', 
                        'Descrição da Ordem': 'Descrição da Atividade',
                        'Denominação do loc.instalação': 'Local / Equipamento (SAP)'
                    }
                    
                    if 'Data_Calc' in df_ordens_do_cara.columns:
                        colunas_mostrar.append('Data_Calc')
                        colunas_dict['Data_Calc'] = 'Data de Cálculo/Início'
                        
                    colunas_mostrar.append('Trabalho_real')
                    colunas_dict['Trabalho_real'] = 'Horas Gastas'
                    
                    df_mostrar = df_ordens_do_cara[colunas_mostrar].copy()
                    df_mostrar = df_mostrar.sort_values(by='Trabalho_real', ascending=False)
                    df_mostrar = df_mostrar.rename(columns=colunas_dict)
                    
                    st.dataframe(df_mostrar, use_container_width=True, hide_index=True)
                else:
                    st.warning(f"Nenhum apontamento feito por {nome_selecionado} neste período.")
        else:
             st.error("Colunas de cálculo ausentes. Verifique a base de dados.")
    except Exception as e:
        st.error(f"Ocorreu um erro ao processar métricas de Horas: {e}")
