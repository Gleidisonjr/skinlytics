#!/usr/bin/env python3
"""
🚀 SKINLYTICS - CS2 SKIN TRADING PLATFORM
Versão simplificada para teste inicial
"""

import os
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

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
</style>
""", unsafe_allow_html=True)

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
    
    # Dados simulados para teste
    st.subheader("📊 Dados de Teste")
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📦 Total Listings",
            value="1,234",
            delta="+12"
        )
    
    with col2:
        st.metric(
            label="🎨 Skins Únicas",
            value="567",
            delta="+5"
        )
    
    with col3:
        st.metric(
            label="💰 Valor Total",
            value="$45,678.90",
            delta="+$1,234"
        )
    
    with col4:
        st.metric(
            label="📊 Preço Médio",
            value="$37.05",
            delta="-$2.15"
        )
    
    # Tabs principais
    tab1, tab2, tab3, tab4 = st.tabs(["🎯 Oportunidades", "📊 Mercado", "📈 Tendências", "🔍 Explorer"])
    
    with tab1:
        st.subheader("🏆 Top Oportunidades de Trading")
        
        # Dados simulados
        opportunities = [
            {"skin": "AK-47 | Redline (FT)", "price": 45.50, "score": 85, "trend": 12.5},
            {"skin": "AWP | Asiimov (WW)", "price": 89.99, "score": 78, "trend": -5.2},
            {"skin": "M4A4 | Howl (FN)", "price": 1250.00, "score": 92, "trend": 8.7},
            {"skin": "Karambit | Fade (FN)", "price": 890.00, "score": 88, "trend": 15.3},
        ]
        
        for i, opp in enumerate(opportunities, 1):
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                st.write(f"**{i}. {opp['skin']}**")
            
            with col2:
                st.metric("Preço", f"${opp['price']:.2f}")
            
            with col3:
                trend_color = "green" if opp['trend'] > 0 else "red"
                st.markdown(f"<span style='color:{trend_color}'>{opp['trend']:+.1f}%</span>", unsafe_allow_html=True)
            
            with col4:
                score_color = "green" if opp['score'] > 80 else "orange"
                st.markdown(f"<span style='color:{score_color};font-weight:bold'>{opp['score']}</span>", unsafe_allow_html=True)
            
            st.divider()
    
    with tab2:
        st.subheader("📊 Visão Geral do Mercado")
        
        # Dados simulados para gráficos
        rarity_data = {
            'Raridade': ['Consumer', 'Industrial', 'Mil-Spec', 'Restricted', 'Classified', 'Covert'],
            'Quantidade': [150, 120, 80, 60, 40, 25]
        }
        
        df = pd.DataFrame(rarity_data)
        st.dataframe(df, use_container_width=True)
        
        # Gráfico simples com st.bar_chart
        st.subheader("📈 Distribuição por Raridade")
        chart_data = pd.DataFrame(rarity_data)
        st.bar_chart(chart_data.set_index('Raridade'))
    
    with tab3:
        st.subheader("📈 Tendências de Preços")
        
        # Dados simulados de tendências
        trend_data = {
            'Skin': ['AK-47 | Redline', 'AWP | Asiimov', 'M4A4 | Howl', 'Karambit | Fade'],
            'Volume': [1250, 890, 340, 156],
            'Preço Médio': [45.50, 89.99, 1250.00, 890.00]
        }
        
        trend_df = pd.DataFrame(trend_data)
        st.dataframe(trend_df, use_container_width=True)
        
        # Gráfico de linha simples
        st.subheader("📊 Evolução de Preços (Simulação)")
        dates = pd.date_range(start='2025-01-01', end='2025-08-06', freq='D')
        prices = np.random.normal(100, 20, len(dates)).cumsum()
        
        price_df = pd.DataFrame({
            'Data': dates,
            'Preço': prices
        })
        
        st.line_chart(price_df.set_index('Data'))
    
    with tab4:
        st.subheader("🔍 Explorer de Dados")
        
        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            search_term = st.text_input("🔍 Buscar skin", placeholder="Ex: AK-47, AWP...")
        with col2:
            price_range = st.slider("💰 Faixa de preço ($)", 0, 1000, (0, 100))
        
        if search_term:
            st.info(f"🔍 Buscando por: {search_term}")
            st.success("✅ Funcionalidade de busca será implementada com dados reais")
        else:
            st.info("🔍 Digite um termo para buscar skins")
    
    # Footer
    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**🔄 Status:** Modo de teste")
    with col2:
        st.markdown(f"**⏰ Última atualização:** {datetime.now().strftime('%H:%M:%S')}")
    with col3:
        if st.button("🔄 Atualizar dados"):
            st.rerun()
    
    # Debug info
    if show_debug:
        st.subheader("🐛 Debug Info")
        st.json({
            "timestamp": datetime.now().isoformat(),
            "mode": "test",
            "plotly_available": False,
            "version": "1.0.0-simple"
        })

if __name__ == "__main__":
    main()
