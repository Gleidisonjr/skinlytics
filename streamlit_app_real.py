#!/usr/bin/env python3
"""
🚀 SKINLYTICS - CS2 SKIN TRADING PLATFORM
Dashboard com dados reais do PostgreSQL
"""

import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import time
import psycopg2
from sqlalchemy import create_engine, text
import json

# Configuração da página
st.set_page_config(
    page_title="Skinlytics - CS2 Trading Intelligence",
    page_icon="🎯",
    layout="wide"
)

# CSS customizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #FF6B35;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .opportunity-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1.1rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Configuração do banco de dados
def get_db_connection():
    """Conecta com o PostgreSQL"""
    try:
        # Railway PostgreSQL
        if 'DATABASE_URL' in os.environ:
            return create_engine(os.environ['DATABASE_URL'])
        
        # Local PostgreSQL
        elif 'POSTGRES_HOST' in os.environ:
            db_url = f"postgresql://{os.environ.get('POSTGRES_USER', 'postgres')}:{os.environ.get('POSTGRES_PASSWORD', 'password')}@{os.environ.get('POSTGRES_HOST', 'localhost')}:{os.environ.get('POSTGRES_PORT', '5432')}/{os.environ.get('POSTGRES_DB', 'skinlytics')}"
            return create_engine(db_url)
        
        # Fallback para SQLite local
        else:
            return create_engine('sqlite:///data/skins_saas.db')
            
    except Exception as e:
        st.error(f"Erro ao conectar com banco: {e}")
        return None

def create_tables_if_not_exist():
    """Cria as tabelas se não existirem"""
    engine = get_db_connection()
    if not engine:
        return False
    
    try:
        with engine.connect() as conn:
            # Criar tabela skins_optimized
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS skins_optimized (
                    id SERIAL PRIMARY KEY,
                    market_hash_name VARCHAR(255) NOT NULL,
                    rarity INTEGER DEFAULT 0,
                    is_stattrak BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Criar tabela listings_optimized
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS listings_optimized (
                    id SERIAL PRIMARY KEY,
                    skin_id INTEGER REFERENCES skins_optimized(id),
                    price INTEGER NOT NULL,
                    float_value DECIMAL(10,8),
                    watchers INTEGER DEFAULT 0,
                    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Criar tabela price_history
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS price_history (
                    id SERIAL PRIMARY KEY,
                    skin_id INTEGER REFERENCES skins_optimized(id),
                    price INTEGER NOT NULL,
                    date DATE NOT NULL,
                    volume INTEGER DEFAULT 1,
                    UNIQUE(skin_id, date)
                )
            """))
            
            # Criar tabela market_insights
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS market_insights (
                    id SERIAL PRIMARY KEY,
                    date DATE NOT NULL,
                    total_listings INTEGER DEFAULT 0,
                    total_value DECIMAL(15,2) DEFAULT 0,
                    avg_price DECIMAL(10,2) DEFAULT 0,
                    volatility_index DECIMAL(5,2) DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date)
                )
            """))
            
            conn.commit()
            return True
            
    except Exception as e:
        st.error(f"Erro ao criar tabelas: {e}")
        return False

# Criar tabelas automaticamente
if 'RAILWAY_ENVIRONMENT' in os.environ:
    create_tables_if_not_exist()

