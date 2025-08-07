#!/usr/bin/env python3
"""
Script para configurar tabelas no Railway (roda automaticamente)
"""

import os
import psycopg2
from sqlalchemy import create_engine, text
from datetime import datetime

def setup_railway_database():
    """Configura o banco no Railway automaticamente"""
    print("🔧 Configurando banco Railway...")
    
    # Verificar se estamos no Railway
    if 'RAILWAY_ENVIRONMENT' not in os.environ:
        print("⚠️ Não estamos no Railway - pulando configuração")
        return True
    
    # Verificar se DATABASE_URL está configurada
    if 'DATABASE_URL' not in os.environ:
        print("❌ DATABASE_URL não encontrada no Railway")
        return False
    
    try:
        # Conectar com o banco
        engine = create_engine(os.environ['DATABASE_URL'])
        
        with engine.connect() as conn:
            print("✅ Conectado com PostgreSQL Railway")
            
            # Criar tabela skins_optimized
            print("📊 Criando tabela skins_optimized...")
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
            print("📊 Criando tabela listings_optimized...")
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
            print("📊 Criando tabela price_history...")
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
            print("📊 Criando tabela market_insights...")
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
            
            # Commit das mudanças
            conn.commit()
            print("✅ Tabelas criadas com sucesso!")
            
            # Verificar tabelas criadas
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            print(f"📊 Tabelas disponíveis: {tables}")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        return False

if __name__ == "__main__":
    print("🚀 CONFIGURAÇÃO AUTOMÁTICA DO RAILWAY")
    print("="*50)
    
    success = setup_railway_database()
    
    if success:
        print("\n🎉 Banco configurado com sucesso!")
        print("💡 Dashboard pronto para uso!")
    else:
        print("\n❌ Erro na configuração")
        print("💡 Verifique os logs do Railway")
