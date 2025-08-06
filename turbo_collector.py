#!/usr/bin/env python3
"""
🚀 TURBO COLLECTOR - Coleta maximizada de dados CSFloat
Versão otimizada para coletar o máximo de dados possível
"""
import asyncio
import aiohttp
import sqlite3
import json
import time
from datetime import datetime
import argparse
import logging
import sys
from typing import List, Dict, Any

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('data/turbo_collector.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class TurboCollector:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://csfloat.com/api/v1"
        self.session = None
        self.db_path = 'data/skins.db'
        self.logger = logging.getLogger(__name__)
        
        # Estatísticas
        self.stats = {
            'total_collected': 0,
            'total_requests': 0,
            'failed_requests': 0,
            'start_time': time.time(),
            'duplicates_skipped': 0
        }
        
        # Cache para evitar duplicatas
        self.existing_listings = set()
        self.load_existing_listings()
    
    def load_existing_listings(self):
        """Carrega IDs dos listings existentes para evitar duplicatas"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM listings")
            self.existing_listings = {row[0] for row in cursor.fetchall()}
            conn.close()
            self.logger.info(f"Cache carregado: {len(self.existing_listings)} listings existentes")
        except Exception as e:
            self.logger.warning(f"Erro ao carregar cache: {e}")
            self.existing_listings = set()
    
    async def create_session(self):
        """Cria sessão HTTP otimizada"""
        connector = aiohttp.TCPConnector(
            limit=50,  # Máximo de conexões
            limit_per_host=10,  # Por host
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        
        headers = {
            'Authorization': self.api_key,
            'User-Agent': 'Skinlytics-TurboCollector/1.0'
        }
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=headers
        )
        
        self.logger.info("Sessão HTTP criada com otimizações")
    
    async def get_listings_page(self, page: int, sort_by: str = 'most_recent', **params) -> List[Dict]:
        """Coleta uma página de listings"""
        url = f"{self.base_url}/listings"
        
        query_params = {
            'page': page,
            'limit': 50,  # Máximo por página
            'sort_by': sort_by,
            **params
        }
        
        try:
            async with self.session.get(url, params=query_params) as response:
                self.stats['total_requests'] += 1
                
                if response.status == 200:
                    data = await response.json()
                    
                    # CSFloat retorna {"data": [...]}
                    if isinstance(data, dict) and 'data' in data:
                        listings = data['data']
                    elif isinstance(data, list):
                        listings = data
                    else:
                        self.logger.warning(f"Formato inesperado: {type(data)}")
                        return []
                    
                    return listings
                
                elif response.status == 429:
                    # Rate limit - aguardar mais tempo
                    self.logger.warning("Rate limit atingido, aguardando...")
                    await asyncio.sleep(10)
                    return []
                
                else:
                    self.logger.error(f"Erro {response.status}: {await response.text()}")
                    self.stats['failed_requests'] += 1
                    return []
                    
        except Exception as e:
            self.logger.error(f"Erro na requisição: {e}")
            self.stats['failed_requests'] += 1
            return []
    
    def save_listings_batch(self, listings: List[Dict]):
        """Salva lote de listings no banco"""
        if not listings:
            return 0
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Verificar se tabelas existem
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS skins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                market_hash_name TEXT UNIQUE,
                item_name TEXT,
                wear_name TEXT,
                def_index INTEGER,
                paint_index INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS listings (
                id TEXT PRIMARY KEY,
                item_name TEXT,
                price_usd REAL,
                float_value REAL,
                paint_seed INTEGER,
                paint_index INTEGER,
                def_index INTEGER,
                wear_name TEXT,
                rarity INTEGER,
                collection TEXT,
                stickers TEXT,
                seller_id TEXT,
                seller_username TEXT,
                seller_stats TEXT,
                created_at_csfloat TEXT,
                collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        new_count = 0
        
        for listing in listings:
            try:
                listing_id = listing.get('id')
                
                # Pular se já existe
                if listing_id in self.existing_listings:
                    self.stats['duplicates_skipped'] += 1
                    continue
                
                item = listing.get('item', {})
                seller = listing.get('seller', {})
                
                # Dados do listing
                data = {
                    'id': listing_id,
                    'item_name': item.get('item_name', ''),
                    'price_usd': listing.get('price', 0) / 100.0,  # CSFloat usa centavos
                    'float_value': item.get('float_value'),
                    'paint_seed': item.get('paint_seed'),
                    'paint_index': item.get('paint_index'),
                    'def_index': item.get('def_index'),
                    'wear_name': item.get('wear_name', ''),
                    'rarity': item.get('rarity'),
                    'collection': item.get('collection', ''),
                    'stickers': json.dumps(item.get('stickers', [])),
                    'seller_id': seller.get('steam_id', ''),
                    'seller_username': seller.get('username', ''),
                    'seller_stats': json.dumps(seller.get('statistics', {})),
                    'created_at_csfloat': listing.get('created_at', '')
                }
                
                # Inserir listing
                cursor.execute("""
                    INSERT OR IGNORE INTO listings 
                    (id, item_name, price_usd, float_value, paint_seed, paint_index, 
                     def_index, wear_name, rarity, collection, stickers, seller_id, 
                     seller_username, seller_stats, created_at_csfloat)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data['id'], data['item_name'], data['price_usd'], data['float_value'],
                    data['paint_seed'], data['paint_index'], data['def_index'], 
                    data['wear_name'], data['rarity'], data['collection'], data['stickers'],
                    data['seller_id'], data['seller_username'], data['seller_stats'],
                    data['created_at_csfloat']
                ))
                
                if cursor.rowcount > 0:
                    new_count += 1
                    self.existing_listings.add(listing_id)
                
                # Inserir skin (se nova)
                market_hash_name = item.get('market_hash_name', '')
                if market_hash_name:
                    cursor.execute("""
                        INSERT OR IGNORE INTO skins 
                        (market_hash_name, item_name, wear_name, def_index, paint_index)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        market_hash_name, data['item_name'], data['wear_name'],
                        data['def_index'], data['paint_index']
                    ))
                
            except Exception as e:
                self.logger.error(f"Erro ao salvar listing {listing.get('id', 'unknown')}: {e}")
        
        conn.commit()
        conn.close()
        
        return new_count
    
    async def turbo_collect_cycle(self, max_pages: int = 20, concurrent_workers: int = 5):
        """Executa um ciclo de coleta turbo"""
        self.logger.info(f"Iniciando ciclo TURBO: {max_pages} páginas, {concurrent_workers} workers")
        
        # Diferentes estratégias de coleta para maximizar dados
        strategies = [
            {'sort_by': 'most_recent'},
            {'sort_by': 'lowest_price'},
            {'sort_by': 'highest_price'},
            {'sort_by': 'lowest_float'},
            {'sort_by': 'highest_float'},
        ]
        
        total_new = 0
        
        for strategy in strategies:
            self.logger.info(f"Estratégia: {strategy}")
            
            # Criar tasks para coleta paralela
            tasks = []
            for page in range(max_pages):
                task = self.get_listings_page(page, **strategy)
                tasks.append(task)
            
            # Executar em lotes para não sobrecarregar
            batch_size = concurrent_workers
            for i in range(0, len(tasks), batch_size):
                batch = tasks[i:i + batch_size]
                results = await asyncio.gather(*batch, return_exceptions=True)
                
                # Processar resultados
                for result in results:
                    if isinstance(result, list):
                        new_count = self.save_listings_batch(result)
                        total_new += new_count
                        self.stats['total_collected'] += new_count
                
                # Pequena pausa entre lotes
                await asyncio.sleep(1)
            
            # Pausa entre estratégias
            await asyncio.sleep(2)
        
        self.logger.info(f"Ciclo concluído: +{total_new} novos listings")
        return total_new
    
    def print_stats(self):
        """Mostra estatísticas da coleta"""
        runtime = time.time() - self.stats['start_time']
        success_rate = ((self.stats['total_requests'] - self.stats['failed_requests']) / max(1, self.stats['total_requests'])) * 100
        
        print("\n" + "="*60)
        print("🚀 TURBO COLLECTOR - ESTATÍSTICAS")
        print("="*60)
        print(f"⏱️  Runtime: {runtime/60:.1f} minutos")
        print(f"📦 Total Coletados: {self.stats['total_collected']:,}")
        print(f"🔄 Total Requests: {self.stats['total_requests']:,}")
        print(f"✅ Taxa de Sucesso: {success_rate:.1f}%")
        print(f"⚡ Duplicatas Ignoradas: {self.stats['duplicates_skipped']:,}")
        print(f"🎯 Listings/min: {self.stats['total_collected']/(runtime/60):.1f}")
        print("="*60)
    
    async def run_turbo_collection(self, cycles: int = 5, interval: int = 300):
        """Executa coleta turbo contínua"""
        await self.create_session()
        
        self.logger.info(f"🚀 INICIANDO TURBO COLLECTOR - {cycles} ciclos")
        
        try:
            for cycle in range(cycles):
                self.logger.info(f"\n🔥 CICLO {cycle + 1}/{cycles}")
                
                new_listings = await self.turbo_collect_cycle(
                    max_pages=10,  # Reduzido para não bater rate limit
                    concurrent_workers=3
                )
                
                self.print_stats()
                
                if cycle < cycles - 1:
                    self.logger.info(f"⏳ Aguardando {interval}s até próximo ciclo...")
                    await asyncio.sleep(interval)
        
        finally:
            if self.session:
                await self.session.close()
                self.logger.info("🔌 Sessão HTTP fechada")

async def main():
    parser = argparse.ArgumentParser(description='Turbo Collector - Coleta maximizada')
    parser.add_argument('--cycles', type=int, default=10, help='Número de ciclos')
    parser.add_argument('--interval', type=int, default=300, help='Intervalo entre ciclos (segundos)')
    args = parser.parse_args()
    
    # API Key (você deve ter no .env)
    api_key = "brtnO9zH3PuubFCCsQY9kNX5jyqoJvu3"  # Substitua pela sua chave
    
    collector = TurboCollector(api_key)
    await collector.run_turbo_collection(cycles=args.cycles, interval=args.interval)

if __name__ == "__main__":
    asyncio.run(main())