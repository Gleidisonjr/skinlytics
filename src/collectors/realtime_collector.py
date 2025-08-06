import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
import os
from dotenv import load_dotenv

from src.models.database import get_session, Skin, Listing, StickerApplication, create_tables
from src.services.csfloat_service import CSFloatService

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('data/realtime_collector.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class RealtimeCollector:
    def __init__(self):
        self.session = get_session()
        self.is_running = False
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
    
    async def continuous_collection(self):
        """Coleta contínua com máximo de dados possível"""
        logger.info("🚀 Iniciando coleta em tempo real...")
        
        # Configurações de coleta agressiva
        collection_configs = [
            # Coleta geral com diferentes ordenações
            {"sort_by": "most_recent", "limit": 50, "name": "Recent"},
            {"sort_by": "lowest_price", "limit": 50, "name": "Cheapest"},
            {"sort_by": "highest_price", "limit": 20, "name": "Expensive"},
            {"sort_by": "best_deal", "limit": 50, "name": "Best Deals"},
            
            # Por categoria
            {"category": 1, "limit": 30, "name": "Normal Items"},  # Normal
            {"category": 2, "limit": 20, "name": "StatTrak"},     # StatTrak
            {"category": 3, "limit": 10, "name": "Souvenir"},     # Souvenir
            
            # Por faixas de preço (em cents)
            {"min_price": 1, "max_price": 5000, "limit": 50, "name": "Under $50"},
            {"min_price": 5000, "max_price": 50000, "limit": 30, "name": "$50-$500"},
            {"min_price": 50000, "max_price": 500000, "limit": 20, "name": "$500-$5000"},
            {"min_price": 500000, "limit": 10, "name": "Over $5000"},
            
            # Por float ranges
            {"min_float": 0.0, "max_float": 0.07, "limit": 20, "name": "Factory New"},
            {"min_float": 0.07, "max_float": 0.15, "limit": 20, "name": "Minimal Wear"},
            {"min_float": 0.15, "max_float": 0.38, "limit": 20, "name": "Field-Tested"},
            {"min_float": 0.38, "max_float": 0.45, "limit": 15, "name": "Well-Worn"},
            {"min_float": 0.45, "max_float": 1.0, "limit": 10, "name": "Battle-Scarred"},
        ]
        
        async with CSFloatService() as csfloat_service:
            while self.is_running:
                total_collected = 0
                
                for config in collection_configs:
                    try:
                        logger.info(f"📊 Coletando: {config['name']}")
                        
                        listings = await csfloat_service.get_listings(**{
                            k: v for k, v in config.items() if k not in ['name']
                        })
                        
                        collected = 0
                        for listing_data in listings:
                            try:
                                if self._process_listing_enhanced(listing_data):
                                    collected += 1
                            except Exception as e:
                                logger.error(f"Error processing listing: {e}")
                                continue
                        
                        if collected > 0:
                            self.session.commit()
                            total_collected += collected
                            logger.info(f"✅ {config['name']}: {collected} listings")
                        
                        # Rate limiting - respeitar API
                        await asyncio.sleep(2)
                        
                    except Exception as e:
                        logger.error(f"Error in {config['name']} collection: {e}")
                        await asyncio.sleep(5)
                        continue
                
                logger.info(f"🎯 Ciclo completo: {total_collected} listings coletados")
                
                # Pausa entre ciclos completos
                logger.info("⏱️ Aguardando próximo ciclo (30s)...")
                await asyncio.sleep(30)
    
    def _process_listing_enhanced(self, listing_data: Dict[str, Any]) -> bool:
        """Processa listing com máximo de informações"""
        try:
            item_data = listing_data.get('item', {})
            seller_data = listing_data.get('seller', {})
            
            market_hash_name = item_data.get('market_hash_name')
            if not market_hash_name:
                return False
            
            # Find or create skin com mais informações
            skin = self.session.query(Skin).filter_by(
                market_hash_name=market_hash_name
            ).first()
            
            if not skin:
                skin = Skin(
                    market_hash_name=market_hash_name,
                    item_name=item_data.get('item_name'),
                    wear_name=item_data.get('wear_name'),
                    def_index=item_data.get('def_index'),
                    paint_index=item_data.get('paint_index'),
                    rarity=item_data.get('rarity'),
                    quality=item_data.get('quality'),
                    collection=item_data.get('collection'),
                    description=item_data.get('description'),
                    icon_url=item_data.get('icon_url'),
                    is_stattrak=item_data.get('is_stattrak', False),
                    is_souvenir=item_data.get('is_souvenir', False)
                )
                self.session.add(skin)
                self.session.flush()
            
            # Check if listing exists
            listing_id = listing_data.get('id')
            existing = self.session.query(Listing).filter_by(id=listing_id).first()
            
            if existing:
                # Update com todas as informações
                existing.state = listing_data.get('state')
                existing.price = listing_data.get('price')
                existing.seller_online = seller_data.get('online', False)
                existing.watchers = listing_data.get('watchers', 0)
                existing.collected_at = datetime.utcnow()
                
                # Update seller stats if available
                if seller_data.get('statistics'):
                    stats = seller_data['statistics']
                    existing.seller_total_trades = stats.get('total_trades', 0)
                    existing.seller_verified_trades = stats.get('total_verified_trades', 0)
                    existing.seller_median_trade_time = stats.get('median_trade_time', 0)
                    existing.seller_failed_trades = stats.get('total_failed_trades', 0)
                
                return False  # Não é novo
            else:
                # Parse datetime corretamente
                created_at = None
                if listing_data.get('created_at'):
                    try:
                        created_at = datetime.fromisoformat(
                            listing_data['created_at'].replace('Z', '+00:00')
                        )
                    except:
                        pass
                
                # Create new listing com TODAS as informações
                listing = Listing(
                    id=listing_id,
                    skin_id=skin.id,
                    created_at_csfloat=created_at,
                    type=listing_data.get('type'),
                    price=listing_data.get('price'),
                    state=listing_data.get('state'),
                    
                    # Item details expandidos
                    asset_id=item_data.get('asset_id'),
                    paint_seed=item_data.get('paint_seed'),
                    float_value=item_data.get('float_value'),
                    tradable=item_data.get('tradable'),
                    inspect_link=item_data.get('inspect_link'),
                    has_screenshot=item_data.get('has_screenshot', False),
                    
                    # Seller info expandido
                    seller_steam_id=seller_data.get('steam_id'),
                    seller_username=seller_data.get('username'),
                    seller_avatar=seller_data.get('avatar'),
                    seller_online=seller_data.get('online', False),
                    
                    # Market data
                    min_offer_price=listing_data.get('min_offer_price'),
                    max_offer_discount=listing_data.get('max_offer_discount'),
                    watchers=listing_data.get('watchers', 0),
                    is_watchlisted=listing_data.get('is_watchlisted', False)
                )
                
                # Adicionar estatísticas do vendedor se disponível
                if seller_data.get('statistics'):
                    stats = seller_data['statistics']
                    listing.seller_total_trades = stats.get('total_trades', 0)
                    listing.seller_verified_trades = stats.get('total_verified_trades', 0)
                    listing.seller_median_trade_time = stats.get('median_trade_time', 0)
                    listing.seller_failed_trades = stats.get('total_failed_trades', 0)
                
                self.session.add(listing)
                self.session.flush()
                
                # Process stickers com mais detalhes
                stickers = item_data.get('stickers', [])
                for sticker_data in stickers:
                    sticker = StickerApplication(
                        listing_id=listing.id,
                        sticker_id=sticker_data.get('stickerId'),
                        slot=sticker_data.get('slot'),
                        wear=sticker_data.get('wear'),
                        icon_url=sticker_data.get('icon_url'),
                        name=sticker_data.get('name'),
                        scm_price=sticker_data.get('scm', {}).get('price'),
                        scm_volume=sticker_data.get('scm', {}).get('volume')
                    )
                    self.session.add(sticker)
                
                return True
                
        except Exception as e:
            logger.error(f"Error processing listing: {e}")
            return False
    
    async def collect_popular_skins(self):
        """Coleta skins populares específicas"""
        popular_skins = [
            "AK-47 | Redline",
            "AWP | Dragon Lore", 
            "AK-47 | Fire Serpent",
            "M4A4 | Howl",
            "AWP | Asiimov",
            "Glock-18 | Fade",
            "Desert Eagle | Blaze",
            "USP-S | Kill Confirmed",
            "Karambit",
            "Butterfly Knife",
            "Bayonet",
            "M4A1-S | Hot Rod",
            "AK-47 | Case Hardened",
            "AWP | Lightning Strike"
        ]
        
        async with CSFloatService() as csfloat_service:
            for skin_name in popular_skins:
                try:
                    logger.info(f"🎯 Coletando skin popular: {skin_name}")
                    
                    listings = await csfloat_service.get_listings(
                        market_hash_name=skin_name,
                        limit=20,
                        sort_by="most_recent"
                    )
                    
                    collected = 0
                    for listing_data in listings:
                        if self._process_listing_enhanced(listing_data):
                            collected += 1
                    
                    if collected > 0:
                        self.session.commit()
                        logger.info(f"✅ {skin_name}: {collected} listings")
                    
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error collecting {skin_name}: {e}")
                    continue
    
    def start_realtime_collection(self):
        """Inicia coleta em tempo real"""
        self.is_running = True
        
        async def run_both():
            # Criar tarefas paralelas
            tasks = [
                asyncio.create_task(self.continuous_collection()),
                asyncio.create_task(self.collect_popular_skins_loop())
            ]
            
            await asyncio.gather(*tasks)
        
        asyncio.run(run_both())
    
    async def collect_popular_skins_loop(self):
        """Loop para coletar skins populares a cada 5 minutos"""
        while self.is_running:
            await self.collect_popular_skins()
            logger.info("⏰ Aguardando próxima coleta de populares (5min)...")
            await asyncio.sleep(300)  # 5 minutos
    
    def stop_collection(self):
        """Para a coleta"""
        self.is_running = False
        logger.info("🛑 Parando coleta em tempo real...")

def main():
    """Função principal para execução"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Realtime CSFloat Collector')
    parser.add_argument('--create-tables', action='store_true', help='Create database tables')
    parser.add_argument('--duration', type=int, help='Duration in minutes (0 = infinite)')
    
    args = parser.parse_args()
    
    if args.create_tables:
        create_tables()
        logger.info("Database tables created")
    
    try:
        with RealtimeCollector() as collector:
            if args.duration and args.duration > 0:
                logger.info(f"🕐 Coletando por {args.duration} minutos...")
                
                async def timed_collection():
                    collector.is_running = True
                    task = asyncio.create_task(collector.continuous_collection())
                    await asyncio.sleep(args.duration * 60)
                    collector.stop_collection()
                    task.cancel()
                
                asyncio.run(timed_collection())
            else:
                logger.info("🔄 Iniciando coleta contínua (Ctrl+C para parar)...")
                collector.start_realtime_collection()
                
    except KeyboardInterrupt:
        logger.info("\n🛑 Coleta interrompida pelo usuário")
    except Exception as e:
        logger.error(f"Erro na coleta: {e}")

if __name__ == "__main__":
    main()