#!/usr/bin/env python3
"""
🚀 POPULATE RAILWAY - Popula banco PostgreSQL com dados de exemplo
"""

import os
import random
import time
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_tables_if_not_exist(engine):
    """Cria tabelas se não existirem"""
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
            logger.info("✅ Tabelas criadas/verificadas")
            
    except Exception as e:
        logger.error(f"❌ Erro ao criar tabelas: {e}")

def populate_railway_database():
    """Popula o banco Railway com dados de exemplo"""
    logger.info("🚀 POPULANDO BANCO RAILWAY")
    
    # Verificar se DATABASE_URL está configurada
    if 'DATABASE_URL' not in os.environ:
        logger.error("❌ DATABASE_URL não encontrada")
        logger.info("💡 Configure a variável DATABASE_URL no Railway")
        return False
    
    try:
        # Conectar com o banco
        engine = create_engine(os.environ['DATABASE_URL'])
        
        # Criar tabelas se necessário
        create_tables_if_not_exist(engine)
        
        # Dados de exemplo
        sample_skins = [
            ("AK-47 | Redline (FT)", 3, False),
            ("AWP | Asiimov (WW)", 4, False),
            ("M4A4 | Howl (FN)", 5, True),
            ("Karambit | Fade (FN)", 6, False),
            ("USP-S | Kill Confirmed (FN)", 4, True),
            ("Desert Eagle | Golden Koi (FN)", 4, False),
            ("M4A1-S | Hyper Beast (MW)", 3, True),
            ("Glock-18 | Water Elemental (FT)", 2, False),
            ("P250 | Asiimov (WW)", 3, False),
            ("Tec-9 | Nuclear Threat (MW)", 4, True),
            ("FAMAS | Pulse (FN)", 2, False),
            ("Galil AR | Cerberus (MW)", 3, True),
            ("SSG 08 | Blood in the Water (MW)", 3, False),
            ("AUG | Chameleon (FN)", 4, False),
            ("SG 553 | Cyrex (FT)", 3, True),
            ("MAC-10 | Heat (WW)", 2, False),
            ("MP9 | Hot Rod (FN)", 3, True),
            ("UMP-45 | Grand Prix (MW)", 2, False),
            ("P90 | Asiimov (FT)", 3, False),
            ("PP-Bizon | Antique (WW)", 2, True)
        ]
        
        with engine.connect() as conn:
            logger.info("📊 Inserindo skins...")
            
            # Inserir skins
            skin_ids = []
            for skin_name, rarity, is_stattrak in sample_skins:
                result = conn.execute(text("""
                    INSERT INTO skins_optimized (market_hash_name, rarity, is_stattrak)
                    VALUES (:name, :rarity, :stattrak)
                    ON CONFLICT DO NOTHING
                    RETURNING id
                """), {
                    'name': skin_name,
                    'rarity': rarity,
                    'stattrak': is_stattrak
                })
                
                skin_id = result.fetchone()
                if skin_id:
                    skin_ids.append(skin_id[0])
                else:
                    # Buscar skin existente
                    result = conn.execute(text("""
                        SELECT id FROM skins_optimized WHERE market_hash_name = :name
                    """), {'name': skin_name})
                    skin_ids.append(result.fetchone()[0])
            
            logger.info(f"✅ {len(skin_ids)} skins inseridas")
            
            # Inserir listings
            logger.info("📦 Inserindo listings...")
            num_listings = 200
            
            for i in range(num_listings):
                skin_id = random.choice(skin_ids)
                price = random.randint(1000, 500000)  # $10 - $5000
                float_value = round(random.uniform(0.01, 0.99), 8)
                watchers = random.randint(0, 50)
                
                conn.execute(text("""
                    INSERT INTO listings_optimized (skin_id, price, float_value, watchers)
                    VALUES (:skin_id, :price, :float_value, :watchers)
                """), {
                    'skin_id': skin_id,
                    'price': price,
                    'float_value': float_value,
                    'watchers': watchers
                })
                
                if (i + 1) % 50 == 0:
                    logger.info(f"📦 Inseridos {i + 1}/{num_listings} listings")
            
            # Inserir histórico de preços
            logger.info("📈 Inserindo histórico de preços...")
            for skin_id in skin_ids:
                for days_ago in range(30):
                    date = datetime.now() - timedelta(days=days_ago)
                    base_price = random.randint(1000, 500000)
                    price_variation = random.uniform(0.8, 1.2)
                    price = int(base_price * price_variation)
                    volume = random.randint(10, 200)
                    
                    conn.execute(text("""
                        INSERT INTO price_history (skin_id, price, date, volume)
                        VALUES (:skin_id, :price, :date, :volume)
                        ON CONFLICT DO NOTHING
                    """), {
                        'skin_id': skin_id,
                        'price': price,
                        'date': date.date(),
                        'volume': volume
                    })
            
            # Inserir insights de mercado
            logger.info("📊 Inserindo insights de mercado...")
            for days_ago in range(7):
                date = datetime.now() - timedelta(days=days_ago)
                total_listings = random.randint(5000, 15000)
                total_value = random.uniform(500000, 2000000)
                avg_price = total_value / total_listings
                volatility = random.uniform(0.1, 0.5)
                
                conn.execute(text("""
                    INSERT INTO market_insights (date, total_listings, total_value, avg_price, volatility_index)
                    VALUES (:date, :listings, :value, :avg_price, :volatility)
                    ON CONFLICT DO NOTHING
                """), {
                    'date': date.date(),
                    'listings': total_listings,
                    'value': total_value,
                    'avg_price': avg_price,
                    'volatility': volatility
                })
            
            conn.commit()
            logger.info("✅ Dados inseridos com sucesso!")
            
            # Mostrar estatísticas
            show_database_stats(engine)
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Erro ao popular banco: {e}")
        return False

def show_database_stats(engine):
    """Mostra estatísticas do banco"""
    try:
        with engine.connect() as conn:
            # Contar skins
            result = conn.execute(text("SELECT COUNT(*) FROM skins_optimized"))
            skins_count = result.fetchone()[0]
            
            # Contar listings
            result = conn.execute(text("SELECT COUNT(*) FROM listings_optimized"))
            listings_count = result.fetchone()[0]
            
            # Valor total
            result = conn.execute(text("SELECT SUM(price) FROM listings_optimized WHERE price > 0"))
            total_value = result.fetchone()[0] or 0
            
            # Preço médio
            result = conn.execute(text("SELECT AVG(price) FROM listings_optimized WHERE price > 0"))
            avg_price = result.fetchone()[0] or 0
            
            logger.info("📊 ESTATÍSTICAS FINAIS:")
            logger.info(f"   🎨 Skins: {skins_count}")
            logger.info(f"   📦 Listings: {listings_count}")
            logger.info(f"   💰 Valor Total: ${total_value/100:,.2f}")
            logger.info(f"   📈 Preço Médio: ${avg_price/100:.2f}")
            
    except Exception as e:
        logger.error(f"❌ Erro ao mostrar estatísticas: {e}")

def main():
    """Função principal"""
    success = populate_railway_database()
    
    if success:
        logger.info("🎉 População concluída!")
        logger.info("🌐 Acesse: https://skinlytics-production.up.railway.app")
    else:
        logger.error("❌ Falha na população do banco")

if __name__ == "__main__":
    main()
