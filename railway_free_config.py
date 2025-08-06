#!/usr/bin/env python3
"""
Configurações otimizadas para Railway Free Plan
Ajusta recursos para máxima eficiência em 512MB RAM
"""

import os
import streamlit as st

# Configurações de memória otimizadas para Railway Free
RAILWAY_FREE_CONFIG = {
    "max_memory_mb": 400,  # Deixar 100MB de buffer
    "db_pool_size": 3,     # Menos conexões DB
    "cache_ttl": 300,      # Cache mais agressivo
    "max_rows_display": 1000,  # Limitar dados exibidos
    "auto_refresh_interval": 60,  # Refresh menos frequente
}

def optimize_for_railway_free():
    """Aplica otimizações específicas para Railway Free"""
    
    # Configurar Streamlit para menor uso de memória
    st.set_page_config(
        page_title="Skinlytics",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="collapsed",  # Economizar memória
        menu_items={
            'Get Help': None,
            'Report a bug': None,
            'About': "Skinlytics MVP - CS2 Trading Intelligence"
        }
    )
    
    # Configurar cache mais agressivo
    if 'RAILWAY_ENVIRONMENT' in os.environ:
        os.environ['STREAMLIT_SERVER_MAX_UPLOAD_SIZE'] = '50'
        os.environ['STREAMLIT_SERVER_MAX_MESSAGE_SIZE'] = '50'
    
    return RAILWAY_FREE_CONFIG

def get_optimized_db_connection():
    """Connection string otimizada para Railway Free"""
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        # Fallback para desenvolvimento local
        return "postgresql://skinlytics_user:skinlytics_pass_2025@localhost:5432/skinlytics"
    
    # Adicionar parâmetros de otimização para Railway
    if '?' not in database_url:
        database_url += '?'
    else:
        database_url += '&'
    
    # Otimizações para Railway Free
    optimizations = [
        'pool_size=3',
        'max_overflow=0',
        'pool_timeout=30',
        'pool_recycle=1800',
        'sslmode=require'
    ]
    
    return database_url + '&'.join(optimizations)

def get_memory_usage():
    """Monitor de uso de memória para Railway Free"""
    try:
        import psutil
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        return {
            'memory_used_mb': round(memory_mb, 1),
            'memory_limit_mb': RAILWAY_FREE_CONFIG['max_memory_mb'],
            'memory_percent': round((memory_mb / RAILWAY_FREE_CONFIG['max_memory_mb']) * 100, 1)
        }
    except ImportError:
        return {'memory_used_mb': 0, 'memory_limit_mb': 400, 'memory_percent': 0}

# Configuração de logging otimizada
LOGGING_CONFIG = {
    'level': 'WARNING',  # Menos logs = menos I/O
    'disable_existing_loggers': True,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        }
    },
    'formatters': {
        'simple': {
            'format': '%(levelname)s: %(message)s'
        }
    }
}

if __name__ == "__main__":
    print("🚂 Railway Free Plan Configuration")
    print("=" * 40)
    print(f"Max Memory: {RAILWAY_FREE_CONFIG['max_memory_mb']} MB")
    print(f"DB Pool Size: {RAILWAY_FREE_CONFIG['db_pool_size']}")
    print(f"Cache TTL: {RAILWAY_FREE_CONFIG['cache_ttl']} seconds")
    print(f"Auto Refresh: {RAILWAY_FREE_CONFIG['auto_refresh_interval']} seconds")
    print("✅ Configuração otimizada para Railway Free!")