#!/usr/bin/env python3
"""
Script para verificar se o banco PostgreSQL está funcionando
"""

import os
import psycopg2
from sqlalchemy import create_engine, text
import pandas as pd

def check_database():
    """Verifica se o banco está funcionando"""
    print("🔍 Verificando banco de dados...")
    
    try:
        # Tentar conectar com Railway PostgreSQL
        if 'DATABASE_URL' in os.environ:
            print("✅ DATABASE_URL encontrada")
            engine = create_engine(os.environ['DATABASE_URL'])
            
            with engine.connect() as conn:
                # Verificar tabelas
                result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
                tables = [row[0] for row in result.fetchall()]
                print(f"📊 Tabelas encontradas: {tables}")
                
                # Verificar dados
                if 'listings_optimized' in tables:
                    result = conn.execute(text("SELECT COUNT(*) FROM listings_optimized"))
                    listings_count = result.fetchone()[0]
                    print(f"📦 Listings: {listings_count:,}")
                
                if 'skins_optimized' in tables:
                    result = conn.execute(text("SELECT COUNT(*) FROM skins_optimized"))
                    skins_count = result.fetchone()[0]
                    print(f"🎨 Skins: {skins_count:,}")
                
                if 'price_history' in tables:
                    result = conn.execute(text("SELECT COUNT(*) FROM price_history"))
                    history_count = result.fetchone()[0]
                    print(f"📈 Price History: {history_count:,}")
                
                # Últimos listings
                result = conn.execute(text("""
                    SELECT s.market_hash_name, l.price, l.collected_at
                    FROM listings_optimized l
                    JOIN skins_optimized s ON l.skin_id = s.id
                    ORDER BY l.collected_at DESC
                    LIMIT 5
                """))
                recent = result.fetchall()
                
                if recent:
                    print("\n🕐 Últimos listings:")
                    for listing in recent:
                        print(f"  - {listing[0][:40]}: ${listing[1]/100:.2f} ({listing[2]})")
                else:
                    print("⚠️ Nenhum listing encontrado")
                    
        else:
            print("❌ DATABASE_URL não encontrada")
            print("💡 Configure a variável DATABASE_URL no Railway")
            
    except Exception as e:
        print(f"❌ Erro ao conectar com banco: {e}")

if __name__ == "__main__":
    check_database()
