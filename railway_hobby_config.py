#!/usr/bin/env python3
"""
Configurações otimizadas para Railway Hobby Plan ($5)
Aproveita 1GB RAM e 2 vCPUs para máxima performance
"""

import os
import streamlit as st

# Configurações otimizadas para Railway Hobby Plan
RAILWAY_HOBBY_CONFIG = {
    "max_memory_mb": 900,  # Usar quase toda a RAM disponível
    "db_pool_size": 10,    # Mais conexões simultâneas
    "cache_ttl": 180,      # Cache mais longo
    "max_rows_display": 5000,  # Mais dados na tela
    "auto_refresh_interval": 30,  # Refresh mais frequente
    "concurrent_requests": 4,     # Mais requests simultâneos
}

def optimize_for_railway_hobby():
    """Aplica otimizações específicas para Railway Hobby Plan"""
    
    # Configurar Streamlit para alta performance
    st.set_page_config(
        page_title="Skinlytics - CS2 Trading Intelligence",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded",  # Full experience
        menu_items={
            'Get Help': 'https://github.com/Gleidisonjr/skinlytics',
            'Report a bug': 'https://github.com/Gleidisonjr/skinlytics/issues',
            'About': """
            # Skinlytics CS2 Trading Platform
            
            🎯 **Professional CS2 Skin Trading Intelligence**
            
            - Real-time market analysis
            - Advanced trading opportunities
            - Professional-grade infrastructure
            
            Powered by Railway Hobby Plan ($5/month)
            """
        }
    )
    
    # Configurar para alta performance
    if 'RAILWAY_ENVIRONMENT' in os.environ:
        os.environ['STREAMLIT_SERVER_MAX_UPLOAD_SIZE'] = '200'
        os.environ['STREAMLIT_SERVER_MAX_MESSAGE_SIZE'] = '200'
        os.environ['STREAMLIT_SERVER_ENABLE_CORS'] = 'false'
        os.environ['STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION'] = 'false'
    
    return RAILWAY_HOBBY_CONFIG

def get_optimized_db_connection_hobby():
    """Connection string otimizada para Railway Hobby Plan"""
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        # Fallback para desenvolvimento local
        return "postgresql://skinlytics_user:skinlytics_pass_2025@localhost:5432/skinlytics"
    
    # Adicionar parâmetros de alta performance para Railway Hobby
    if '?' not in database_url:
        database_url += '?'
    else:
        database_url += '&'
    
    # Otimizações para Railway Hobby Plan
    optimizations = [
        'pool_size=10',           # Mais conexões
        'max_overflow=5',         # Overflow permitido
        'pool_timeout=60',        # Timeout maior
        'pool_recycle=3600',      # Recycle menos frequente
        'pool_pre_ping=true',     # Health check
        'sslmode=require',
        'application_name=skinlytics_hobby'
    ]
    
    return database_url + '&'.join(optimizations)

def get_performance_stats():
    """Monitor de performance para Railway Hobby Plan"""
    try:
        import psutil
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        cpu_percent = process.cpu_percent()
        
        return {
            'memory_used_mb': round(memory_mb, 1),
            'memory_limit_mb': RAILWAY_HOBBY_CONFIG['max_memory_mb'],
            'memory_percent': round((memory_mb / RAILWAY_HOBBY_CONFIG['max_memory_mb']) * 100, 1),
            'cpu_percent': round(cpu_percent, 1),
            'db_pool_size': RAILWAY_HOBBY_CONFIG['db_pool_size'],
            'plan': 'Hobby ($5/month)'
        }
    except ImportError:
        return {
            'memory_used_mb': 0, 
            'memory_limit_mb': 900, 
            'memory_percent': 0,
            'cpu_percent': 0,
            'db_pool_size': 10,
            'plan': 'Hobby ($5/month)'
        }

# Configuração de cache avançada para Hobby Plan
ADVANCED_CACHE_CONFIG = {
    'ttl': 180,  # 3 minutos
    'max_entries': 1000,  # Mais entradas em cache
    'persist': True,  # Persistir cache
    'allow_output_mutation': True,  # Performance boost
}

# Configuração de logging otimizada para produção
PRODUCTION_LOGGING_CONFIG = {
    'level': 'INFO',  # Mais detalhado que free
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'detailed',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': '/tmp/skinlytics.log',
            'formatter': 'detailed',
        }
    }
}

if __name__ == "__main__":
    print("🚂 Railway Hobby Plan Configuration ($5/month)")
    print("=" * 50)
    print(f"Max Memory: {RAILWAY_HOBBY_CONFIG['max_memory_mb']} MB")
    print(f"DB Pool Size: {RAILWAY_HOBBY_CONFIG['db_pool_size']}")
    print(f"Cache TTL: {RAILWAY_HOBBY_CONFIG['cache_ttl']} seconds")
    print(f"Auto Refresh: {RAILWAY_HOBBY_CONFIG['auto_refresh_interval']} seconds")
    print(f"Max Rows Display: {RAILWAY_HOBBY_CONFIG['max_rows_display']}")
    print(f"Concurrent Requests: {RAILWAY_HOBBY_CONFIG['concurrent_requests']}")
    print("🔥 Configuração HIGH-PERFORMANCE ativada!")