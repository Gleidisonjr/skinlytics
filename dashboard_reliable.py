#!/usr/bin/env python3
"""
🎯 DASHBOARD RELIABLE - Dashboard para Dados Confiáveis de Skins CS2
Usa dados coletados via Pricempire + Steam Market APIs
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import os
from datetime import datetime, timedelta
import glob

# Configuração da página
st.set_page_config(
    page_title="Skinlytics Reliable - CS2 Skins Analytics",
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
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .source-badge {
        background: #ff6b6b;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .price-comparison {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
    }
</style>
""", unsafe_allow_html=True)

def load_latest_data():
    """Carrega o arquivo de dados mais recente"""
    try:
        # Procurar por arquivos de coleta
        collection_files = glob.glob("reliable_collection_*.json")
        if not collection_files:
            return None
        
        # Pegar o arquivo mais recente
        latest_file = max(collection_files, key=os.path.getctime)
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data, latest_file
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None, None

def create_price_comparison_chart(data):
    """Cria gráfico de comparação de preços entre fontes"""
    if not data or 'skins' not in data:
        return None
    
    # Preparar dados para o gráfico
    chart_data = []
    
    for skin_name, skin_data in data['skins'].items():
        if skin_data.get('best_price'):
            chart_data.append({
                'Skin': skin_name[:30] + '...' if len(skin_name) > 30 else skin_name,
                'Preço': skin_data['best_price']['price'],
                'Fonte': skin_data['best_price']['source'].replace('_', ' ').title(),
                'Nome Completo': skin_name
            })
    
    if not chart_data:
        return None
    
    df = pd.DataFrame(chart_data)
    
    # Gráfico de barras
    fig = px.bar(
        df.head(20),  # Top 20 skins
        x='Preço',
        y='Skin',
        color='Fonte',
        title='Top 20 Skins por Preço (Comparação de Fontes)',
        color_discrete_map={
            'pricempire': '#ff6b6b',
            'steam market': '#4ecdc4'
        },
        hover_data=['Nome Completo']
    )
    
    fig.update_layout(
        height=600,
        xaxis_title="Preço (USD)",
        yaxis_title="Skin",
        showlegend=True
    )
    
    return fig

def create_source_distribution_chart(data):
    """Cria gráfico de distribuição por fonte"""
    if not data or 'skins' not in data:
        return None
    
    # Contar skins por fonte
    source_counts = {}
    total_skins = len(data['skins'])
    
    for skin_name, skin_data in data['skins'].items():
        if skin_data.get('pricempire'):
            source_counts['Pricempire'] = source_counts.get('Pricempire', 0) + 1
        if skin_data.get('steam_market'):
            source_counts['Steam Market'] = source_counts.get('Steam Market', 0) + 1
    
    # Criar gráfico de pizza
    fig = go.Figure(data=[go.Pie(
        labels=list(source_counts.keys()),
        values=list(source_counts.values()),
        hole=0.4,
        marker_colors=['#ff6b6b', '#4ecdc4']
    )])
    
    fig.update_layout(
        title='Distribuição de Dados por Fonte',
        height=400,
        showlegend=True
    )
    
    return fig

def create_price_range_chart(data):
    """Cria gráfico de distribuição de preços por faixa"""
    if not data or 'skins' not in data:
        return None
    
    # Preparar dados de preços
    prices = []
    for skin_name, skin_data in data['skins'].items():
        if skin_data.get('best_price'):
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
        labels={'x': 'Faixa de Preço', 'y': 'Número de Skins'}
    )
    
    fig.update_layout(
        height=400,
        xaxis_title="Faixa de Preço",
        yaxis_title="Número de Skins"
    )
    
    return fig

