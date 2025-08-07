#!/usr/bin/env python3
"""
🚀 DEMO COLLECTOR - Coletor otimizado para Windows
- Respeita rate limits
- Sem emojis (compatível Windows)
- Conexões limpas
- Logs detalhados
"""

import asyncio
import aiohttp
import logging
import time
import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text
import json

# Configurar encoding para Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

# Configurar logging sem emojis
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('demo_collector.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DemoCSFloatCollector:
    def __init__(self):
        self.api_key = "phtZp7cjyjCviMBP9J7nvBpEkggaUQQO"
        self.base_url = "https://csfloat.com/api/v1"
        self.session = None
        self.engine = None
        self.stats = {
            'requests_made': 0,
            'successful_requests': 0,
            'rate_limited': 0,
            'skins_collected': 0,
            'listings_collected': 0,
            'errors': 0
        }
        
    async def setup(self):
        """Configura conexoes"""
        # Configurar aiohttp session
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'User-Agent': 'Skinlytics/1.0'
            }
        )
        
        # Configurar banco de dados
        if 'DATABASE_URL' in os.environ:
            self.engine = create_engine(os.environ['DATABASE_URL'])
        else:
            self.engine = create_engine('sqlite:///data/skins_saas.db')
            
        logger.info("Conexoes configuradas")
        
    async def cleanup(self):
        """Limpa recursos"""
        if self.session:
            await self.session.close()
        logger.info("Recursos limpos")
        
    async def make_request(self, url, params=None, delay=5.0):
        """Faz requisicao com delay e retry"""
        self.stats['requests_made'] += 1
        
        # Delay para respeitar rate limits
        await asyncio.sleep(delay)
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 429:
                    self.stats['rate_limited'] += 1
                    logger.warning(f"Rate limited - aguardando 120s")
                    await asyncio.sleep(120)  # Espera 2 minutos
                    return None
                    
                elif response.status == 200:
                    self.stats['successful_requests'] += 1
                    data = await response.json()
                    return data
                    
                else:
                    logger.error(f"Erro {response.status}: {await response.text()}")
                    self.stats['errors'] += 1
                    return None
                    
        except Exception as e:
            logger.error(f"Erro na requisicao: {e}")
            self.stats['errors'] += 1
            return None
            
    async def collect_listings(self, strategy='newest', max_pages=2):
        """Coleta listings com estrategia especifica"""
        logger.info(f"Coletando listings: {strategy}")
        
        collected_data = []
        
        for page in range(max_pages):
            params = {
                'page': page,
                'limit': 25,  # Reduzido para 25
                'sort_by': strategy,
                'category': 0
            }
            
            url = f"{self.base_url}/listings"
            data = await self.make_request(url, params, delay=10.0)  # Delay aumentado
            
            if not data or 'data' not in data:
                logger.warning(f"Sem dados na pagina {page}")
                break
                
            listings = data['data']
            if not listings:
                logger.info(f"Fim dos dados na pagina {page}")
                break
                
            collected_data.extend(listings)
            logger.info(f"Pagina {page}: {len(listings)} listings")
            
            # Delay entre paginas
            await asyncio.sleep(15.0)  # Delay aumentado
            
        return collected_data
        
    async def save_to_database(self, listings):
        """Salva dados no banco"""
        if not listings:
            return
            
        try:
            with self.engine.connect() as conn:
                for listing in listings:
                    # Extrair dados do listing
                    skin_name = listing.get('market_hash_name', 'Unknown')
                    price = listing.get('price', 0)
                    float_value = listing.get('float_value', 0)
                    watchers = listing.get('watchers', 0)
                    
                    # Inserir skin se nao existir
                    result = conn.execute(text("""
                        INSERT INTO skins_optimized (market_hash_name, rarity, is_stattrak)
                        VALUES (:name, :rarity, :stattrak)
                        ON CONFLICT DO NOTHING
                        RETURNING id
                    """), {
                        'name': skin_name,
                        'rarity': 0,  # Default
                        'stattrak': 'StatTrak' in skin_name
                    })
                    
                    skin_id = result.fetchone()
                    if skin_id:
                        skin_id = skin_id[0]
                    else:
                        # Buscar skin existente
                        result = conn.execute(text("""
                            SELECT id FROM skins_optimized WHERE market_hash_name = :name
                        """), {'name': skin_name})
                        skin_id = result.fetchone()[0]
                    
                    # Inserir listing
                    conn.execute(text("""
                        INSERT INTO listings_optimized (skin_id, price, float_value, watchers)
                        VALUES (:skin_id, :price, :float_value, :watchers)
                    """), {
                        'skin_id': skin_id,
                        'price': price,
                        'float_value': float_value,
                        'watchers': watchers
                    })
                    
                conn.commit()
                self.stats['listings_collected'] += len(listings)
                logger.info(f"Salvos {len(listings)} listings no banco")
                
        except Exception as e:
            logger.error(f"Erro ao salvar no banco: {e}")
            
    async def show_stats(self):
        """Mostra estatisticas"""
        logger.info("ESTATISTICAS DA COLETA:")
        logger.info(f"   Requisicoes feitas: {self.stats['requests_made']}")
        logger.info(f"   Requisicoes bem-sucedidas: {self.stats['successful_requests']}")
        logger.info(f"   Rate limited: {self.stats['rate_limited']}")
        logger.info(f"   Listings coletados: {self.stats['listings_collected']}")
        logger.info(f"   Erros: {self.stats['errors']}")
        
    async def run_collection(self, cycles=1):
        """Executa coleta completa"""
        logger.info("INICIANDO COLETA DEMO")
        
        await self.setup()
        
        strategies = ['newest']  # Apenas uma estrategia
        
        for cycle in range(cycles):
            logger.info(f"Ciclo {cycle + 1}/{cycles}")
            
            for strategy in strategies:
                logger.info(f"Estrategia: {strategy}")
                
                listings = await self.collect_listings(strategy, max_pages=1)  # Apenas 1 pagina
                
                if listings:
                    await self.save_to_database(listings)
                    
                # Delay entre estrategias
                await asyncio.sleep(30.0)
                
            # Delay entre ciclos
            if cycle < cycles - 1:
                logger.info("Aguardando 60s antes do proximo ciclo...")
                await asyncio.sleep(60.0)
                
        await self.show_stats()
        await self.cleanup()
        
        logger.info("Coleta concluida!")

async def main():
    """Funcao principal"""
    collector = DemoCSFloatCollector()
    await collector.run_collection(cycles=1)

if __name__ == "__main__":
    asyncio.run(main())
