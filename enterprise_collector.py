#!/usr/bin/env python3
"""
🚀 SKINLYTICS ENTERPRISE COLLECTOR
Coletor otimizado para arquitetura PostgreSQL + ClickHouse + Redis
"""
import asyncio
import aiohttp
import json
import time
from datetime import datetime
import argparse
import logging
import sys
from typing import List, Dict, Any
import redis
from sqlalchemy.exc import IntegrityError

# Importar nossos modelos - USANDO MODELO OTIMIZADO
from src.models.optimized_database import get_session, Skin as OptimizedSkin, ListingOptimized
from src.services.csfloat_service import CSFloatService

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('data/enterprise_collector.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class EnterpriseCollector:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.logger = logging.getLogger(__name__)
        
        # Services
        self.csfloat_service = CSFloatService()
        
        # Redis cache
        self.redis_client = redis.Redis(
            host='localhost', 
            port=6379, 
            password='redis_pass_2025',
            decode_responses=True
        )
        
        # Estatísticas
        self.stats = {
            'total_collected': 0,
            'total_requests': 0,
            'failed_requests': 0,
            'start_time': time.time(),
            'duplicates_skipped': 0,
            'cache_hits': 0
        }
        
        self.logger.info("🚀 Enterprise Collector inicializado")
        self.logger.info("✅ PostgreSQL, ClickHouse e Redis configurados")
    
    async def create_session(self):
        """Inicializa sessão HTTP"""
        # CSFloatService usa context manager, não precisamos de create_session
        self.logger.info("📡 Sessão HTTP enterprise pronta")
    
    def is_listing_cached(self, listing_id: str) -> bool:
        """Verifica se listing já foi processado (Redis cache)"""
        try:
            cached = self.redis_client.get(f"listing:{listing_id}")
            if cached:
                self.stats['cache_hits'] += 1
                return True
            return False
        except Exception as e:
            self.logger.warning(f"Erro no cache Redis: {e}")
            return False
    
    def cache_listing(self, listing_id: str):
        """Marca listing como processado no cache"""
        try:
            # Cache por 7 dias
            self.redis_client.setex(f"listing:{listing_id}", 604800, "processed")
        except Exception as e:
            self.logger.warning(f"Erro ao cachear: {e}")
    
    def save_listing_enterprise(self, listing_data: Dict) -> bool:
        """Salva listing na arquitetura enterprise OTIMIZADA (PostgreSQL)"""
        session = get_session()
        
        try:
            # Verificar se listing já existe
            listing_id = listing_data.get('id')
            if not listing_id:
                return False
            
            # Cache check
            if self.is_listing_cached(listing_id):
                self.stats['duplicates_skipped'] += 1
                return False
            
            existing = session.query(ListingOptimized).filter_by(id=listing_id).first()
            if existing:
                self.stats['duplicates_skipped'] += 1
                self.cache_listing(listing_id)
                return False
            
            # Extrair dados do item
            item = listing_data.get('item', {})
            seller = listing_data.get('seller', {})
            
            # Criar/obter skin OTIMIZADA
            market_hash_name = item.get('market_hash_name', '')
            skin = None
            
            if market_hash_name:
                skin = session.query(OptimizedSkin).filter_by(market_hash_name=market_hash_name).first()
                
                if not skin:
                    # Modelo otimizado - apenas campos essenciais
                    skin = OptimizedSkin(
                        market_hash_name=market_hash_name,
                        item_name=item.get('item_name', ''),
                        wear_name=item.get('wear_name', ''),
                        def_index=item.get('def_index'),
                        paint_index=item.get('paint_index'),
                        rarity=item.get('rarity'),
                        is_stattrak=item.get('is_stattrak', False),
                        is_souvenir=item.get('is_souvenir', False)
                    )
                    session.add(skin)
                    session.flush()  # Para obter o ID
            
            # Criar hash do seller para privacidade
            import hashlib
            seller_hash = None
            if seller.get('steam_id'):
                seller_hash = hashlib.sha256(seller['steam_id'].encode()).hexdigest()[:16]
            
            # Criar listing OTIMIZADO
            listing = ListingOptimized(
                id=listing_id,
                skin_id=skin.id if skin else None,
                created_at_csfloat=listing_data.get('created_at'),
                type=listing_data.get('type', 'buy_now'),
                price=listing_data.get('price', 0),  # Manter em centavos como integer
                state=listing_data.get('state', ''),
                
                # Propriedades essenciais do item
                paint_seed=item.get('paint_seed'),
                float_value=item.get('float_value'),
                
                # Market dynamics essenciais
                watchers=listing_data.get('watchers', 0),
                min_offer_price=listing_data.get('min_offer_price', 0),
                max_offer_discount=listing_data.get('max_offer_discount', 0),
                
                # Seller hash (privacidade)
                seller_hash=seller_hash
            )
            
            # Estatísticas do vendedor (essenciais para credibilidade)
            seller_stats = seller.get('statistics', {})
            if seller_stats:
                listing.seller_total_trades = seller_stats.get('total_trades', 0)
                listing.seller_verified_trades = seller_stats.get('total_verified_trades', 0)
                listing.seller_median_trade_time = seller_stats.get('median_trade_time', 0)
                listing.seller_failed_trades = seller_stats.get('total_failed_trades', 0)
            
            session.add(listing)
            
            # NOTA: Stickers removidos do modelo otimizado por enquanto
            # Eles podem ser adicionados em uma tabela separada se necessário
            
            session.commit()
            
            # Cache como processado
            self.cache_listing(listing_id)
            
            self.stats['total_collected'] += 1
            return True
            
        except IntegrityError:
            session.rollback()
            self.stats['duplicates_skipped'] += 1
            return False
            
        except Exception as e:
            session.rollback()
            self.logger.error(f"Erro ao salvar listing {listing_id}: {e}")
            return False
            
        finally:
            session.close()
    
    async def collect_listings_page(self, page: int, sort_by: str = 'most_recent') -> List[Dict]:
        """Coleta uma página de listings usando CSFloat service"""
        try:
            async with self.csfloat_service as service:
                listings = await service.get_listings(
                    page=page,
                    limit=50,
                    sort_by=sort_by
                )
            
            self.stats['total_requests'] += 1
            return listings
            
        except Exception as e:
            self.logger.error(f"Erro ao coletar página {page}: {e}")
            self.stats['failed_requests'] += 1
            return []
    
    async def enterprise_collection_cycle(self, max_pages: int = 10, concurrent_workers: int = 3):
        """Executa um ciclo de coleta enterprise"""
        self.logger.info(f"🔥 Iniciando ciclo ENTERPRISE: {max_pages} páginas, {concurrent_workers} workers")
        
        strategies = [
            'most_recent',
            'lowest_price', 
            'highest_price',
            'lowest_float',
            'highest_float'
        ]
        
        total_new = 0
        
        for strategy in strategies:
            self.logger.info(f"📊 Estratégia: {strategy}")
            
            # Coleta paralela
            tasks = []
            for page in range(max_pages):
                task = self.collect_listings_page(page, strategy)
                tasks.append(task)
            
            # Executar em lotes
            batch_size = concurrent_workers
            for i in range(0, len(tasks), batch_size):
                batch = tasks[i:i + batch_size]
                results = await asyncio.gather(*batch, return_exceptions=True)
                
                # Processar resultados
                for page_listings in results:
                    if isinstance(page_listings, list):
                        for listing in page_listings:
                            if self.save_listing_enterprise(listing):
                                total_new += 1
                
                # Pausa entre lotes
                await asyncio.sleep(1)
            
            # Pausa entre estratégias  
            await asyncio.sleep(2)
        
        self.logger.info(f"✅ Ciclo concluído: +{total_new} novos listings")
        return total_new
    
    def print_enterprise_stats(self):
        """Mostra estatísticas enterprise"""
        runtime = time.time() - self.stats['start_time']
        success_rate = ((self.stats['total_requests'] - self.stats['failed_requests']) / max(1, self.stats['total_requests'])) * 100
        
        print("\n" + "="*70)
        print("🚀 ENTERPRISE COLLECTOR - ESTATÍSTICAS")
        print("="*70)
        print(f"🐘 PostgreSQL: Dados operacionais")
        print(f"🏠 ClickHouse: Preparado para analytics")
        print(f"🔴 Redis: {self.stats['cache_hits']:,} cache hits")
        print(f"⏱️  Runtime: {runtime/60:.1f} minutos")
        print(f"📦 Total Coletados: {self.stats['total_collected']:,}")
        print(f"🔄 Total Requests: {self.stats['total_requests']:,}")
        print(f"✅ Taxa de Sucesso: {success_rate:.1f}%")
        print(f"⚡ Duplicatas Ignoradas: {self.stats['duplicates_skipped']:,}")
        print(f"🎯 Listings/min: {self.stats['total_collected']/(runtime/60):.1f}")
        print("="*70)
    
    async def run_enterprise_collection(self, cycles: int = 10, interval: int = 300):
        """Executa coleta enterprise contínua"""
        await self.create_session()
        
        self.logger.info(f"🚀 INICIANDO ENTERPRISE COLLECTOR - {cycles} ciclos")
        self.logger.info("🏗️ Arquitetura: PostgreSQL + ClickHouse + Redis")
        
        try:
            for cycle in range(cycles):
                self.logger.info(f"\n🔥 CICLO ENTERPRISE {cycle + 1}/{cycles}")
                
                new_listings = await self.enterprise_collection_cycle(
                    max_pages=8,  # Otimizado para enterprise
                    concurrent_workers=4
                )
                
                self.print_enterprise_stats()
                
                if cycle < cycles - 1:
                    self.logger.info(f"⏳ Aguardando {interval}s até próximo ciclo...")
                    await asyncio.sleep(interval)
        
        finally:
            # CSFloatService usa context manager, não precisa de close manual
            self.logger.info("🔌 Sessão enterprise fechada")

async def main():
    parser = argparse.ArgumentParser(description='Enterprise Collector - PostgreSQL + ClickHouse + Redis')
    parser.add_argument('--cycles', type=int, default=20, help='Número de ciclos')
    parser.add_argument('--interval', type=int, default=300, help='Intervalo entre ciclos (segundos)')
    args = parser.parse_args()
    
    # API Key do .env
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('CSFLOAT_API_KEY')
    if not api_key:
        print("❌ CSFLOAT_API_KEY não encontrada no .env")
        return
    
    collector = EnterpriseCollector(api_key)
    await collector.run_enterprise_collection(cycles=args.cycles, interval=args.interval)

if __name__ == "__main__":
    asyncio.run(main())