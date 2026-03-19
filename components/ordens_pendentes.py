import streamlit as st

def renderizar_ordens_pendentes(df_abertas, centros_selecionados_externos=None):
    """Renderiza a aba de Gestão de Ordens Pendentes com filtros e métricas."""
    st.write("#### Gestão de Ordens Abertas")
    
    if df_abertas is None or df_abertas.empty:
        st.warning("Não há dados de ordens abertas.")
        return

    # Camada Anticorrupção/Filtro
    df_abertas_filtrado = df_abertas.copy()
    col_centro = 'Centro trab.respons.'
    
    if centros_selecionados_externos is not None and col_centro in df_abertas.columns:
        df_abertas_filtrado = df_abertas_filtrado[df_abertas_filtrado[col_centro].isin(centros_selecionados_externos)]

    tem_cat = 'Categoria' in df_abertas_filtrado.columns
    tem_class = 'Classificacao_Ordem' in df_abertas_filtrado.columns
    
    if tem_cat or tem_class:
        num_cols = sum([tem_cat, tem_class])
        cols = st.columns(num_cols)
        idx = 0
        
        if tem_cat:
            categorias_existentes = df_abertas['Categoria'].dropna().unique().tolist()
            filtro_cat = cols[idx].multiselect("Categoria:", options=categorias_existentes, default=categorias_existentes, key="filtro_cat_ordens")
            df_abertas_filtrado = df_abertas_filtrado[df_abertas_filtrado['Categoria'].isin(filtro_cat)]
            idx += 1
            
        if tem_class:
            tipos_existentes = df_abertas['Classificacao_Ordem'].dropna().unique().tolist()
            filtro_tipo_ab = cols[idx].multiselect("Tipo de Ordem:", options=tipos_existentes, default=tipos_existentes, key="filtro_tipo_ord_abertas")
            df_abertas_filtrado = df_abertas_filtrado[df_abertas_filtrado['Classificacao_Ordem'].isin(filtro_tipo_ab)]
        
        if not df_abertas_filtrado.empty and tem_class:
            st.markdown("##### 📈 Quantidade por Tipo (Pendentes)")
            contagem = df_abertas_filtrado['Classificacao_Ordem'].value_counts()
            col_metricas_ab = st.columns(len(contagem) if len(contagem) > 0 else 1)
            for i, (tipo, qtd) in enumerate(contagem.items()):
                col_metricas_ab[i % len(col_metricas_ab)].metric(label=tipo, value=qtd)
            st.markdown("---")
        
        col_mostrar_ab = [c for c in ['Ordem', 'Categoria', 'Classificacao_Ordem', 'Descrição', 'Equipamento'] if c in df_abertas_filtrado.columns]
        st.dataframe(df_abertas_filtrado[col_mostrar_ab or df_abertas_filtrado.columns], use_container_width=True, hide_index=True)
    else:
        st.dataframe(df_abertas_filtrado, use_container_width=True, hide_index=True)
