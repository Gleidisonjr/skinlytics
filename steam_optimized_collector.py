#!/usr/bin/env python3
"""
🎮 STEAM OPTIMIZED COLLECTOR - Coletor Otimizado do Steam Market
Estratégias inteligentes para maximizar dados coletados
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
import random

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('steam_optimized.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SteamOptimizedCollector:
    def __init__(self):
        self.session = None
        self.steam_market_base = "https://steamcommunity.com/market/priceoverview/"
        
        # Rate limiting otimizado
        self.steam_requests = 0
        self.last_steam_reset = time.time()
        self.steam_delay = 0.8  # 75 requests/min (mais agressivo mas seguro)
        
        # Lista expandida de skins populares
        self.popular_skins = self._load_extended_skin_list()
        
        # Estratégias de coleta
        self.collection_strategies = [
            'popular_skins',      # Skins mais populares
            'weapon_categories',   # Por categoria de arma
            'price_ranges',        # Por faixa de preço
            'rarity_levels'       # Por nível de raridade
        ]
        
    def _load_extended_skin_list(self) -> List[str]:
        """Carrega lista estendida de skins"""
        base_skins = [
            # AK-47 Series
            "AK-47 | Redline (Field-Tested)", "AK-47 | Redline (Minimal Wear)",
            "AK-47 | Redline (Well-Worn)", "AK-47 | Redline (Battle-Scarred)",
            "AK-47 | Redline (Factory New)", "AK-47 | Asiimov (Field-Tested)",
            "AK-47 | Asiimov (Minimal Wear)", "AK-47 | Asiimov (Well-Worn)",
            "AK-47 | Asiimov (Battle-Scarred)", "AK-47 | Asiimov (Factory New)",
            
            # M4A4 Series
            "M4A4 | Desolate Space (Field-Tested)", "M4A4 | Desolate Space (Minimal Wear)",
            "M4A4 | Desolate Space (Well-Worn)", "M4A4 | Desolate Space (Battle-Scarred)",
            "M4A4 | Desolate Space (Factory New)", "M4A4 | Howl (Factory New)",
            "M4A4 | Howl (Minimal Wear)", "M4A4 | Howl (Field-Tested)",
            
            # AWP Series
            "AWP | Dragon Lore (Factory New)", "AWP | Dragon Lore (Minimal Wear)",
            "AWP | Dragon Lore (Field-Tested)", "AWP | Dragon Lore (Well-Worn)",
            "AWP | Dragon Lore (Battle-Scarred)", "AWP | Medusa (Factory New)",
            "AWP | Medusa (Minimal Wear)", "AWP | Medusa (Field-Tested)",
            
            # M4A1-S Series
            "M4A1-S | Hyper Beast (Field-Tested)", "M4A1-S | Hyper Beast (Minimal Wear)",
            "M4A1-S | Hyper Beast (Well-Worn)", "M4A1-S | Hyper Beast (Battle-Scarred)",
            "M4A1-S | Hyper Beast (Factory New)", "M4A1-S | Master Piece (Factory New)",
            
            # USP-S Series
            "USP-S | Kill Confirmed (Field-Tested)", "USP-S | Kill Confirmed (Minimal Wear)",
            "USP-S | Kill Confirmed (Well-Worn)", "USP-S | Kill Confirmed (Battle-Scarred)",
            "USP-S | Kill Confirmed (Factory New)", "USP-S | Kill Confirmed (Minimal Wear)",
            
            # Glock Series
            "Glock-18 | Water Elemental (Field-Tested)", "Glock-18 | Water Elemental (Minimal Wear)",
            "Glock-18 | Water Elemental (Well-Worn)", "Glock-18 | Water Elemental (Battle-Scarred)",
            "Glock-18 | Water Elemental (Factory New)", "Glock-18 | Fade (Factory New)",
            
            # Desert Eagle Series
            "Desert Eagle | Golden Koi (Field-Tested)", "Desert Eagle | Golden Koi (Minimal Wear)",
            "Desert Eagle | Golden Koi (Well-Worn)", "Desert Eagle | Golden Koi (Battle-Scarred)",
            "Desert Eagle | Golden Koi (Factory New)", "Desert Eagle | Blaze (Factory New)",
            
            # Knife Series
            "Karambit | Fade (Factory New)", "Karambit | Fade (Minimal Wear)",
            "Karambit | Fade (Field-Tested)", "Karambit | Fade (Well-Worn)",
            "Karambit | Fade (Battle-Scarred)", "Karambit | Marble Fade (Factory New)",
            "M9 Bayonet | Marble Fade (Factory New)", "M9 Bayonet | Marble Fade (Minimal Wear)",
            "Butterfly Knife | Fade (Factory New)", "Butterfly Knife | Fade (Minimal Wear)",
            
            # Hand Wraps Series
            "★ Hand Wraps | CAUTION! (Field-Tested)", "★ Hand Wraps | CAUTION! (Minimal Wear)",
            "★ Hand Wraps | CAUTION! (Well-Worn)", "★ Hand Wraps | CAUTION! (Battle-Scarred)",
            "★ Hand Wraps | CAUTION! (Factory New)", "★ Hand Wraps | Desert Shamagh (Field-Tested)",
            "★ Hand Wraps | Desert Shamagh (Minimal Wear)", "★ Hand Wraps | Desert Shamagh (Well-Worn)",
            "★ Hand Wraps | Desert Shamagh (Battle-Scarred)", "★ Hand Wraps | Desert Shamagh (Factory New)",
            
            # Specialist Gloves Series
            "★ Specialist Gloves | Crimson Kimono (Field-Tested)", "★ Specialist Gloves | Crimson Kimono (Minimal Wear)",
            "★ Specialist Gloves | Crimson Kimono (Well-Worn)", "★ Specialist Gloves | Crimson Kimono (Battle-Scarred)",
            "★ Specialist Gloves | Crimson Kimono (Factory New)", "★ Specialist Gloves | Emerald Web (Field-Tested)",
            
            # Driver Gloves Series
            "★ Driver Gloves | Crimson Weave (Field-Tested)", "★ Driver Gloves | Crimson Weave (Minimal Wear)",
            "★ Driver Gloves | Crimson Weave (Well-Worn)", "★ Driver Gloves | Crimson Weave (Battle-Scarred)",
            "★ Driver Gloves | Crimson Weave (Factory New)", "★ Driver Gloves | Lunar Weave (Field-Tested)",
            
            # Sport Gloves Series
            "★ Sport Gloves | Vice (Field-Tested)", "★ Sport Gloves | Vice (Minimal Wear)",
            "★ Sport Gloves | Vice (Well-Worn)", "★ Sport Gloves | Vice (Battle-Scarred)",
            "★ Sport Gloves | Vice (Factory New)", "★ Sport Gloves | Pandora's Box (Field-Tested)"
        ]
        
        # Adicionar variações de wear para mais skins
        extended_skins = base_skins.copy()
        
        # Adicionar mais variações
        additional_skins = [
            "AK-47 | Bloodsport (Field-Tested)", "AK-47 | Bloodsport (Minimal Wear)",
            "AK-47 | Bloodsport (Well-Worn)", "AK-47 | Bloodsport (Battle-Scarred)",
            "AK-47 | Bloodsport (Factory New)", "AK-47 | Fire Serpent (Field-Tested)",
            "AK-47 | Fire Serpent (Minimal Wear)", "AK-47 | Fire Serpent (Well-Worn)",
            "AK-47 | Fire Serpent (Battle-Scarred)", "AK-47 | Fire Serpent (Factory New)",
            
            "M4A4 | Evil Daimyo (Field-Tested)", "M4A4 | Evil Daimyo (Minimal Wear)",
            "M4A4 | Evil Daimyo (Well-Worn)", "M4A4 | Evil Daimyo (Battle-Scarred)",
            "M4A4 | Evil Daimyo (Factory New)", "M4A4 | Royal Paladin (Field-Tested)",
            
            "AWP | Lightning Strike (Factory New)", "AWP | Lightning Strike (Minimal Wear)",
            "AWP | Lightning Strike (Field-Tested)", "AWP | Lightning Strike (Well-Worn)",
            "AWP | Lightning Strike (Battle-Scarred)", "AWP | Graphite (Field-Tested)",
            
            "M4A1-S | Cyrex (Field-Tested)", "M4A1-S | Cyrex (Minimal Wear)",
            "M4A1-S | Cyrex (Well-Worn)", "M4A1-S | Cyrex (Battle-Scarred)",
            "M4A1-S | Cyrex (Factory New)", "M4A1-S | Golden Coil (Field-Tested)",
            
            "USP-S | Caiman (Field-Tested)", "USP-S | Caiman (Minimal Wear)",
            "USP-S | Caiman (Well-Worn)", "USP-S | Caiman (Battle-Scarred)",
            "USP-S | Caiman (Factory New)", "USP-S | Road Rash (Field-Tested)",
            
            "Glock-18 | Twilight Galaxy (Field-Tested)", "Glock-18 | Twilight Galaxy (Minimal Wear)",
            "Glock-18 | Twilight Galaxy (Well-Worn)", "Glock-18 | Twilight Galaxy (Battle-Scarred)",
            "Glock-18 | Twilight Galaxy (Factory New)", "Glock-18 | Candy Apple (Field-Tested)",
            
            "Desert Eagle | Sunset Storm (Field-Tested)", "Desert Eagle | Sunset Storm (Minimal Wear)",
            "Desert Eagle | Sunset Storm (Well-Worn)", "Desert Eagle | Sunset Storm (Battle-Scarred)",
            "Desert Eagle | Sunset Storm (Factory New)", "Desert Eagle | Hypnotic (Field-Tested)"
        ]
        
        extended_skins.extend(additional_skins)
        return extended_skins
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Skinlytics/2.0 (Portfolio Project)',
                'Accept': 'application/json'
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _respect_steam_rate_limit(self):
        """Respeita rate limit do Steam Market de forma inteligente"""
        current_time = time.time()
        
        # Reset contador a cada minuto
        if current_time - self.last_steam_reset >= 60:
            self.steam_requests = 0
            self.last_steam_reset = current_time
        
        # Aguarda se necessário
        if self.steam_requests >= 75:  # 75 requests/min (otimizado)
            wait_time = 60 - (current_time - self.last_steam_reset)
            if wait_time > 0:
                logger.info(f"Rate limit Steam atingido. Aguardando {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
                self.steam_requests = 0
                self.last_steam_reset = current_time
        
        self.steam_requests += 1
        
        # Delay variável para evitar detecção
        base_delay = self.steam_delay
        random_variation = random.uniform(0.1, 0.3)
        actual_delay = base_delay + random_variation
        
        await asyncio.sleep(actual_delay)
    
    async def get_steam_market_prices(self, market_hash_names: List[str]) -> Dict:
        """Coleta preços do Steam Market com estratégia otimizada"""
        results = {}
        
        logger.info(f"🎮 Coletando preços de {len(market_hash_names)} skins do Steam Market...")
        
        # Dividir em lotes para melhor controle
        batch_size = 25
        batches = [market_hash_names[i:i + batch_size] for i in range(0, len(market_hash_names), batch_size)]
        
        for batch_num, batch in enumerate(batches):
            logger.info(f"📦 Processando lote {batch_num + 1}/{len(batches)} ({len(batch)} skins)")
            
            batch_results = {}
            for i, market_hash_name in enumerate(batch):
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
                                batch_results[market_hash_name] = {
                                    'source': 'steam_market',
                                    'data': data,
                                    'timestamp': datetime.now().isoformat()
                                }
                                logger.info(f"   ✅ {i+1}/{len(batch)}: {market_hash_name[:30]}... - ${data.get('median_price', 'N/A')}")
                            else:
                                logger.warning(f"   ⚠️ Steam Market error for {market_hash_name}: {data}")
                        elif response.status == 429:
                            logger.warning(f"   ⚠️ Rate limit (429) para {market_hash_name}, aguardando...")
                            await asyncio.sleep(5)  # Aguardar mais tempo
                            continue
                        else:
                            logger.warning(f"   ❌ Steam Market HTTP {response.status} for {market_hash_name}")
                            
                except Exception as e:
                    logger.error(f"   ❌ Erro ao coletar {market_hash_name}: {e}")
                    continue
            
            # Aguardar entre lotes
            if batch_num < len(batches) - 1:
                logger.info(f"⏳ Aguardando 3s entre lotes...")
                await asyncio.sleep(3)
            
            results.update(batch_results)
        
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
                return skins[:200]  # Limitar a 200 para teste
            else:
                logger.warning(f"📋 Arquivo CSV não encontrado: {csv_file}")
                return []
        except Exception as e:
            logger.error(f"❌ Erro ao carregar CSV: {e}")
            return []
    
    def get_optimized_skin_list(self, strategy: str = 'popular_skins', count: int = 100) -> List[str]:
        """Retorna lista de skins baseada na estratégia escolhida"""
        if strategy == 'popular_skins':
            return self.popular_skins[:count]
        elif strategy == 'weapon_categories':
            # Filtrar por categoria de arma
            weapon_skins = [skin for skin in self.popular_skins if any(weapon in skin for weapon in ['AK-47', 'M4A4', 'AWP', 'M4A1-S'])]
            return weapon_skins[:count]
        elif strategy == 'price_ranges':
            # Skins que provavelmente têm preços variados
            return self.popular_skins[:count]
        elif strategy == 'rarity_levels':
            # Skins com diferentes níveis de raridade
            return self.popular_skins[:count]
        else:
            return self.popular_skins[:count]
    
    async def collect_all_data(self, strategy: str = 'popular_skins', max_skins: int = 100) -> Dict:
        """Coleta dados usando estratégia otimizada"""
        logger.info(f"🎯 Iniciando coleta otimizada com estratégia: {strategy}")
        
        # 1. Obter lista de skins baseada na estratégia
        test_skins = self.get_optimized_skin_list(strategy, max_skins)
        logger.info(f"🎮 Coletando dados para {len(test_skins)} skins (estratégia: {strategy})")
        
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
                'strategy_used': strategy,
                'sources': ['steam_market'],
                'success_rate': f"{(len(steam_data) / len(test_skins) * 100):.1f}%"
            },
            'skins': {},
            'steam_market': steam_data,
            'analysis': {
                'price_distribution': self._analyze_price_distribution(steam_data),
                'weapon_categories': self._analyze_weapon_categories(steam_data),
                'wear_distribution': self._analyze_wear_distribution(steam_data)
            }
        }
        
        # 4. Consolidar por skin
        for skin in test_skins:
            consolidated_data['skins'][skin] = {
                'steam_market': steam_data.get(skin),
                'best_price': None,
                'price_info': {},
                'category': self._categorize_skin(skin),
                'estimated_rarity': self._estimate_rarity(skin)
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
    
    def _analyze_price_distribution(self, steam_data: Dict) -> Dict:
        """Analisa distribuição de preços"""
        prices = []
        for skin_data in steam_data.values():
            if skin_data['data'].get('median_price'):
                try:
                    price = float(skin_data['data']['median_price'].replace('$', '').replace(',', ''))
                    prices.append(price)
                except:
                    continue
        
        if not prices:
            return {}
        
        return {
            'total_items': len(prices),
            'average_price': sum(prices) / len(prices),
            'min_price': min(prices),
            'max_price': max(prices),
            'price_ranges': {
                'low': len([p for p in prices if p < 10]),
                'medium': len([p for p in prices if 10 <= p < 100]),
                'high': len([p for p in prices if 100 <= p < 1000]),
                'premium': len([p for p in prices if p >= 1000])
            }
        }
    
    def _analyze_weapon_categories(self, steam_data: Dict) -> Dict:
        """Analisa distribuição por categoria de arma"""
        categories = {}
        for skin_name in steam_data.keys():
            category = self._categorize_skin(skin_name)
            categories[category] = categories.get(category, 0) + 1
        
        return categories
    
    def _analyze_wear_distribution(self, steam_data: Dict) -> Dict:
        """Analisa distribuição por wear"""
        wears = {}
        for skin_name in steam_data.keys():
            if 'Factory New' in skin_name:
                wears['Factory New'] = wears.get('Factory New', 0) + 1
            elif 'Minimal Wear' in skin_name:
                wears['Minimal Wear'] = wears.get('Minimal Wear', 0) + 1
            elif 'Field-Tested' in skin_name:
                wears['Field-Tested'] = wears.get('Field-Tested', 0) + 1
            elif 'Well-Worn' in skin_name:
                wears['Well-Worn'] = wears.get('Well-Worn', 0) + 1
            elif 'Battle-Scarred' in skin_name:
                wears['Battle-Scarred'] = wears.get('Battle-Scarred', 0) + 1
        
        return wears
    
    def _categorize_skin(self, skin_name: str) -> str:
        """Categoriza skin por tipo de arma"""
        if 'AK-47' in skin_name:
            return 'Rifle'
        elif 'M4A4' in skin_name or 'M4A1-S' in skin_name:
            return 'Rifle'
        elif 'AWP' in skin_name:
            return 'Sniper'
        elif 'USP-S' in skin_name or 'Glock-18' in skin_name or 'Desert Eagle' in skin_name:
            return 'Pistol'
        elif 'Karambit' in skin_name or 'M9 Bayonet' in skin_name or 'Butterfly Knife' in skin_name:
            return 'Knife'
        elif 'Hand Wraps' in skin_name or 'Gloves' in skin_name:
            return 'Gloves'
        else:
            return 'Other'
    
    def _estimate_rarity(self, skin_name: str) -> str:
        """Estima raridade da skin"""
        if 'Dragon Lore' in skin_name or 'Howl' in skin_name:
            return 'Legendary'
        elif 'Fade' in skin_name or 'Marble Fade' in skin_name:
            return 'Epic'
        elif 'Factory New' in skin_name:
            return 'Rare'
        elif 'Minimal Wear' in skin_name:
            return 'Uncommon'
        else:
            return 'Common'
    
    def save_data(self, data: Dict, filename: str = None) -> str:
        """Salva dados coletados"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            strategy = data.get('metadata', {}).get('strategy_used', 'unknown')
            filename = f"steam_optimized_{strategy}_{timestamp}.json"
        
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
    logger.info("🚀 Iniciando Steam Optimized Collector")
    
    async with SteamOptimizedCollector() as collector:
        # Testar diferentes estratégias
        strategies = ['popular_skins', 'weapon_categories', 'price_ranges']
        
        for strategy in strategies:
            logger.info(f"\n🎯 Testando estratégia: {strategy}")
            
            # Coletar dados
            data = await collector.collect_all_data(strategy=strategy, max_skins=50)
            
            if data and data['skins']:
                # Salvar dados
                filename = collector.save_data(data)
                
                # Mostrar resumo
                logger.info(f"📊 RESUMO DA COLETA ({strategy}):")
                logger.info(f"   Total de skins: {data['metadata']['total_skins']}")
                logger.info(f"   Steam Market: {data['metadata']['steam_count']}")
                logger.info(f"   Taxa de sucesso: {data['metadata']['success_rate']}")
                logger.info(f"   Arquivo salvo: {filename}")
                
                # Mostrar análise
                if 'analysis' in data:
                    analysis = data['analysis']
                    logger.info(f"📈 ANÁLISE:")
                    logger.info(f"   Distribuição de preços: {analysis.get('price_distribution', {}).get('total_items', 0)} itens")
                    logger.info(f"   Categorias de armas: {analysis.get('weapon_categories', {})}")
                    logger.info(f"   Distribuição de wear: {analysis.get('wear_distribution', {})}")
                
                # Mostrar algumas skins com preços
                logger.info(f"\n💰 EXEMPLOS DE PREÇOS ({strategy}):")
                count = 0
                for skin_name, skin_data in data['skins'].items():
                    if count >= 3:  # Mostrar apenas 3 exemplos por estratégia
                        break
                    if skin_data['best_price']:
                        logger.info(f"   {skin_name}: ${skin_data['best_price']['price']:.2f} ({skin_data['best_price']['source']})")
                        count += 1
                
                # Aguardar entre estratégias
                if strategy != strategies[-1]:
                    logger.info(f"⏳ Aguardando 5s antes da próxima estratégia...")
                    await asyncio.sleep(5)
            else:
                logger.error(f"❌ Falha na coleta com estratégia {strategy}")

if __name__ == "__main__":
    asyncio.run(main())