@st.cache_data(ttl=300)  # 5 minutos de cache
def load_real_market_data():
    """Carrega dados reais do mercado"""
    engine = get_db_connection()
    if not engine:
        return None
    
    try:
        with engine.connect() as conn:
            # Estatísticas gerais
            result = conn.execute(text("SELECT COUNT(*) as total FROM listings_optimized"))
            total_listings = result.fetchone()[0]
            
            result = conn.execute(text("SELECT COUNT(*) as total FROM skins_optimized"))
            total_skins = result.fetchone()[0]
            
            result = conn.execute(text("SELECT SUM(price) as total_value FROM listings_optimized WHERE price > 0"))
            total_value_result = result.fetchone()[0]
            total_value = total_value_result / 100 if total_value_result else 0  # Convert to USD
            
            result = conn.execute(text("SELECT AVG(price) as avg_price FROM listings_optimized WHERE price > 0"))
            avg_price_result = result.fetchone()[0]
            avg_price = avg_price_result / 100 if avg_price_result else 0
            
            # Últimos listings
            result = conn.execute(text("""
                SELECT l.id, l.price, l.float_value, l.watchers, l.collected_at, s.market_hash_name, s.rarity
                FROM listings_optimized l
                JOIN skins_optimized s ON l.skin_id = s.id
                ORDER BY l.collected_at DESC
                LIMIT 20
            """))
            recent_listings = result.fetchall()
            
            # Distribuição por raridade
            result = conn.execute(text("""
                SELECT s.rarity, COUNT(l.id) as count
                FROM skins_optimized s
                JOIN listings_optimized l ON s.id = l.skin_id
                GROUP BY s.rarity
                ORDER BY count DESC
            """))
            rarity_dist = result.fetchall()
            
            # Top skins por volume
            result = conn.execute(text("""
                SELECT s.market_hash_name, COUNT(l.id) as volume, AVG(l.price) as avg_price
                FROM skins_optimized s
                JOIN listings_optimized l ON s.id = l.skin_id
                WHERE l.price > 0
                GROUP BY s.id, s.market_hash_name
                ORDER BY volume DESC
                LIMIT 10
            """))
            top_skins = result.fetchall()
            
        return {
            'stats': {
                'total_listings': total_listings,
                'total_skins': total_skins,
                'total_value': total_value,
                'avg_price': avg_price
            },
            'recent_listings': recent_listings,
            'rarity_dist': rarity_dist,
            'top_skins': top_skins
        }
        
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None

@st.cache_data(ttl=600)  # 10 minutos de cache
def load_price_history():
    """Carrega histórico de preços"""
    engine = get_db_connection()
    if not engine:
        return None
    
    try:
        with engine.connect() as conn:
            # Últimos 30 dias de preços
            result = conn.execute(text("""
                SELECT date, AVG(price) as avg_price, COUNT(*) as volume
                FROM price_history
                WHERE date >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY date
                ORDER BY date
            """))
            price_history = result.fetchall()
            
        return price_history
        
    except Exception as e:
        st.error(f"Erro ao carregar histórico: {e}")
        return None

