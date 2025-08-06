import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import time
import os
from sqlalchemy import create_engine, text

# Page config
st.set_page_config(
    page_title="CS2 Skin Tracker - Real Time Analytics",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #38bdf8;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #334155;
    }
    .stMetric {
        background: rgba(30, 41, 59, 0.6);
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #334155;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=30)  # Cache por 30 segundos
def load_data():
    """Carrega dados do banco em tempo real"""
    try:
        # Conectar ao banco
        engine = create_engine('sqlite:///./data/skins_saas.db')
        
        # Query otimizada para dados em tempo real
        query = """
        SELECT 
            l.id,
            s.market_hash_name,
            s.item_name,
            s.wear_name,
            l.price / 100.0 as price_usd,
            l.float_value,
            l.seller_username,
            l.seller_total_trades,
            l.seller_verified_trades,
            l.state,
            l.watchers,
            l.collected_at,
            s.is_stattrak,
            s.is_souvenir,
            s.rarity,
            CASE 
                WHEN s.market_hash_name LIKE '%AK-47%' OR s.market_hash_name LIKE '%M4A%' OR s.market_hash_name LIKE '%AWP%' THEN 'Rifle'
                WHEN s.market_hash_name LIKE '%Glock%' OR s.market_hash_name LIKE '%USP%' OR s.market_hash_name LIKE '%P250%' THEN 'Pistol'
                WHEN s.market_hash_name LIKE '%Knife%' OR s.market_hash_name LIKE '%Karambit%' THEN 'Knife'
                ELSE 'Other'
            END as category
        FROM listings l
        JOIN skins s ON l.skin_id = s.id
        ORDER BY l.collected_at DESC
        LIMIT 1000
        """
        
        df = pd.read_sql_query(query, engine)
        df['collected_at'] = pd.to_datetime(df['collected_at'])
        return df
        
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def get_summary_stats(df):
    """Calcula estatísticas resumidas"""
    if df.empty:
        return {}
    
    return {
        'total_listings': len(df),
        'unique_skins': df['market_hash_name'].nunique(),
        'avg_price': df['price_usd'].mean(),
        'total_value': df['price_usd'].sum(),
        'latest_update': df['collected_at'].max(),
        'price_range': {
            'min': df['price_usd'].min(),
            'max': df['price_usd'].max()
        }
    }

def main():
    # Header
    st.markdown('<h1 class="main-header">🎯 CS2 Skin Tracker - Real Time Analytics</h1>', unsafe_allow_html=True)
    st.markdown("**Dados em tempo real da CSFloat API** | Atualização automática a cada 30 segundos")
    
    # Sidebar para filtros
    with st.sidebar:
        st.header("🔧 Filtros")
        
        # Auto refresh
        auto_refresh = st.checkbox("Auto-refresh (30s)", value=True)
        if auto_refresh:
            time.sleep(30)
            st.rerun()
        
        st.divider()
        
        # Filtros de preço
        st.subheader("💰 Preço")
        price_range = st.slider("Faixa de preço (USD)", 0.0, 1000.0, (0.0, 100.0))
        
        # Filtros de categoria
        st.subheader("🎮 Categoria")
        category_filter = st.multiselect(
            "Selecione categorias",
            ["Rifle", "Pistol", "Knife", "Other"],
            default=["Rifle", "Pistol", "Knife", "Other"]
        )
        
        # Filtros de condição
        st.subheader("🔍 Condição")
        stattrak_filter = st.checkbox("Apenas StatTrak", value=False)
        souvenir_filter = st.checkbox("Apenas Souvenir", value=False)
        
        # Filtro de float
        st.subheader("📊 Float Range")
        float_range = st.slider("Float Value", 0.0, 1.0, (0.0, 1.0))
    
    # Carregar dados
    with st.spinner('🔄 Carregando dados em tempo real...'):
        df = load_data()
    
    if df.empty:
        st.error("❌ Nenhum dado encontrado. Execute o coletor primeiro!")
        st.code("python src/collectors/realtime_collector.py --duration 5")
        return
    
    # Aplicar filtros
    filtered_df = df[
        (df['price_usd'] >= price_range[0]) & 
        (df['price_usd'] <= price_range[1]) &
        (df['category'].isin(category_filter)) &
        (df['float_value'] >= float_range[0]) &
        (df['float_value'] <= float_range[1])
    ]
    
    if stattrak_filter:
        filtered_df = filtered_df[filtered_df['is_stattrak'] == True]
    if souvenir_filter:
        filtered_df = filtered_df[filtered_df['is_souvenir'] == True]
    
    # Estatísticas principais
    stats = get_summary_stats(filtered_df)
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📊 Total Listings", 
            f"{stats.get('total_listings', 0):,}",
            delta=f"+{len(filtered_df)} filtrados"
        )
    
    with col2:
        st.metric(
            "🎮 Skins Únicas", 
            f"{stats.get('unique_skins', 0):,}",
            delta="Em tempo real"
        )
    
    with col3:
        st.metric(
            "💰 Preço Médio", 
            f"${stats.get('avg_price', 0):.2f}",
            delta=f"${stats.get('price_range', {}).get('max', 0):.2f} máx"
        )
    
    with col4:
        st.metric(
            "💎 Valor Total", 
            f"${stats.get('total_value', 0):,.0f}",
            delta="Market Cap"
        )
    
    # Última atualização
    if stats.get('latest_update'):
        time_diff = datetime.now() - stats['latest_update'].replace(tzinfo=None)
        st.info(f"⏱️ Última atualização: {time_diff.seconds}s atrás ({stats['latest_update'].strftime('%H:%M:%S')})")
    
    st.divider()
    
    # Layout principal com abas
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Analytics", "📋 Listings", "🎯 Top Skins", "📊 Estatísticas"])
    
    with tab1:
        # Gráficos analíticos
        col1, col2 = st.columns(2)
        
        with col1:
            # Distribuição de preços
            fig_price = px.histogram(
                filtered_df, 
                x='price_usd', 
                nbins=30,
                title="📊 Distribuição de Preços",
                color_discrete_sequence=['#38bdf8']
            )
            fig_price.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white'
            )
            st.plotly_chart(fig_price, use_container_width=True)
        
        with col2:
            # Preços por categoria
            category_avg = filtered_df.groupby('category')['price_usd'].agg(['mean', 'count']).reset_index()
            fig_cat = px.bar(
                category_avg, 
                x='category', 
                y='mean',
                title="💰 Preço Médio por Categoria",
                color='count',
                color_continuous_scale='viridis'
            )
            fig_cat.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white'
            )
            st.plotly_chart(fig_cat, use_container_width=True)
        
        # Float vs Price correlation
        fig_scatter = px.scatter(
            filtered_df, 
            x='float_value', 
            y='price_usd',
            color='category',
            size='watchers',
            hover_data=['market_hash_name', 'seller_username'],
            title="🔗 Correlação Float vs Preço",
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig_scatter.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white'
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        # Preços ao longo do tempo
        time_data = filtered_df.set_index('collected_at').resample('5T')['price_usd'].agg(['mean', 'count'])
        fig_time = go.Figure()
        fig_time.add_trace(go.Scatter(
            x=time_data.index,
            y=time_data['mean'],
            mode='lines+markers',
            name='Preço Médio',
            line=dict(color='#38bdf8')
        ))
        fig_time.update_layout(
            title="📈 Evolução do Preço Médio",
            xaxis_title="Tempo",
            yaxis_title="Preço (USD)",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white'
        )
        st.plotly_chart(fig_time, use_container_width=True)
    
    with tab2:
        # Tabela de listings
        st.subheader("📋 Listings Recentes")
        
        # Ordenação
        sort_by = st.selectbox(
            "Ordenar por:",
            ["collected_at", "price_usd", "float_value", "watchers"],
            format_func=lambda x: {
                "collected_at": "⏰ Mais Recente",
                "price_usd": "💰 Preço",
                "float_value": "🎯 Float",
                "watchers": "👥 Watchers"
            }[x]
        )
        
        sort_order = st.radio("Ordem:", ["Decrescente", "Crescente"], horizontal=True)
        ascending = sort_order == "Crescente"
        
        # Aplicar ordenação
        display_df = filtered_df.sort_values(sort_by, ascending=ascending).head(100)
        
        # Formatação da tabela
        display_df['price_formatted'] = display_df['price_usd'].apply(lambda x: f"${x:.2f}")
        display_df['float_formatted'] = display_df['float_value'].apply(lambda x: f"{x:.4f}")
        display_df['time_ago'] = display_df['collected_at'].apply(
            lambda x: f"{(datetime.now() - x.replace(tzinfo=None)).seconds // 60}min"
        )
        
        # Exibir tabela
        st.dataframe(
            display_df[['market_hash_name', 'price_formatted', 'float_formatted', 'seller_username', 'watchers', 'state', 'time_ago']],
            column_config={
                'market_hash_name': 'Skin',
                'price_formatted': 'Preço',
                'float_formatted': 'Float',
                'seller_username': 'Vendedor',
                'watchers': 'Watchers',
                'state': 'Status',
                'time_ago': 'Tempo'
            },
            use_container_width=True,
            height=400
        )
    
    with tab3:
        # Top skins por diferentes métricas
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💎 Skins Mais Caras")
            top_expensive = filtered_df.nlargest(10, 'price_usd')[['market_hash_name', 'price_usd', 'float_value']]
            top_expensive['price_usd'] = top_expensive['price_usd'].apply(lambda x: f"${x:.2f}")
            st.dataframe(top_expensive, use_container_width=True)
        
        with col2:
            st.subheader("👥 Mais Assistidas")
            top_watched = filtered_df.nlargest(10, 'watchers')[['market_hash_name', 'watchers', 'price_usd']]
            top_watched['price_usd'] = top_watched['price_usd'].apply(lambda x: f"${x:.2f}")
            st.dataframe(top_watched, use_container_width=True)
        
        # Skins mais populares
        st.subheader("🔥 Skins Mais Listadas")
        popular_skins = filtered_df.groupby('market_hash_name').agg({
            'price_usd': ['count', 'mean', 'min', 'max'],
            'watchers': 'sum'
        }).round(2)
        popular_skins.columns = ['Listings', 'Preço Médio', 'Min', 'Max', 'Total Watchers']
        popular_skins = popular_skins.sort_values('Listings', ascending=False).head(15)
        st.dataframe(popular_skins, use_container_width=True)
    
    with tab4:
        # Estatísticas detalhadas
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("📊 Distribuição por Categoria")
            category_dist = filtered_df['category'].value_counts()
            fig_pie = px.pie(
                values=category_dist.values,
                names=category_dist.index,
                title="Distribuição por Categoria"
            )
            fig_pie.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white'
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            st.subheader("🎯 Float Distribution")
            fig_float = px.histogram(
                filtered_df,
                x='float_value',
                nbins=20,
                title="Distribuição de Float Values"
            )
            fig_float.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white'
            )
            st.plotly_chart(fig_float, use_container_width=True)
        
        with col3:
            st.subheader("💹 Price Statistics")
            price_stats = filtered_df['price_usd'].describe()
            for stat, value in price_stats.items():
                st.metric(stat.title(), f"${value:.2f}")

if __name__ == "__main__":
    main()