#!/usr/bin/env python3
"""
📊 MONITOR DE POPULAÇÃO - Acompanha dados em tempo real
"""

import os
import time
import psutil
import logging
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Conecta com o PostgreSQL ou SQLite"""
    try:
        if 'DATABASE_URL' in os.environ:
            return create_engine(os.environ['DATABASE_URL'])
        else:
            return create_engine('sqlite:///data/skins_saas.db')
    except Exception as e:
        logger.error(f"Erro ao conectar com banco: {e}")
        return None

def get_database_stats():
    """Obtem estatisticas detalhadas do banco"""
    engine = get_db_connection()
    if not engine:
        return None

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
            
            # Preco medio
            result = conn.execute(text("SELECT AVG(price) FROM listings_optimized WHERE price > 0"))
            avg_price = result.fetchone()[0] or 0
            
            # Listings por hora (ultimas 24h)
            result = conn.execute(text("""
                SELECT COUNT(*) FROM listings_optimized 
                WHERE collected_at >= NOW() - INTERVAL '24 hours'
            """))
            listings_24h = result.fetchone()[0]
            
            # Top skins por volume
            result = conn.execute(text("""
                SELECT s.market_hash_name, COUNT(l.id) as volume, AVG(l.price) as avg_price
                FROM skins_optimized s
                JOIN listings_optimized l ON s.id = l.skin_id
                WHERE l.price > 0
                GROUP BY s.id, s.market_hash_name
                ORDER BY volume DESC
                LIMIT 5
            """))
            top_skins = result.fetchall()
            
            # Distribuicao por raridade
            result = conn.execute(text("""
                SELECT s.rarity, COUNT(l.id) as count
                FROM skins_optimized s
                JOIN listings_optimized l ON s.id = l.skin_id
                GROUP BY s.rarity
                ORDER BY count DESC
            """))
            rarity_dist = result.fetchall()
            
            return {
                'skins': skins_count,
                'listings': listings_count,
                'total_value': total_value / 100,  # Convert to USD
                'avg_price': avg_price / 100,  # Convert to USD
                'listings_24h': listings_24h,
                'top_skins': top_skins,
                'rarity_dist': rarity_dist,
                'status': 'Conectado'
            }
    except Exception as e:
        return {'skins': 0, 'listings': 0, 'total_value': 0, 'avg_price': 0, 'status': f'Erro: {e}'}

def check_collector_status():
    """Verifica se o processo do collector esta rodando"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.cmdline()
            if 'demo_collector.py' in ' '.join(cmdline):
                return "Rodando"
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return "Parado"

def get_recent_logs(log_file='demo_collector.log', num_lines=5):
    """Le as ultimas linhas do arquivo de log"""
    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            return "".join(lines[-num_lines:])
    except FileNotFoundError:
        return "Arquivo de log nao encontrado."
    except Exception as e:
        return f"Erro ao ler log: {e}"

def monitor_population(interval=30, max_iterations=20):
    """Loop principal de monitoramento"""
    logger.info("MONITOR DE POPULACAO DE DADOS")
    logger.info("="*50)

    iteration = 0
    while iteration < max_iterations:
        iteration += 1
        current_time = datetime.now().strftime("%H:%M:%S")

        logger.info(f"\n[{current_time}] Monitor - Iteracao {iteration}")
        logger.info("="*50)

        # Status do Collector
        collector_status = check_collector_status()
        logger.info(f"STATUS DO COLLECTOR: {collector_status}")

        # Estatisticas do Banco
        db_stats = get_database_stats()
        if db_stats:
            logger.info(f"\nESTATISTICAS DO BANCO:")
            logger.info(f"   Skins: {db_stats['skins']}")
            logger.info(f"   Listings: {db_stats['listings']}")
            logger.info(f"   Valor Total: ${db_stats['total_value']:,.2f}")
            logger.info(f"   Preco Medio: ${db_stats['avg_price']:.2f}")
            logger.info(f"   Listings 24h: {db_stats['listings_24h']}")
            logger.info(f"   Status: {db_stats['status']}")

            # Top skins
            if db_stats['top_skins']:
                logger.info(f"\nTOP SKINS POR VOLUME:")
                for i, skin in enumerate(db_stats['top_skins'][:3], 1):
                    name = skin[0][:40]
                    volume = skin[1]
                    avg_price = skin[2] / 100
                    logger.info(f"   {i}. {name}: {volume} listings, ${avg_price:.2f}")

            # Distribuicao por raridade
            if db_stats['rarity_dist']:
                logger.info(f"\nDISTRIBUICAO POR RARIDADE:")
                rarity_names = {0: "Consumer", 1: "Industrial", 2: "Mil-Spec", 3: "Restricted", 
                              4: "Classified", 5: "Covert", 6: "Contraband"}
                for rarity, count in db_stats['rarity_dist'][:5]:
                    name = rarity_names.get(rarity, f"Rarity {rarity}")
                    logger.info(f"   {name}: {count} listings")

        # Logs Recentes
        recent_logs = get_recent_logs()
        logger.info(f"\nLOGS RECENTES:\n{recent_logs}")

        # Calculo de taxa de crescimento
        if iteration > 1 and db_stats:
            growth_rate = (db_stats['listings'] - getattr(monitor_population, 'last_listings', 0)) / interval * 60
            logger.info(f"TAXA DE CRESCIMENTO: {growth_rate:.1f} listings/min")
            monitor_population.last_listings = db_stats['listings']

        logger.info(f"\nAtualizando em {interval}s... (Ctrl+C para parar)")
        time.sleep(interval)

if __name__ == "__main__":
    try:
        monitor_population(interval=30, max_iterations=40)
    except KeyboardInterrupt:
        logger.info("\nMonitor interrompido pelo usuario")
    except Exception as e:
        logger.error(f"Erro no monitor: {e}")