def show_database_status():
    """Mostra status da conexão com o banco"""
    engine = get_db_connection()
    if engine:
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM listings_optimized"))
                count = result.fetchone()[0]
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.success(f"✅ Banco conectado")
                with col2:
                    st.info(f"📊 {count:,} listings")
                with col3:
                    st.info(f"🕐 {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            st.error(f"❌ Erro no banco: {e}")
    else:
        st.warning("⚠️ Banco não conectado")

def main():
    """Função principal do dashboard"""
    
    # Header
    st.markdown('<h1 class="main-header">🎯 SKINLYTICS</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">CS2 Skin Trading Intelligence Platform</p>', unsafe_allow_html=True)
    
    # Status do banco
    show_database_status()
    
    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/200x100/FF6B35/FFFFFF?text=SKINLYTICS", width=200)
        st.markdown("### 🚀 Features")
        st.markdown("- 📊 Dados em tempo real")
        st.markdown("- 🎯 Oportunidades de trading")
        st.markdown("- 📈 Análise de tendências")
        st.markdown("- 🔍 Filtros avançados")
        
        st.markdown("### ⚙️ Configurações")
        auto_refresh = st.checkbox("Auto-refresh (30s)", value=False)
        show_debug = st.checkbox("Mostrar debug", value=False)
        
        if auto_refresh:
            time.sleep(30)
            st.rerun()
    
    # Carregar dados reais
    with st.spinner("🔄 Carregando dados reais do mercado..."):
        market_data = load_real_market_data()
        price_history = load_price_history()
    
    if not market_data:
        st.error("❌ Não foi possível carregar os dados. Verifique se o collector está rodando.")
        return
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📦 Total Listings",
            value=f"{market_data['stats']['total_listings']:,}",
            delta="Dados reais"
        )
    
    with col2:
        st.metric(
            label="🎨 Skins Únicas",
            value=f"{market_data['stats']['total_skins']:,}",
            delta="CSFloat"
        )
    
    with col3:
        st.metric(
            label="💰 Valor Total",
            value=f"${market_data['stats']['total_value']:,.2f}",
            delta="USD"
        )
    
    with col4:
        st.metric(
            label="📊 Preço Médio",
            value=f"${market_data['stats']['avg_price']:.2f}",
            delta="Por item"
        )
    
    # Tabs principais
    tab1, tab2, tab3, tab4 = st.tabs(["🎯 Oportunidades", "📊 Mercado", "📈 Tendências", "🔍 Explorer"])
    
    with tab1:
        st.subheader("🏆 Top Oportunidades de Trading")
        
        if market_data['top_skins']:
            # Criar DataFrame para análise
            df = pd.DataFrame(market_data['top_skins'], 
                            columns=['skin_name', 'volume', 'avg_price'])
            df['avg_price_usd'] = df['avg_price'] / 100
            
            # Calcular scores simples
            df['score'] = (df['volume'] * df['avg_price_usd']).rank(ascending=False)
            
            # Mostrar top oportunidades
            for i, row in df.head(10).iterrows():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    st.write(f"**{i+1}. {row['skin_name'][:50]}**")
                
                with col2:
                    st.metric("Preço", f"${row['avg_price_usd']:.2f}")
                
                with col3:
                    st.metric("Volume", f"{row['volume']}")
                
                with col4:
                    score_color = "green" if row['score'] <= 3 else "orange"
                    st.markdown(f"<span style='color:{score_color};font-weight:bold'>{row['score']:.0f}</span>", unsafe_allow_html=True)
                
                st.divider()
        else:
            st.info("🔄 Carregando oportunidades... Execute o collector para obter dados.")
    
    with tab2:
        st.subheader("📊 Visão Geral do Mercado")
        
        # Gráfico de distribuição por raridade
        if market_data['rarity_dist']:
            rarity_names = {0: "Consumer", 1: "Industrial", 2: "Mil-Spec", 3: "Restricted", 
                          4: "Classified", 5: "Covert", 6: "Contraband", 7: "★ Knife"}
            
            rarity_df = pd.DataFrame([
                {'Raridade': rarity_names.get(r[0], f"Rarity {r[0]}"), 'Quantidade': r[1]}
                for r in market_data['rarity_dist']
            ])
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig_pie = px.pie(
                    rarity_df, 
                    values='Quantidade', 
                    names='Raridade',
                    title="📊 Distribuição por Raridade",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                fig_bar = px.bar(
                    rarity_df,
                    x='Raridade',
                    y='Quantidade',
                    title="📈 Quantidade por Raridade",
                    color='Quantidade',
                    color_continuous_scale='viridis'
                )
                st.plotly_chart(fig_bar, use_container_width=True)
        
        # Últimos listings
        st.subheader("⏰ Últimos Listings")
        if market_data['recent_listings']:
            recent_df = pd.DataFrame([
                {
                    'Skin': listing[5][:40],
                    'Preço': f"${listing[1]/100:.2f}",
                    'Float': f"{listing[2]:.4f}" if listing[2] else "N/A",
                    'Watchers': listing[3] or 0,
                    'Coletado': listing[4].strftime("%H:%M:%S") if listing[4] else "N/A"
                }
                for listing in market_data['recent_listings']
            ])
            st.dataframe(recent_df, use_container_width=True)
    
    with tab3:
        st.subheader("📈 Tendências de Preços")
        
        if price_history:
            # Criar gráfico de preços
            price_df = pd.DataFrame(price_history, columns=['date', 'avg_price', 'volume'])
            price_df['avg_price_usd'] = price_df['avg_price'] / 100
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=price_df['date'],
                y=price_df['avg_price_usd'],
                mode='lines+markers',
                name='Preço Médio',
                line=dict(color='#FF6B35', width=2)
            ))
            fig.update_layout(
                title="📈 Evolução de Preços (Últimos 30 dias)",
                xaxis_title="Data",
                yaxis_title="Preço Médio ($)",
                hovermode='x'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Estatísticas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Preço Atual", f"${price_df['avg_price_usd'].iloc[-1]:.2f}")
            with col2:
                st.metric("Volume Total", f"{price_df['volume'].sum():,}")
            with col3:
                change = ((price_df['avg_price_usd'].iloc[-1] - price_df['avg_price_usd'].iloc[0]) / price_df['avg_price_usd'].iloc[0]) * 100
                st.metric("Variação 30d", f"{change:+.1f}%")
        else:
            st.info("📊 Histórico de preços será disponível após coleta de dados")
    
    with tab4:
        st.subheader("🔍 Explorer de Dados")
        
        # Filtros avançados
        col1, col2, col3 = st.columns(3)
        with col1:
            search_term = st.text_input("🔍 Buscar skin", placeholder="Ex: AK-47, AWP...")
        with col2:
            price_range = st.slider("💰 Faixa de preço ($)", 0, 1000, (0, 100))
        with col3:
            rarity_filter = st.selectbox("🎨 Raridade", ["Todas", "Consumer", "Industrial", "Mil-Spec", "Restricted", "Classified", "Covert"])
        
        # Busca em tempo real
        if search_term:
            engine = get_db_connection()
            if engine:
                try:
                    with engine.connect() as conn:
                        query = """
                            SELECT s.market_hash_name, l.price, l.float_value, s.rarity, l.watchers
                            FROM skins_optimized s
                            JOIN listings_optimized l ON s.id = l.skin_id
                            WHERE s.market_hash_name ILIKE :search
                            AND l.price >= :min_price AND l.price <= :max_price
                            ORDER BY l.price DESC
                            LIMIT 50
                        """
                        result = conn.execute(text(query), {
                            'search': f'%{search_term}%',
                            'min_price': price_range[0] * 100,
                            'max_price': price_range[1] * 100
                        })
                        results = result.fetchall()
                        
                        if results:
                            results_df = pd.DataFrame([
                                {
                                    'Skin': row[0],
                                    'Preço': f"${row[1]/100:.2f}",
                                    'Float': f"{row[2]:.6f}" if row[2] else "N/A",
                                    'Raridade': row[3],
                                    'Watchers': row[4] or 0
                                }
                                for row in results
                            ])
                            
                            st.dataframe(results_df, use_container_width=True)
                            st.success(f"✅ Encontrados {len(results)} resultados para '{search_term}'")
                        else:
                            st.warning(f"❌ Nenhum resultado encontrado para '{search_term}'")
                            
                except Exception as e:
                    st.error(f"Erro na busca: {e}")
    
    # Footer
    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**🔄 Status:** Dados reais do CSFloat")
    with col2:
        st.markdown(f"**⏰ Última atualização:** {datetime.now().strftime('%H:%M:%S')}")
    with col3:
        if st.button("🔄 Atualizar dados"):
            st.cache_data.clear()
            st.rerun()
    
    # Debug info
    if show_debug:
        st.subheader("🐛 Debug Info")
        st.json({
            "timestamp": datetime.now().isoformat(),
            "data_loaded": market_data is not None,
            "price_history_loaded": price_history is not None,
            "database_connected": get_db_connection() is not None,
            "cache_stats": "Active"
        })

if __name__ == "__main__":
    main()
