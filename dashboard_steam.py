#!/usr/bin/env python3
"""
🎮 DASHBOARD STEAM - Dashboard para Dados do Steam Market
Visualiza dados coletados via Steam Market API
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
import glob
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Skinlytics Steam - CS2 Steam Market Analytics",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #4ecdc4 0%, #44a08d 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .price-high {
        color: #28a745;
        font-weight: bold;
    }
    .price-medium {
        color: #ffc107;
        font-weight: bold;
    }
    .price-low {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

def load_latest_steam_data():
    """Carrega o arquivo de dados do Steam Market mais recente"""
    try:
        # Procurar por arquivos de coleta do Steam
        collection_files = glob.glob("steam_collection_*.json")
        if not collection_files:
            return None, None
        
        # Pegar o arquivo mais recente
        latest_file = max(collection_files, key=os.path.getctime)
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data, latest_file
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None, None

def create_price_distribution_chart(data):
    """Cria gráfico de distribuição de preços"""
    if not data or 'skins' not in data:
        return None
    
    # Preparar dados de preços
    prices = []
    for skin_name, skin_data in data['skins'].items():
        if skin_data.get('best_price') and skin_data['best_price'].get('price'):
            prices.append(skin_data['best_price']['price'])
    
    if not prices:
        return None
    
    # Criar faixas de preço
    df_prices = pd.DataFrame({'Preço': prices})
    
    # Definir faixas
    bins = [0, 10, 50, 100, 500, 1000, float('inf')]
    labels = ['$0-10', '$10-50', '$50-100', '$100-500', '$500-1000', '$1000+']
    
    df_prices['Faixa'] = pd.cut(df_prices['Preço'], bins=bins, labels=labels, include_lowest=True)
    
    # Contar por faixa
    price_distribution = df_prices['Faixa'].value_counts().sort_index()
    
    # Gráfico de barras
    fig = px.bar(
        x=price_distribution.index,
        y=price_distribution.values,
        title='Distribuição de Preços por Faixa',
        labels={'x': 'Faixa de Preço', 'y': 'Número de Skins'},
        color=price_distribution.values,
        color_continuous_scale='viridis'
    )
    
    fig.update_layout(
        height=400,
        xaxis_title="Faixa de Preço",
        yaxis_title="Número de Skins",
        showlegend=False
    )
    
    return fig

def create_top_skins_chart(data, top_n=15):
    """Cria gráfico das skins mais caras"""
    if not data or 'skins' not in data:
        return None
    
    # Preparar dados para o gráfico
    chart_data = []
    
    for skin_name, skin_data in data['skins'].items():
        if skin_data.get('best_price') and skin_data['best_price'].get('price'):
            chart_data.append({
                'Skin': skin_name[:40] + '...' if len(skin_name) > 40 else skin_name,
                'Preço': skin_data['best_price']['price'],
                'Nome Completo': skin_name,
                'Tipo': skin_data['best_price'].get('type', 'median')
            })
    
    if not chart_data:
        return None
    
    df = pd.DataFrame(chart_data)
    
    # Ordenar por preço e pegar top N
    df_sorted = df.sort_values('Preço', ascending=True).tail(top_n)
    
    # Gráfico de barras horizontais
    fig = px.bar(
        df_sorted,
        x='Preço',
        y='Skin',
        title=f'Top {top_n} Skins Mais Caras',
        color='Preço',
        color_continuous_scale='viridis',
        hover_data=['Nome Completo', 'Tipo']
    )
    
    fig.update_layout(
        height=600,
        xaxis_title="Preço (USD)",
        yaxis_title="Skin",
        showlegend=False
    )
    
    return fig

def create_volume_analysis(data):
    """Cria análise de volume de vendas"""
    if not data or 'skins' not in data:
        return None
    
    # Preparar dados de volume
    volume_data = []
    
    for skin_name, skin_data in data['skins'].items():
        if skin_data.get('price_info') and skin_data['price_info'].get('volume'):
            try:
                volume = int(skin_data['price_info']['volume'])
                if volume > 0:
                    volume_data.append({
                        'Skin': skin_name[:30] + '...' if len(skin_name) > 30 else skin_name,
                        'Volume': volume,
                        'Preço': skin_data.get('best_price', {}).get('price', 0),
                        'Nome Completo': skin_name
                    })
            except (ValueError, TypeError):
                continue
    
    if not volume_data:
        return None
    
    df_volume = pd.DataFrame(volume_data)
    
    # Top 10 por volume
    df_top_volume = df_volume.nlargest(10, 'Volume')
    
    # Gráfico de volume
    fig = px.bar(
        df_top_volume,
        x='Volume',
        y='Skin',
        title='Top 10 Skins por Volume de Vendas',
        color='Preço',
        color_continuous_scale='plasma',
        hover_data=['Nome Completo', 'Preço']
    )
    
    fig.update_layout(
        height=500,
        xaxis_title="Volume de Vendas",
        yaxis_title="Skin",
        showlegend=False
    )
    
    return fig

def display_skin_table(data):
    """Exibe tabela detalhada das skins"""
    if not data or 'skins' not in data:
        return
    
    # Preparar dados para a tabela
    table_data = []
    
    for skin_name, skin_data in data['skins'].items():
        if skin_data.get('best_price'):
            row = {
                'Skin': skin_name,
                'Preço': f"${skin_data['best_price']['price']:.2f}" if skin_data['best_price'].get('price') else 'N/A',
                'Tipo': skin_data['best_price'].get('type', 'N/A'),
                'Volume': skin_data.get('price_info', {}).get('volume', 'N/A'),
                'Preço Médio': skin_data.get('price_info', {}).get('median_price', 'N/A'),
                'Preço Mais Baixo': skin_data.get('price_info', {}).get('lowest_price', 'N/A')
            }
            table_data.append(row)
    
    if table_data:
        df = pd.DataFrame(table_data)
        
        # Filtros
        col1, col2 = st.columns(2)
        
        with col1:
            price_filter = st.selectbox(
                "Filtrar por faixa de preço:",
                ['Todas'] + ['$0-10', '$10-50', '$50-100', '$100-500', '$500+']
            )
        
        with col2:
            search_term = st.text_input("Buscar skin:", "")
        
        # Aplicar filtros
        filtered_df = df.copy()
        
        if price_filter != 'Todas':
            if price_filter == '$0-10':
                filtered_df = filtered_df[filtered_df['Preço'].str.replace('$', '').str.replace(',', '').astype(float) <= 10]
            elif price_filter == '$10-50':
                filtered_df = filtered_df[(filtered_df['Preço'].str.replace('$', '').str.replace(',', '').astype(float) > 10) & 
                                        (filtered_df['Preço'].str.replace('$', '').str.replace(',', '').astype(float) <= 50)]
            elif price_filter == '$50-100':
                filtered_df = filtered_df[(filtered_df['Preço'].str.replace('$', '').str.replace(',', '').astype(float) > 50) & 
                                        (filtered_df['Preço'].str.replace('$', '').str.replace(',', '').astype(float) <= 100)]
            elif price_filter == '$100-500':
                filtered_df = filtered_df[(filtered_df['Preço'].str.replace('$', '').str.replace(',', '').astype(float) > 100) & 
                                        (filtered_df['Preço'].str.replace('$', '').str.replace(',', '').astype(float) <= 500)]
            elif price_filter == '$500+':
                filtered_df = filtered_df[filtered_df['Preço'].str.replace('$', '').str.replace(',', '').astype(float) > 500]
        
        if search_term:
            filtered_df = filtered_df[filtered_df['Skin'].str.contains(search_term, case=False, na=False)]
        
        # Exibir tabela
        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Estatísticas dos filtros
        st.info(f"📊 Mostrando {len(filtered_df)} de {len(df)} skins")

def main():
    """Função principal do dashboard"""
    
    # Header principal
    st.markdown('<h1 class="main-header">🎮 SKINLYTICS STEAM</h1>', unsafe_allow_html=True)
    st.markdown('<h3 style="text-align: center; color: #666;">Dashboard de Análise do Steam Market CS2</h3>', unsafe_allow_html=True)
    
    # Carregar dados
    data, filename = load_latest_steam_data()
    
    if not data:
        st.error("❌ Nenhum arquivo de dados do Steam Market encontrado!")
        st.info("💡 Execute o `steam_only_collector.py` primeiro para coletar dados")
        return
    
    # Sidebar com informações
    st.sidebar.title("📊 Informações da Coleta")
    
    if filename:
        st.sidebar.info(f"📁 **Arquivo:** {filename}")
    
    if 'metadata' in data:
        metadata = data['metadata']
        st.sidebar.metric("🎮 Total de Skins", metadata.get('total_skins', 0))
        st.sidebar.metric("✅ Steam Market", metadata.get('steam_count', 0))
        
        if 'collection_timestamp' in metadata:
            timestamp = metadata['collection_timestamp']
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                st.sidebar.info(f"🕒 **Coletado em:** {dt.strftime('%d/%m/%Y %H:%M')}")
            except:
                st.sidebar.info(f"🕒 **Coletado em:** {timestamp}")
        
        if 'note' in metadata:
            st.sidebar.warning(f"⚠️ **Nota:** {metadata['note']}")
    
    # Métricas principais
    st.markdown("## 📊 Métricas Principais")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Total de Skins", data.get('metadata', {}).get('total_skins', 0))
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Steam Market", data.get('metadata', {}).get('steam_count', 0))
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        # Calcular taxa de sucesso
        total = data.get('metadata', {}).get('total_skins', 0)
        successful = sum(1 for skin in data.get('skins', {}).values() if skin.get('best_price'))
        success_rate = (successful / total * 100) if total > 0 else 0
        st.metric("Taxa de Sucesso", f"{success_rate:.1f}%")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        # Calcular valor total
        total_value = sum(skin.get('best_price', {}).get('price', 0) for skin in data.get('skins', {}).values() if skin.get('best_price'))
        st.metric("Valor Total", f"${total_value:,.0f}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Gráficos
    st.markdown("## 📈 Análise Visual")
    
    # Gráfico de distribuição de preços
    price_dist_chart = create_price_distribution_chart(data)
    if price_dist_chart:
        st.plotly_chart(price_dist_chart, use_container_width=True)
    
    # Gráficos em colunas
    col1, col2 = st.columns(2)
    
    with col1:
        top_skins_chart = create_top_skins_chart(data, top_n=10)
        if top_skins_chart:
            st.plotly_chart(top_skins_chart, use_container_width=True)
    
    with col2:
        volume_chart = create_volume_analysis(data)
        if volume_chart:
            st.plotly_chart(volume_chart, use_container_width=True)
    
    # Detalhes das skins
    st.markdown("## 🔍 Detalhes das Skins")
    display_skin_table(data)
    
    # Informações sobre a fonte
    st.markdown("## ℹ️ Sobre o Steam Market")
    
    st.markdown("""
    ### 🎮 **Steam Market API**
    - **Rate Limit**: 60 requests/min
    - **Dados**: Preços oficiais da Valve
    - **Vantagem**: Dados oficiais e confiáveis
    - **Status**: ✅ Funcionando perfeitamente
    - **Fonte**: API pública do Steam Community
    
    ### 📊 **Dados Coletados**
    - **Preço Médio**: Preço mediano das vendas
    - **Preço Mais Baixo**: Menor preço disponível
    - **Volume**: Número de itens vendidos
    - **Timestamp**: Momento da coleta
    """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666;">
        🚀 **Skinlytics Steam** - Dashboard de dados do Steam Market CS2<br>
        📊 Dados coletados via Steam Market API<br>
        🔒 Sem problemas de rate limiting ou bloqueios
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