def display_skin_details(data):
    """Exibe detalhes das skins em uma tabela interativa"""
    if not data or 'skins' not in data:
        return
    
    # Preparar dados para a tabela
    table_data = []
    
    for skin_name, skin_data in data['skins'].items():
        row = {
            'Skin': skin_name,
            'Melhor Preço': f"${skin_data['best_price']['price']:.2f}" if skin_data.get('best_price') else 'N/A',
            'Fonte': skin_data['best_price']['source'].replace('_', ' ').title() if skin_data.get('best_price') else 'N/A',
            'Pricempire': '✅' if skin_data.get('pricempire') else '❌',
            'Steam Market': '✅' if skin_data.get('steam_market') else '❌'
        }
        table_data.append(row)
    
    if table_data:
        df = pd.DataFrame(table_data)
        
        # Filtros
        col1, col2 = st.columns(2)
        
        with col1:
            source_filter = st.selectbox(
                "Filtrar por fonte:",
                ['Todas'] + list(df['Fonte'].unique())
            )
        
        with col2:
            search_term = st.text_input("Buscar skin:", "")
        
        # Aplicar filtros
        filtered_df = df.copy()
        
        if source_filter != 'Todas':
            filtered_df = filtered_df[filtered_df['Fonte'] == source_filter]
        
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
    st.markdown('<h1 class="main-header">🎮 SKINLYTICS RELIABLE</h1>', unsafe_allow_html=True)
    st.markdown('<h3 style="text-align: center; color: #666;">Dashboard de Análise de Skins CS2 - Dados Confiáveis</h3>', unsafe_allow_html=True)
    
    # Carregar dados
    data, filename = load_latest_data()
    
    if not data:
        st.error("❌ Nenhum arquivo de dados encontrado!")
        st.info("💡 Execute o `reliable_collector.py` primeiro para coletar dados")
        return
    
    # Sidebar com informações
    st.sidebar.title("📊 Informações da Coleta")
    
    if filename:
        st.sidebar.info(f"📁 **Arquivo:** {filename}")
    
    if 'metadata' in data:
        metadata = data['metadata']
        st.sidebar.metric("🎮 Total de Skins", metadata.get('total_skins', 0))
        st.sidebar.metric("💰 Pricempire", metadata.get('pricempire_count', 0))
        st.sidebar.metric("🎮 Steam Market", metadata.get('steam_count', 0))
        
        if 'collection_timestamp' in metadata:
            timestamp = metadata['collection_timestamp']
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                st.sidebar.info(f"🕒 **Coletado em:** {dt.strftime('%d/%m/%Y %H:%M')}")
            except:
                st.sidebar.info(f"🕒 **Coletado em:** {timestamp}")
    
    # Métricas principais
    st.markdown("## 📊 Métricas Principais")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Total de Skins", data.get('metadata', {}).get('total_skins', 0))
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Pricempire", data.get('metadata', {}).get('pricempire_count', 0))
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_append_html=True)
        st.metric("Steam Market", data.get('metadata', {}).get('steam_count', 0))
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        # Calcular taxa de sucesso
        total = data.get('metadata', {}).get('total_skins', 0)
        successful = sum(1 for skin in data.get('skins', {}).values() if skin.get('best_price'))
        success_rate = (successful / total * 100) if total > 0 else 0
        st.metric("Taxa de Sucesso", f"{success_rate:.1f}%")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Gráficos
    st.markdown("## 📈 Análise Visual")
    
    # Gráfico de comparação de preços
    price_chart = create_price_comparison_chart(data)
    if price_chart:
        st.plotly_chart(price_chart, use_container_width=True)
    
    # Gráficos em colunas
    col1, col2 = st.columns(2)
    
    with col1:
        source_chart = create_source_distribution_chart(data)
        if source_chart:
            st.plotly_chart(source_chart, use_container_width=True)
    
    with col2:
        price_range_chart = create_price_range_chart(data)
        if price_range_chart:
            st.plotly_chart(price_range_chart, use_container_width=True)
    
    # Detalhes das skins
    st.markdown("## 🔍 Detalhes das Skins")
    display_skin_details(data)
    
    # Informações sobre as fontes
    st.markdown("## ℹ️ Sobre as Fontes de Dados")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 💰 **Pricempire API**
        - **Rate Limit**: 120 requests/min
        - **Dados**: Preços de múltiplas plataformas
        - **Vantagem**: Comparação de mercados
        - **Status**: ✅ Confiável e estável
        """)
    
    with col2:
        st.markdown("""
        ### 🎮 **Steam Market API**
        - **Rate Limit**: 60 requests/min
        - **Dados**: Preços oficiais Steam
        - **Vantagem**: Dados oficiais da Valve
        - **Status**: ✅ Confiável e estável
        """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666;">
        🚀 **Skinlytics Reliable** - Dashboard de dados confiáveis de skins CS2<br>
        📊 Dados coletados via Pricempire + Steam Market APIs<br>
        🔒 Sem problemas de rate limiting ou bloqueios
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
