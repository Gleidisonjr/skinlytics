#!/usr/bin/env python3
"""
🚀 SKINLYTICS - CS2 SKIN TRADING PLATFORM
MVP Dashboard para análise de mercado e oportunidades de trading
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import time

# Imports do nosso sistema
from src.models.optimized_database import get_session, Skin as OptimizedSkin, ListingOptimized, MarketInsights, PriceHistory
from src.services.aggregation_service import AggregationService

# Configuração da página
st.set_page_config(
    page_title="Skinlytics - CS2 Trading Intelligence",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
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

# Cache para melhor performance
@st.cache_data(ttl=300)  # 5 minutos de cache
def load_market_data():
    """Carrega dados do mercado"""
    session = get_session()
    
    try:
        # Estatísticas gerais
        total_listings = session.query(ListingOptimized).count()
        total_skins = session.query(OptimizedSkin).count()
        total_value = session.query(ListingOptimized.price).filter(ListingOptimized.price > 0).all()
        total_value_sum = sum([l[0] for l in total_value if l[0]]) / 100  # Convert to USD
        
        # Últimos listings
        recent_listings = session.query(ListingOptimized, OptimizedSkin).join(OptimizedSkin).order_by(
            ListingOptimized.collected_at.desc()
        ).limit(20).all()
        
        # Top oportunidades
        aggregation_service = AggregationService()
        opportunities = aggregation_service.get_top_opportunities(20)
        
        # Distribuição por raridade
        rarity_dist = session.query(
            OptimizedSkin.rarity, 
            session.query(ListingOptimized).filter(ListingOptimized.skin_id == OptimizedSkin.id).count().label('count')
        ).join(ListingOptimized).group_by(OptimizedSkin.rarity).all()
        
        session.close()
        
        return {
            'stats': {
                'total_listings': total_listings,
                'total_skins': total_skins,
                'total_value': total_value_sum,
                'avg_price': total_value_sum / total_listings if total_listings > 0 else 0
            },
            'recent_listings': recent_listings,
            'opportunities': opportunities,
            'rarity_dist': rarity_dist
        }
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        session.close()
        return None

@st.cache_data(ttl=600)  # 10 minutos de cache
def load_price_trends():
    """Carrega tendências de preços"""
    session = get_session()
    
    try:
        # Top 10 skins por volume
        top_skins = session.query(
            OptimizedSkin.market_hash_name,
            session.query(ListingOptimized.price).filter(
                ListingOptimized.skin_id == OptimizedSkin.id
            ).count().label('volume'),
            session.query(ListingOptimized.price).filter(
                ListingOptimized.skin_id == OptimizedSkin.id,
                ListingOptimized.price > 0
            ).func.avg().label('avg_price')
        ).join(ListingOptimized).group_by(
            OptimizedSkin.id, OptimizedSkin.market_hash_name
        ).order_by('volume desc').limit(10).all()
        
        session.close()
        return top_skins
    except Exception as e:
        st.error(f"Erro ao carregar tendências: {e}")
        session.close()
        return []

def main():
    """Função principal do dashboard"""
    
    # Header
    st.markdown('<h1 class="main-header">🎯 SKINLYTICS</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">CS2 Skin Trading Intelligence Platform</p>', unsafe_allow_html=True)
    
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
    
    # Carregar dados
    with st.spinner("🔄 Carregando dados do mercado..."):
        market_data = load_market_data()
        price_trends = load_price_trends()
    
    if not market_data:
        st.error("❌ Não foi possível carregar os dados. Verifique se o collector está rodando.")
        return
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📦 Total Listings",
            value=f"{market_data['stats']['total_listings']:,}",
            delta="Em tempo real"
        )
    
    with col2:
        st.metric(
            label="🎨 Skins Únicas",
            value=f"{market_data['stats']['total_skins']:,}",
            delta="Crescendo"
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
        
        if market_data['opportunities']:
            # Filtros
            col1, col2, col3 = st.columns(3)
            with col1:
                min_score = st.slider("Score Mínimo", 0, 100, 60)
            with col2:
                max_price = st.slider("Preço Máximo ($)", 0, 1000, 500)
            with col3:
                stattrak_only = st.checkbox("Apenas StatTrak™")
            
            # Filtrar oportunidades
            filtered_ops = [
                op for op in market_data['opportunities']
                if op['opportunity_score'] >= min_score
                and op['current_price'] <= max_price
                and (not stattrak_only or op['is_stattrak'])
            ]
            
            # Mostrar oportunidades
            for i, opp in enumerate(filtered_ops[:10], 1):
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    stattrak_badge = "🔥" if opp['is_stattrak'] else ""
                    undervalued_badge = "💎" if opp['is_undervalued'] else ""
                    st.write(f"**{i}. {opp['skin_name'][:50]}** {stattrak_badge}{undervalued_badge}")
                
                with col2:
                    st.metric("Preço", f"${opp['current_price']:.2f}")
                
                with col3:
                    trend_color = "green" if opp['trend_7d'] > 0 else "red" if opp['trend_7d'] < 0 else "gray"
                    st.markdown(f"<span style='color:{trend_color}'>{opp['trend_7d']:+.1f}%</span>", unsafe_allow_html=True)
                
                with col4:
                    score_color = "green" if opp['opportunity_score'] > 80 else "orange" if opp['opportunity_score'] > 60 else "red"
                    st.markdown(f"<span style='color:{score_color};font-weight:bold'>{opp['opportunity_score']:.0f}</span>", unsafe_allow_html=True)
                
                st.divider()
        else:
            st.info("🔄 Carregando oportunidades... Execute o agregador para calcular scores.")
    
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
                    'Skin': listing.market_hash_name[:40],
                    'Preço': f"${listing_obj.price/100:.2f}",
                    'Float': f"{listing_obj.float_value:.4f}" if listing_obj.float_value else "N/A",
                    'Watchers': listing_obj.watchers or 0,
                    'Coletado': listing_obj.collected_at.strftime("%H:%M:%S")
                }
                for listing_obj, listing in market_data['recent_listings']
            ])
            st.dataframe(recent_df, use_container_width=True)
    
    with tab3:
        st.subheader("📈 Tendências de Preços")
        
        if price_trends:
            trend_df = pd.DataFrame([
                {
                    'Skin': trend[0][:30],
                    'Volume': trend[1],
                    'Preço Médio': f"${trend[2]/100:.2f}" if trend[2] else "$0.00"
                }
                for trend in price_trends
            ])
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig_volume = px.bar(
                    trend_df,
                    x='Volume',
                    y='Skin',
                    orientation='h',
                    title="🔥 Top Skins por Volume",
                    color='Volume',
                    color_continuous_scale='blues'
                )
                fig_volume.update_layout(height=400)
                st.plotly_chart(fig_volume, use_container_width=True)
            
            with col2:
                st.subheader("📊 Detalhes")
                st.dataframe(trend_df, use_container_width=True)
        
        # Simulação de gráfico temporal (para futuras implementações)
        st.subheader("📊 Preços Históricos (Simulação)")
        dates = pd.date_range(start='2025-01-01', end='2025-08-06', freq='D')
        fake_prices = np.random.normal(100, 20, len(dates)).cumsum()
        
        fig_timeline = go.Figure()
        fig_timeline.add_trace(go.Scatter(
            x=dates,
            y=fake_prices,
            mode='lines',
            name='AK-47 | Redline (FT)',
            line=dict(color='#FF6B35', width=2)
        ))
        fig_timeline.update_layout(
            title="📈 Evolução de Preços (Exemplo)",
            xaxis_title="Data",
            yaxis_title="Preço ($)",
            hovermode='x'
        )
        st.plotly_chart(fig_timeline, use_container_width=True)
    
    with tab4:
        st.subheader("🔍 Explorer de Dados")
        
        # Filtros avançados
        col1, col2, col3 = st.columns(3)
        with col1:
            search_term = st.text_input("🔍 Buscar skin", placeholder="Ex: AK-47, AWP...")
        with col2:
            price_range = st.slider("💰 Faixa de preço ($)", 0, 1000, (0, 100))
        with col3:
            float_range = st.slider("🎯 Float range", 0.0, 1.0, (0.0, 1.0))
        
        # Busca em tempo real
        if search_term:
            session = get_session()
            try:
                results = session.query(ListingOptimized, OptimizedSkin).join(OptimizedSkin).filter(
                    OptimizedSkin.market_hash_name.ilike(f'%{search_term}%'),
                    ListingOptimized.price >= price_range[0] * 100,
                    ListingOptimized.price <= price_range[1] * 100
                ).limit(50).all()
                
                if results:
                    results_df = pd.DataFrame([
                        {
                            'Skin': skin.market_hash_name,
                            'Preço': f"${listing.price/100:.2f}",
                            'Float': f"{listing.float_value:.6f}" if listing.float_value else "N/A",
                            'Raridade': skin.rarity,
                            'StatTrak': "🔥" if skin.is_stattrak else "",
                            'Watchers': listing.watchers or 0
                        }
                        for listing, skin in results
                    ])
                    
                    st.dataframe(results_df, use_container_width=True)
                    st.success(f"✅ Encontrados {len(results)} resultados para '{search_term}'")
                else:
                    st.warning(f"❌ Nenhum resultado encontrado para '{search_term}'")
                
                session.close()
            except Exception as e:
                st.error(f"Erro na busca: {e}")
                session.close()
    
    # Footer
    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**🔄 Status:** Coletando dados em tempo real")
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
            "opportunities_count": len(market_data['opportunities']) if market_data else 0,
            "cache_stats": "Active"
        })

if __name__ == "__main__":
    main()