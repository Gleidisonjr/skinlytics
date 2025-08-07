#!/usr/bin/env python3
"""
Script para criar tabelas no PostgreSQL Railway
"""

import os
import psycopg2
from sqlalchemy import create_engine, text
from datetime import datetime

def create_railway_tables():
    """Cria as tabelas no PostgreSQL Railway"""
    print("🔧 Criando tabelas no PostgreSQL Railway...")
    
    # Verificar se DATABASE_URL está configurada
    if 'DATABASE_URL' not in os.environ:
        print("❌ DATABASE_URL não encontrada")
        print("💡 Configure a variável DATABASE_URL no Railway")
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

def insert_sample_data():
    """Insere dados de exemplo"""
    print("\n📊 Inserindo dados de exemplo...")
    
    try:
        engine = create_engine(os.environ['DATABASE_URL'])
        
        with engine.connect() as conn:
            # Inserir skins de exemplo
            skins_data = [
                ("AK-47 | Redline (FT)", 3, False),
                ("AWP | Asiimov (WW)", 4, False),
                ("M4A4 | Howl (FN)", 5, True),
                ("Karambit | Fade (FN)", 6, False),
                ("USP-S | Kill Confirmed (FN)", 4, True)
            ]
            
            for skin_name, rarity, is_stattrak in skins_data:
                conn.execute(text("""
                    INSERT INTO skins_optimized (market_hash_name, rarity, is_stattrak)
                    VALUES (:name, :rarity, :stattrak)
                    ON CONFLICT DO NOTHING
                """), {
                    'name': skin_name,
                    'rarity': rarity,
                    'stattrak': is_stattrak
                })
            
            # Inserir listings de exemplo
            listings_data = [
                (1, 4550, 0.15, 5),  # AK-47 Redline
                (2, 8999, 0.42, 3),  # AWP Asiimov
                (3, 125000, 0.01, 12),  # M4A4 Howl
                (4, 89000, 0.03, 8),  # Karambit Fade
                (5, 12500, 0.05, 2)   # USP-S Kill Confirmed
            ]
            
            for skin_id, price, float_val, watchers in listings_data:
                conn.execute(text("""
                    INSERT INTO listings_optimized (skin_id, price, float_value, watchers)
                    VALUES (:skin_id, :price, :float_val, :watchers)
                """), {
                    'skin_id': skin_id,
                    'price': price,
                    'float_val': float_val,
                    'watchers': watchers
                })
            
            # Inserir histórico de preços
            from datetime import timedelta
            for i in range(30):
                date = datetime.now() - timedelta(days=i)
                conn.execute(text("""
                    INSERT INTO price_history (skin_id, price, date, volume)
                    VALUES (1, :price, :date, :volume)
                    ON CONFLICT DO NOTHING
                """), {
                    'price': 4550 + (i * 10),
                    'date': date.date(),
                    'volume': 100 + i
                })
            
            conn.commit()
            print("✅ Dados de exemplo inseridos!")
            
    except Exception as e:
        print(f"❌ Erro ao inserir dados: {e}")

if __name__ == "__main__":
    print("🚀 CRIANDO TABELAS NO RAILWAY POSTGRESQL")
    print("="*50)
    
    success = create_railway_tables()
    
    if success:
        print("\n🎉 Tabelas criadas com sucesso!")
        print("💡 Agora o dashboard deve funcionar")
        
        # Perguntar se quer inserir dados de exemplo
        response = input("\n❓ Inserir dados de exemplo? (s/n): ")
        if response.lower() in ['s', 'sim', 'y', 'yes']:
            insert_sample_data()
            print("\n✅ Dashboard pronto para uso!")
            print("🌐 Acesse: https://skinlytics-production.up.railway.app")
    else:
        print("\n❌ Erro ao criar tabelas")
        print("💡 Verifique a configuração do Railway")
