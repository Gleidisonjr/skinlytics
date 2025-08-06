"""
CS2 Skin Mass Collector - Coleta Massiva Otimizada

Este módulo implementa um sistema de coleta massiva de dados do CSFloat,
projetado para coletar informações de TODAS as skins disponíveis de forma
eficiente e escalável.

Features:
    - Coleta paralela com controle de rate limiting
    - Sistema de retry automático para falhas
    - Persistência otimizada em lotes (batch processing)
    - Monitoramento de progresso em tempo real
    - Recuperação automática de interrupções
    - Filtragem inteligente de duplicatas

Author: CS2 Skin Tracker Team
Version: 2.0.0
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set
import json
import time
from pathlib import Path
import signal
import sys
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager

from sqlalchemy.orm import sessionmaker
from sqlalchemy import and_, or_, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from ..models.database import get_engine, Skin, Listing, StickerApplication
from ..services.csfloat_service import CSFloatService

# Configurar logging estruturado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('data/mass_collector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class CollectionStats:
    """Estatísticas da coleta massiva"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    duplicate_listings: int = 0
    new_listings: int = 0
    new_skins: int = 0
    start_time: datetime = None
    end_time: datetime = None
    
    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    @property
    def duration(self) -> timedelta:
        if not self.start_time or not self.end_time:
            return timedelta(0)
        return self.end_time - self.start_time
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class MassCollector:
    """
    Coletor massivo otimizado para CSFloat API.
    
    Este coletor implementa estratégias avançadas para coletar o máximo
    de dados possível respeitando os limites da API e otimizando performance.
    """
    
    def __init__(self, api_key: str, max_concurrent: int = 5, batch_size: int = 100):
        """
        Inicializa o coletor massivo.
        
        Args:
            api_key (str): Chave da API CSFloat
            max_concurrent (int): Número máximo de requisições simultâneas
            batch_size (int): Tamanho do lote para inserção no banco
        """
        self.api_key = api_key
        self.max_concurrent = max_concurrent
        self.batch_size = batch_size
        self.stats = CollectionStats()
        self.running = False
        self.session_factory = None
        self.engine = None
        
        # Controle de rate limiting
        self.rate_limit_delay = 1.0  # Segundos entre requisições
        self.last_request_time = 0
        
        # Cache para evitar duplicatas
        self.processed_listings: Set[str] = set()
        self.processed_skins: Set[str] = set()
        
        # Configurar tratamento de sinais
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Tratamento de sinais para parada graceful"""
        logger.info(f"Sinal {signum} recebido. Parando coleta...")
        self.running = False
    
    async def initialize(self):
        """Inicializa componentes do coletor"""
        logger.info("Inicializando Mass Collector...")
        
        # Configurar banco de dados
        self.engine = get_engine()
        self.session_factory = sessionmaker(bind=self.engine)
        
        # Carregar cache de IDs já processados
        await self._load_processed_cache()
        
        logger.info(f"Mass Collector inicializado. Cache: {len(self.processed_listings)} listings, {len(self.processed_skins)} skins")
    
    async def _load_processed_cache(self):
        """Carrega cache de IDs já processados do banco"""
        try:
            with self.session_factory() as session:
                # Carregar listings já processados
                listing_ids = session.query(Listing.id).all()
                self.processed_listings = {lid[0] for lid in listing_ids}
                
                # Carregar skins já processadas
                skin_names = session.query(Skin.market_hash_name).all()
                self.processed_skins = {name[0] for name in skin_names}
                
            logger.info(f"Cache carregado: {len(self.processed_listings)} listings, {len(self.processed_skins)} skins")
            
        except Exception as e:
            logger.error(f"Erro ao carregar cache: {e}")
    
    @asynccontextmanager
    async def _rate_limited_request(self):
        """Context manager para controle de rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = time.time()
        yield
    
    async def _fetch_listings_batch(self, session: aiohttp.ClientSession, 
                                   csfloat_service: CSFloatService,
                                   page: int, **params) -> List[Dict[str, Any]]:
        """
        Busca um lote de listings com retry automático.
        
        Args:
            session: Sessão aiohttp
            csfloat_service: Serviço CSFloat
            page: Número da página
            **params: Parâmetros adicionais para a API
            
        Returns:
            Lista de listings ou lista vazia em caso de erro
        """
        max_retries = 3
        retry_delay = 2.0
        
        for attempt in range(max_retries):
            try:
                async with self._rate_limited_request():
                    self.stats.total_requests += 1
                    
                    listings = await csfloat_service.get_listings(
                        page=page, 
                        limit=50,  # Máximo da API
                        **params
                    )
                    
                    if listings:
                        self.stats.successful_requests += 1
                        logger.debug(f"Página {page}: {len(listings)} listings obtidos")
                        return listings
                    else:
                        logger.warning(f"Página {page}: Nenhum listing retornado")
                        return []
                        
            except Exception as e:
                self.stats.failed_requests += 1
                logger.warning(f"Tentativa {attempt + 1} falhou para página {page}: {e}")
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (attempt + 1))
                else:
                    logger.error(f"Falha definitiva na página {page} após {max_retries} tentativas")
        
        return []
    
    async def _process_listings_batch(self, listings: List[Dict[str, Any]]) -> tuple:
        """
        Processa um lote de listings e salva no banco.
        
        Args:
            listings: Lista de dados de listings da API
            
        Returns:
            Tuple (novos_listings, novas_skins, duplicatas)
        """
        if not listings:
            return 0, 0, 0
        
        new_listings_count = 0
        new_skins_count = 0
        duplicates_count = 0
        
        try:
            with self.session_factory() as db_session:
                skin_objects = {}
                listing_objects = []
                sticker_objects = []
                
                for listing_data in listings:
                    listing_id = listing_data.get('id')
                    if not listing_id:
                        continue
                    
                    # Verificar duplicatas
                    if listing_id in self.processed_listings:
                        duplicates_count += 1
                        continue
                    
                    # Processar skin
                    item_info = listing_data.get('item', {})
                    market_hash_name = item_info.get('market_hash_name', '')
                    
                    if market_hash_name and market_hash_name not in skin_objects:
                        if market_hash_name not in self.processed_skins:
                            # Nova skin
                            skin = Skin(
                                market_hash_name=market_hash_name,
                                item_name=item_info.get('item_name', ''),
                                wear_name=item_info.get('wear_name', ''),
                                def_index=item_info.get('def_index'),
                                paint_index=item_info.get('paint_index'),
                                rarity=item_info.get('rarity'),
                                quality=item_info.get('quality'),
                                collection=item_info.get('collection', ''),
                                description=item_info.get('description', ''),
                                icon_url=item_info.get('icon_url', ''),
                                is_stattrak=item_info.get('is_stattrak', False),
                                is_souvenir=item_info.get('is_souvenir', False)
                            )
                            skin_objects[market_hash_name] = skin
                            self.processed_skins.add(market_hash_name)
                            new_skins_count += 1
                        else:
                            # Skin existente - buscar do banco
                            existing_skin = db_session.query(Skin).filter(
                                Skin.market_hash_name == market_hash_name
                            ).first()
                            if existing_skin:
                                skin_objects[market_hash_name] = existing_skin
                    
                    # Processar listing
                    skin_obj = skin_objects.get(market_hash_name)
                    if skin_obj:
                        # Dados do vendedor
                        seller_info = listing_data.get('seller', {})
                        seller_stats = seller_info.get('statistics', {})
                        
                        # Criar objeto listing
                        listing = Listing(
                            id=listing_id,
                            skin_id=skin_obj.id if hasattr(skin_obj, 'id') else None,
                            created_at_csfloat=datetime.fromisoformat(
                                listing_data.get('created_at', '').replace('Z', '+00:00')
                            ) if listing_data.get('created_at') else None,
                            type=listing_data.get('type', ''),
                            price=listing_data.get('price'),
                            state=listing_data.get('state', ''),
                            asset_id=listing_data.get('asset_id'),
                            paint_seed=item_info.get('paint_seed'),
                            float_value=item_info.get('float_value'),
                            tradable=listing_data.get('tradable'),
                            inspect_link=item_info.get('inspect_link', ''),
                            has_screenshot=listing_data.get('has_screenshot', False),
                            watchers=listing_data.get('watchers', 0),
                            seller_steam_id=seller_info.get('steam_id', ''),
                            seller_username=seller_info.get('username', ''),
                            seller_avatar=seller_info.get('avatar', ''),
                            seller_online=seller_info.get('online', False),
                            seller_total_trades=seller_stats.get('total_trades', 0),
                            seller_verified_trades=seller_stats.get('verified_trades', 0),
                            seller_median_trade_time=seller_stats.get('median_trade_time', 0),
                            seller_failed_trades=seller_stats.get('failed_trades', 0)
                        )
                        
                        listing_objects.append(listing)
                        self.processed_listings.add(listing_id)
                        new_listings_count += 1
                        
                        # Processar stickers
                        stickers = item_info.get('stickers', [])
                        for i, sticker_data in enumerate(stickers):
                            sticker = StickerApplication(
                                listing_id=listing_id,
                                sticker_id=sticker_data.get('sticker_id'),
                                slot=sticker_data.get('slot', i),
                                wear=sticker_data.get('wear'),
                                icon_url=sticker_data.get('icon_url', ''),
                                name=sticker_data.get('name', ''),
                                scm_price=sticker_data.get('scm_price', 0),
                                scm_volume=sticker_data.get('scm_volume', 0)
                            )
                            sticker_objects.append(sticker)
                
                # Salvar em lotes para performance
                if skin_objects:
                    for skin in skin_objects.values():
                        if not hasattr(skin, 'id'):  # Nova skin
                            db_session.add(skin)
                    db_session.flush()  # Para obter IDs das skins
                
                # Atualizar skin_id dos listings
                for listing in listing_objects:
                    if listing.skin_id is None:
                        skin_name = next((name for name, obj in skin_objects.items() 
                                        if obj == listing.skin), None)
                        if skin_name:
                            listing.skin_id = skin_objects[skin_name].id
                
                # Salvar listings e stickers
                if listing_objects:
                    db_session.add_all(listing_objects)
                if sticker_objects:
                    db_session.add_all(sticker_objects)
                
                db_session.commit()
                
                logger.debug(f"Lote processado: {new_listings_count} novos listings, "
                           f"{new_skins_count} novas skins, {duplicates_count} duplicatas")
                
        except Exception as e:
            logger.error(f"Erro ao processar lote: {e}")
            return 0, 0, 0
        
        return new_listings_count, new_skins_count, duplicates_count
    
    async def collect_all_categories(self, max_pages_per_category: int = 100):
        """
        Coleta listings de todas as categorias disponíveis.
        
        Args:
            max_pages_per_category: Máximo de páginas por categoria
        """
        logger.info("Iniciando coleta massiva de todas as categorias...")
        self.stats.start_time = datetime.now()
        self.running = True
        
        # Definir estratégias de coleta
        collection_strategies = [
            # Ordenações básicas
            {"sort_by": "most_recent", "category": 0, "name": "Recent All"},
            {"sort_by": "lowest_price", "category": 0, "name": "Cheapest All"},
            {"sort_by": "highest_price", "category": 0, "name": "Most Expensive"},
            {"sort_by": "best_deal", "category": 0, "name": "Best Deals"},
            
            # Por categoria
            {"sort_by": "best_deal", "category": 1, "name": "Normal Items"},
            {"sort_by": "best_deal", "category": 2, "name": "StatTrak Items"},
            {"sort_by": "best_deal", "category": 3, "name": "Souvenir Items"},
            
            # Faixas de preço (em centavos)
            {"sort_by": "best_deal", "min_price": 1, "max_price": 1000, "name": "Under $10"},
            {"sort_by": "best_deal", "min_price": 1000, "max_price": 5000, "name": "$10-$50"},
            {"sort_by": "best_deal", "min_price": 5000, "max_price": 10000, "name": "$50-$100"},
            {"sort_by": "best_deal", "min_price": 10000, "max_price": 50000, "name": "$100-$500"},
            {"sort_by": "best_deal", "min_price": 50000, "max_price": 100000, "name": "$500-$1000"},
            {"sort_by": "best_deal", "min_price": 100000, "name": "Over $1000"},
            
            # Faixas de float
            {"sort_by": "best_deal", "min_float": 0.0, "max_float": 0.07, "name": "Factory New"},
            {"sort_by": "best_deal", "min_float": 0.07, "max_float": 0.15, "name": "Minimal Wear"},
            {"sort_by": "best_deal", "min_float": 0.15, "max_float": 0.38, "name": "Field-Tested"},
            {"sort_by": "best_deal", "min_float": 0.38, "max_float": 0.45, "name": "Well-Worn"},
            {"sort_by": "best_deal", "min_float": 0.45, "max_float": 1.0, "name": "Battle-Scarred"},
        ]
        
        async with aiohttp.ClientSession() as session:
            csfloat_service = CSFloatService(self.api_key, session)
            
            for strategy in collection_strategies:
                if not self.running:
                    break
                
                strategy_name = strategy.pop("name")
                logger.info(f"🎯 Coletando categoria: {strategy_name}")
                
                await self._collect_strategy(csfloat_service, strategy_name, 
                                           max_pages_per_category, **strategy)
                
                # Pequena pausa entre categorias
                await asyncio.sleep(2)
        
        self.stats.end_time = datetime.now()
        await self._log_final_stats()
    
    async def _collect_strategy(self, csfloat_service: CSFloatService, 
                              strategy_name: str, max_pages: int, **params):
        """Coleta uma estratégia específica"""
        page = 0
        consecutive_empty = 0
        strategy_listings = 0
        strategy_skins = 0
        
        while page < max_pages and consecutive_empty < 5 and self.running:
            # Coletar lote
            listings = await self._fetch_listings_batch(
                None, csfloat_service, page, **params
            )
            
            if not listings:
                consecutive_empty += 1
                logger.warning(f"{strategy_name} - Página {page}: vazia ({consecutive_empty}/5)")
                page += 1
                continue
            
            consecutive_empty = 0
            
            # Processar lote
            new_listings, new_skins, duplicates = await self._process_listings_batch(listings)
            
            strategy_listings += new_listings
            strategy_skins += new_skins
            
            self.stats.new_listings += new_listings
            self.stats.new_skins += new_skins
            self.stats.duplicate_listings += duplicates
            
            # Log de progresso
            if page % 10 == 0:
                logger.info(f"{strategy_name} - Página {page}: "
                          f"{new_listings} novos, {duplicates} duplicatas "
                          f"(Total: {strategy_listings} listings, {strategy_skins} skins)")
            
            page += 1
            
            # Controle de performance
            await asyncio.sleep(0.1)
        
        logger.info(f"✅ {strategy_name} concluída: "
                   f"{strategy_listings} listings, {strategy_skins} skins em {page} páginas")
    
    async def _log_final_stats(self):
        """Log das estatísticas finais"""
        logger.info("=" * 80)
        logger.info("📊 COLETA MASSIVA CONCLUÍDA")
        logger.info("=" * 80)
        logger.info(f"⏱️  Duração: {self.stats.duration}")
        logger.info(f"📡 Requisições: {self.stats.total_requests} "
                   f"({self.stats.successful_requests} sucesso, "
                   f"{self.stats.failed_requests} falhas)")
        logger.info(f"📈 Taxa de sucesso: {self.stats.success_rate:.1f}%")
        logger.info(f"🎮 Novas skins: {self.stats.new_skins:,}")
        logger.info(f"📋 Novos listings: {self.stats.new_listings:,}")
        logger.info(f"🔄 Duplicatas evitadas: {self.stats.duplicate_listings:,}")
        logger.info(f"💾 Total em cache: {len(self.processed_listings):,} listings, "
                   f"{len(self.processed_skins):,} skins")
        logger.info("=" * 80)
        
        # Salvar estatísticas
        stats_file = Path("data/mass_collection_stats.json")
        with open(stats_file, "w") as f:
            json.dump(self.stats.to_dict(), f, indent=2, default=str)
        
        logger.info(f"📊 Estatísticas salvas em: {stats_file}")

async def main():
    """Função principal para execução standalone"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    api_key = os.getenv('CSFLOAT_API_KEY')
    if not api_key:
        logger.error("CSFLOAT_API_KEY não encontrada nas variáveis de ambiente")
        return
    
    collector = MassCollector(api_key, max_concurrent=3, batch_size=50)
    
    try:
        await collector.initialize()
        await collector.collect_all_categories(max_pages_per_category=50)
    except KeyboardInterrupt:
        logger.info("Coleta interrompida pelo usuário")
    except Exception as e:
        logger.error(f"Erro na coleta: {e}")
    finally:
        logger.info("Finalizando coletor...")

if __name__ == "__main__":
    asyncio.run(main())