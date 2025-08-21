#!/usr/bin/env python3
"""
🎮 STEAM ONLY COLLECTOR - Coletor Baseado no Steam Market
Usa Steam Market API (funcionando) + lista de skins populares
"""

import asyncio
import aiohttp
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import csv
import os

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('steam_collector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SteamOnlyCollector:
    def __init__(self):
        self.session = None
        self.steam_market_base = "https://steamcommunity.com/market/priceoverview/"
        
        # Rate limiting para Steam
        self.steam_requests = 0
        self.last_steam_reset = time.time()
        self.steam_delay = 1.0  # 60 requests/min = 1s entre requests
        
        # Lista de skins populares (fallback)
        self.popular_skins = [
            "AK-47 | Redline (Field-Tested)",
            "AK-47 | Redline (Minimal Wear)",
            "AK-47 | Redline (Well-Worn)",
            "AK-47 | Redline (Battle-Scarred)",
            "AK-47 | Redline (Factory New)",
            "M4A4 | Desolate Space (Field-Tested)",
            "M4A4 | Desolate Space (Minimal Wear)",
            "M4A4 | Desolate Space (Well-Worn)",
            "M4A4 | Desolate Space (Battle-Scarred)",
            "M4A4 | Desolate Space (Factory New)",
            "AWP | Dragon Lore (Factory New)",
            "AWP | Dragon Lore (Minimal Wear)",
            "AWP | Dragon Lore (Field-Tested)",
            "AWP | Dragon Lore (Well-Worn)",
            "AWP | Dragon Lore (Battle-Scarred)",
            "M4A1-S | Hyper Beast (Field-Tested)",
            "M4A1-S | Hyper Beast (Minimal Wear)",
            "M4A1-S | Hyper Beast (Well-Worn)",
            "M4A1-S | Hyper Beast (Battle-Scarred)",
            "M4A1-S | Hyper Beast (Factory New)",
            "USP-S | Kill Confirmed (Field-Tested)",
            "USP-S | Kill Confirmed (Minimal Wear)",
            "USP-S | Kill Confirmed (Well-Worn)",
            "USP-S | Kill Confirmed (Battle-Scarred)",
            "USP-S | Kill Confirmed (Factory New)",
            "Glock-18 | Water Elemental (Field-Tested)",
            "Glock-18 | Water Elemental (Minimal Wear)",
            "Glock-18 | Water Elemental (Well-Worn)",
            "Glock-18 | Water Elemental (Battle-Scarred)",
            "Glock-18 | Water Elemental (Factory New)",
            "Desert Eagle | Golden Koi (Field-Tested)",
            "Desert Eagle | Golden Koi (Minimal Wear)",
            "Desert Eagle | Golden Koi (Well-Worn)",
            "Desert Eagle | Golden Koi (Battle-Scarred)",
            "Desert Eagle | Golden Koi (Factory New)",
            "Karambit | Fade (Factory New)",
            "Karambit | Fade (Minimal Wear)",
            "Karambit | Fade (Field-Tested)",
            "Karambit | Fade (Well-Worn)",
            "Karambit | Fade (Battle-Scarred)",
            "M9 Bayonet | Marble Fade (Factory New)",
            "M9 Bayonet | Marble Fade (Minimal Wear)",
            "M9 Bayonet | Marble Fade (Field-Tested)",
            "M9 Bayonet | Marble Fade (Well-Worn)",
            "M9 Bayonet | Marble Fade (Battle-Scarred)",
            "Butterfly Knife | Fade (Factory New)",
            "Butterfly Knife | Fade (Minimal Wear)",
            "Butterfly Knife | Fade (Field-Tested)",
            "Butterfly Knife | Fade (Well-Worn)",
            "Butterfly Knife | Fade (Battle-Scarred)"
        ]
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Skinlytics/1.0 (Portfolio Project)',
                'Accept': 'application/json'
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _respect_steam_rate_limit(self):
        """Respeita rate limit do Steam Market"""
        current_time = time.time()
        
        # Reset contador a cada minuto
        if current_time - self.last_steam_reset >= 60:
            self.steam_requests = 0
            self.last_steam_reset = current_time
        
        # Aguarda se necessário
        if self.steam_requests >= 60:  # 60 requests/min para Steam
            wait_time = 60 - (current_time - self.last_steam_reset)
            if wait_time > 0:
                logger.info(f"Rate limit Steam atingido. Aguardando {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
                self.steam_requests = 0
                self.last_steam_reset = current_time
        
        self.steam_requests += 1
        await asyncio.sleep(self.steam_delay)
    
    async def get_steam_market_prices(self, market_hash_names: List[str]) -> Dict:
        """Coleta preços do Steam Market"""
        results = {}
        
        logger.info(f"🎮 Coletando preços de {len(market_hash_names)} skins do Steam Market...")
        
        for i, market_hash_name in enumerate(market_hash_names):
            try:
                await self._respect_steam_rate_limit()
                
                params = {
                    'appid': '730',  # CS2
                    'currency': '1',  # USD
                    'market_hash_name': market_hash_name
                }
                
                async with self.session.get(self.steam_market_base, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success'):
                            results[market_hash_name] = {
                                'source': 'steam_market',
                                'data': data,
                                'timestamp': datetime.now().isoformat()
                            }
                            logger.info(f"   ✅ {i+1}/{len(market_hash_names)}: {market_hash_name[:30]}... - ${data.get('median_price', 'N/A')}")
                        else:
                            logger.warning(f"   ⚠️ Steam Market error for {market_hash_name}: {data}")
                    else:
                        logger.warning(f"   ❌ Steam Market HTTP {response.status} for {market_hash_name}")
                        
            except Exception as e:
                logger.error(f"   ❌ Erro ao coletar {market_hash_name}: {e}")
                continue
        
        logger.info(f"🎯 Steam Market: {len(results)} skins coletadas com sucesso")
        return results
    
    def load_skins_from_csv(self, csv_file: str = "data/skins_list_en.csv") -> List[str]:
        """Carrega lista de skins do arquivo CSV existente"""
        try:
            if os.path.exists(csv_file):
                skins = []
                with open(csv_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if 'market_hash_name' in row and row['market_hash_name']:
                            skins.append(row['market_hash_name'])
                
                logger.info(f"📋 CSV carregado: {len(skins)} skins encontradas")
                return skins[:100]  # Limitar a 100 para teste
            else:
                logger.warning(f"📋 Arquivo CSV não encontrado: {csv_file}")
                return []
        except Exception as e:
            logger.error(f"❌ Erro ao carregar CSV: {e}")
            return []
    
    def get_test_skins(self, count: int = 50) -> List[str]:
        """Retorna lista de skins para teste"""
        # Primeiro tenta carregar do CSV
        csv_skins = self.load_skins_from_csv()
        
        if csv_skins:
            return csv_skins[:count]
        else:
            # Fallback para lista hardcoded
            logger.info(f"📋 Usando lista de skins hardcoded: {len(self.popular_skins)} skins")
            return self.popular_skins[:count]
    
    async def collect_all_data(self, max_skins: int = 50) -> Dict:
        """Coleta dados do Steam Market"""
        logger.info("🎯 Iniciando coleta de dados do Steam Market")
        
        # 1. Obter lista de skins
        test_skins = self.get_test_skins(max_skins)
        logger.info(f"🎮 Coletando dados para {len(test_skins)} skins")
        
        if not test_skins:
            logger.error("❌ Não foi possível obter lista de skins")
            return {}
        
        # 2. Coletar dados do Steam Market
        steam_data = await self.get_steam_market_prices(test_skins)
        
        # 3. Consolidar dados
        consolidated_data = {
            'metadata': {
                'total_skins': len(test_skins),
                'steam_count': len(steam_data),
                'collection_timestamp': datetime.now().isoformat(),
                'sources': ['steam_market'],
                'note': 'Dados coletados apenas do Steam Market (Pricempire API retornando 403)'
            },
            'skins': {},
            'steam_market': steam_data
        }
        
        # Consolidar por skin
        for skin in test_skins:
            consolidated_data['skins'][skin] = {
                'steam_market': steam_data.get(skin),
                'best_price': None,
                'price_info': {}
            }
            
            # Extrair informações de preço
            if skin in steam_data:
                steam_info = steam_data[skin]['data']
                
                # Converter preços para float
                median_price = steam_info.get('median_price', '0')
                lowest_price = steam_info.get('lowest_price', '0')
                
                try:
                    median_float = float(median_price.replace('$', '').replace(',', '')) if median_price != '0' else 0
                    lowest_float = float(lowest_price.replace('$', '').replace(',', '')) if lowest_price != '0' else 0
                    
                    consolidated_data['skins'][skin]['price_info'] = {
                        'median_price': median_float,
                        'lowest_price': lowest_float,
                        'volume': steam_info.get('volume', '0'),
                        'success': steam_info.get('success', False)
                    }
                    
                    # Definir melhor preço
                    if median_float > 0:
                        consolidated_data['skins'][skin]['best_price'] = {
                            'source': 'steam_market',
                            'price': median_float,
                            'type': 'median'
                        }
                    elif lowest_float > 0:
                        consolidated_data['skins'][skin]['best_price'] = {
                            'source': 'steam_market',
                            'price': lowest_float,
                            'type': 'lowest'
                        }
                        
                except ValueError:
                    logger.warning(f"⚠️ Erro ao converter preços para {skin}")
                    continue
        
        logger.info(f"🎯 Coleta concluída! {len(consolidated_data['skins'])} skins processadas")
        return consolidated_data
    
    def save_data(self, data: Dict, filename: str = None):
        """Salva dados coletados em arquivo JSON"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"steam_collection_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"💾 Dados salvos em {filename}")
            return filename
        except Exception as e:
            logger.error(f"❌ Erro ao salvar dados: {e}")
            return None

async def main():
    """Função principal para teste"""
    logger.info("🚀 Iniciando Steam Only Collector")
    
    async with SteamOnlyCollector() as collector:
        # Coletar dados
        data = await collector.collect_all_data(max_skins=30)  # Começar com 30 skins
        
        if data:
            # Salvar dados
            filename = collector.save_data(data)
            
            # Mostrar resumo
            logger.info("📊 RESUMO DA COLETA:")
            logger.info(f"   Total de skins: {data['metadata']['total_skins']}")
            logger.info(f"   Steam Market: {data['metadata']['steam_count']}")
            logger.info(f"   Arquivo salvo: {filename}")
            
            # Mostrar algumas skins com preços
            logger.info("\n💰 EXEMPLOS DE PREÇOS:")
            count = 0
            for skin_name, skin_data in data['skins'].items():
                if count >= 5:  # Mostrar apenas 5 exemplos
                    break
                if skin_data['best_price']:
                    logger.info(f"   {skin_name}: ${skin_data['best_price']['price']:.2f} ({skin_data['best_price']['source']})")
                    count += 1
        else:
            logger.error("❌ Falha na coleta de dados")

if __name__ == "__main__":
    asyncio.run(main())
