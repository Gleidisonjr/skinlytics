#!/usr/bin/env python3
"""
🎯 RELIABLE COLLECTOR - Coletor Confiável de Dados de Skins CS2
Usa Pricempire API + Steam Market API para dados estáveis e contínuos
"""

import asyncio
import aiohttp
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import random

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('reliable_collector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ReliableSkinCollector:
    def __init__(self):
        self.session = None
        self.pricempire_api_key = "demo"  # Gratuito para testes
        self.steam_market_base = "https://steamcommunity.com/market/priceoverview/"
        self.pricempire_base = "https://api.pricempire.com/v2"
        
        # Rate limiting inteligente
        self.pricempire_requests = 0
        self.steam_requests = 0
        self.last_pricempire_reset = time.time()
        self.last_steam_reset = time.time()
        
        # Delays baseados em rate limits
        self.pricempire_delay = 0.5  # 120 requests/min = 0.5s entre requests
        self.steam_delay = 1.0       # Steam é mais restritivo
        
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
    
    async def _respect_rate_limits(self, api_type: str):
        """Respeita rate limits das diferentes APIs"""
        current_time = time.time()
        
        if api_type == "pricempire":
            # Reset contador a cada minuto
            if current_time - self.last_pricempire_reset >= 60:
                self.pricempire_requests = 0
                self.last_pricempire_reset = current_time
            
            # Aguarda se necessário
            if self.pricempire_requests >= 120:
                wait_time = 60 - (current_time - self.last_pricempire_reset)
                if wait_time > 0:
                    logger.info(f"Rate limit Pricempire atingido. Aguardando {wait_time:.1f}s")
                    await asyncio.sleep(wait_time)
                    self.pricempire_requests = 0
                    self.last_pricempire_reset = time.time()
            
            self.pricempire_requests += 1
            await asyncio.sleep(self.pricempire_delay)
            
        elif api_type == "steam":
            # Steam é mais restritivo
            if current_time - self.last_steam_reset >= 60:
                self.steam_requests = 0
                self.last_steam_reset = current_time
            
            if self.steam_requests >= 60:  # 60 requests/min para Steam
                wait_time = 60 - (current_time - self.last_steam_reset)
                if wait_time > 0:
                    logger.info(f"Rate limit Steam atingido. Aguardando {wait_time:.1f}s")
                    await asyncio.sleep(wait_time)
                    self.steam_requests = 0
                    self.last_steam_reset = time.time()
            
            self.steam_requests += 1
            await asyncio.sleep(self.steam_delay)
    
    async def get_pricempire_prices(self, market_hash_names: List[str]) -> Dict:
        """Coleta preços do Pricempire API"""
        results = {}
        
        for market_hash_name in market_hash_names:
            try:
                await self._respect_rate_limits("pricempire")
                
                url = f"{self.pricempire_base}/getPrice"
                params = {
                    'item': market_hash_name,
                    'currency': 'USD'
                }
                
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success'):
                            results[market_hash_name] = {
                                'source': 'pricempire',
                                'data': data.get('data', {}),
                                'timestamp': datetime.now().isoformat()
                            }
                        else:
                            logger.warning(f"Pricempire API error for {market_hash_name}: {data}")
                    else:
                        logger.warning(f"Pricempire HTTP {response.status} for {market_hash_name}")
                        
            except Exception as e:
                logger.error(f"Erro ao coletar {market_hash_name} do Pricempire: {e}")
                continue
        
        return results
    
    async def get_steam_market_prices(self, market_hash_names: List[str]) -> Dict:
        """Coleta preços do Steam Market"""
        results = {}
        
        for market_hash_name in market_hash_names:
            try:
                await self._respect_rate_limits("steam")
                
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
                        else:
                            logger.warning(f"Steam Market error for {market_hash_name}: {data}")
                    else:
                        logger.warning(f"Steam Market HTTP {response.status} for {market_hash_name}")
                        
            except Exception as e:
                logger.error(f"Erro ao coletar {market_hash_name} do Steam Market: {e}")
                continue
        
        return results
    
    async def get_popular_skins(self) -> List[str]:
        """Obtém lista de skins populares do Pricempire"""
        try:
            await self._respect_rate_limits("pricempire")
            
            url = f"{self.pricempire_base}/getItems"
            params = {
                'game': 'cs2',
                'limit': 100
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success'):
                        items = data.get('data', [])
                        return [item.get('market_hash_name') for item in items if item.get('market_hash_name')]
                    else:
                        logger.error(f"Erro ao obter lista de skins: {data}")
                        return []
                else:
                    logger.error(f"HTTP {response.status} ao obter lista de skins")
                    return []
                    
        except Exception as e:
            logger.error(f"Erro ao obter lista de skins: {e}")
            return []
    
    async def collect_all_data(self, max_skins: int = 50) -> Dict:
        """Coleta dados de todas as fontes"""
        logger.info("🎯 Iniciando coleta confiável de dados de skins CS2")
        
        # 1. Obter lista de skins populares
        logger.info("📋 Obtendo lista de skins populares...")
        popular_skins = await self.get_popular_skins()
        
        if not popular_skins:
            logger.error("❌ Não foi possível obter lista de skins")
            return {}
        
        # Limitar número de skins para teste
        test_skins = popular_skins[:max_skins]
        logger.info(f"🎮 Coletando dados para {len(test_skins)} skins")
        
        # 2. Coletar dados do Pricempire
        logger.info("💰 Coletando dados do Pricempire...")
        pricempire_data = await self.get_pricempire_prices(test_skins)
        logger.info(f"✅ Pricempire: {len(pricempire_data)} skins coletadas")
        
        # 3. Coletar dados do Steam Market
        logger.info("🎮 Coletando dados do Steam Market...")
        steam_data = await self.get_steam_market_prices(test_skins)
        logger.info(f"✅ Steam Market: {len(steam_data)} skins coletadas")
        
        # 4. Consolidar dados
        consolidated_data = {
            'metadata': {
                'total_skins': len(test_skins),
                'pricempire_count': len(pricempire_data),
                'steam_count': len(steam_data),
                'collection_timestamp': datetime.now().isoformat(),
                'sources': ['pricempire', 'steam_market']
            },
            'skins': {},
            'pricempire': pricempire_data,
            'steam_market': steam_data
        }
        
        # Consolidar por skin
        for skin in test_skins:
            consolidated_data['skins'][skin] = {
                'pricempire': pricempire_data.get(skin),
                'steam_market': steam_data.get(skin),
                'best_price': None,
                'price_comparison': {}
            }
            
            # Encontrar melhor preço
            prices = []
            if skin in pricempire_data:
                pricempire_price = pricempire_data[skin]['data'].get('price', 0)
                if pricempire_price:
                    prices.append(('pricempire', pricempire_price))
            
            if skin in steam_data:
                steam_price = steam_data[skin]['data'].get('median_price', 0)
                if steam_price:
                    # Converter string de preço para float
                    try:
                        steam_price_clean = float(steam_price.replace('$', '').replace(',', ''))
                        prices.append(('steam_market', steam_price_clean))
                    except:
                        pass
            
            if prices:
                best_source, best_price = min(prices, key=lambda x: x[1])
                consolidated_data['skins'][skin]['best_price'] = {
                    'source': best_source,
                    'price': best_price
                }
        
        logger.info(f"🎯 Coleta concluída! {len(consolidated_data['skins'])} skins processadas")
        return consolidated_data
    
    def save_data(self, data: Dict, filename: str = None):
        """Salva dados coletados em arquivo JSON"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reliable_collection_{timestamp}.json"
        
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
    logger.info("🚀 Iniciando Reliable Skin Collector")
    
    async with ReliableSkinCollector() as collector:
        # Coletar dados
        data = await collector.collect_all_data(max_skins=20)  # Começar com poucas skins
        
        if data:
            # Salvar dados
            filename = collector.save_data(data)
            
            # Mostrar resumo
            logger.info("📊 RESUMO DA COLETA:")
            logger.info(f"   Total de skins: {data['metadata']['total_skins']}")
            logger.info(f"   Pricempire: {data['metadata']['pricempire_count']}")
            logger.info(f"   Steam Market: {data['metadata']['steam_market_count']}")
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
